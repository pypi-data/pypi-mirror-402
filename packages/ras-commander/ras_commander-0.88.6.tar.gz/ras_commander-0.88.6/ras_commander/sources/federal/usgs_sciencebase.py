"""
USGS ScienceBase HEC-RAS model source.

Provides access to HEC-RAS models published as USGS Data Releases
through the ScienceBase Catalog system.

API Documentation: https://www.sciencebase.gov/catalog/
Python Library: https://github.com/usgs/sciencebasepy
"""

import logging
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from ras_commander.Decorators import log_call
from ras_commander.sources.base import (
    DownloadResult,
    ModelMetadata,
    ModelSource,
    ModelType,
    SourceStatus,
)

logger = logging.getLogger(__name__)

# Optional dependency
try:
    import sciencebasepy

    SCIENCEBASEPY_AVAILABLE = True
except ImportError:
    SCIENCEBASEPY_AVAILABLE = False
    logger.warning("sciencebasepy not available - install with: pip install sciencebasepy")


class UsgsScienceBase:
    """
    USGS ScienceBase HEC-RAS model source.

    Searches for HEC-RAS models in USGS Data Releases using the
    ScienceBase Catalog API. Models are typically published with
    DOIs and comprehensive metadata.

    Example:
        >>> source = UsgsScienceBase()
        >>> models = source.list_models(location="Colorado", limit=10)
        >>> result = source.download_model(
        ...     model_id=models[0].source_id,
        ...     output_folder="usgs_models"
        ... )
    """

    def __init__(self):
        """Initialize USGS ScienceBase source."""
        self._sb = None
        if SCIENCEBASEPY_AVAILABLE:
            self._sb = sciencebasepy.SbSession()

    @property
    def source_name(self) -> str:
        """Human-readable source name."""
        return "USGS ScienceBase"

    @property
    def source_type(self) -> str:
        """Source category."""
        return "federal"

    @log_call
    def get_source_status(self) -> SourceStatus:
        """
        Check if USGS ScienceBase is accessible.

        Returns:
            SourceStatus.AVAILABLE if accessible, UNAVAILABLE otherwise
        """
        if not SCIENCEBASEPY_AVAILABLE:
            return SourceStatus.UNAVAILABLE

        try:
            # Test connection with a simple query
            self._sb.find_items({"q": "HEC-RAS", "max": 1})
            return SourceStatus.AVAILABLE
        except Exception as e:
            logger.warning(f"ScienceBase connection failed: {e}")
            return SourceStatus.UNAVAILABLE

    @log_call
    def list_models(
        self,
        location: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        hecras_version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[ModelMetadata]:
        """
        Search for HEC-RAS models in ScienceBase.

        Args:
            location: Filter by location (in title/description)
            model_type: Filter by model type (not well-indexed in ScienceBase)
            hecras_version: Filter by HEC-RAS version (in metadata)
            tags: Filter by tags (in keywords)
            limit: Maximum number of results (default: 100)
            **kwargs: Additional ScienceBase query parameters

        Returns:
            List of matching model metadata
        """
        if not SCIENCEBASEPY_AVAILABLE:
            logger.error("sciencebasepy not available")
            return []

        # Build query string
        query_parts = ['HEC-RAS']

        if location:
            query_parts.append(location)

        if hecras_version:
            query_parts.append(f"HEC-RAS {hecras_version}")

        query = " ".join(query_parts)

        # Build filter parameters
        params = {
            "q": query,
            "max": limit or 100,
            "offset": 0,
            "filter": "browseCategory=Data",  # Data releases only
        }

        # Add custom parameters
        params.update(kwargs)

        try:
            logger.info(f"Searching ScienceBase for: {query}")
            results = self._sb.find_items(params)

            models = []
            for item in results.get("items", []):
                metadata = self._parse_item(item)

                # Apply post-query filters
                if tags and not all(tag in metadata.tags for tag in tags):
                    continue

                if model_type and metadata.model_type != model_type:
                    continue

                models.append(metadata)

            logger.info(f"Found {len(models)} models in ScienceBase")
            return models

        except Exception as e:
            logger.error(f"Error querying ScienceBase: {e}")
            return []

    @log_call
    def download_model(
        self,
        model_id: str,
        output_folder: Union[str, Path],
        extract: bool = True,
        overwrite: bool = False,
        credentials: Optional[dict] = None
    ) -> DownloadResult:
        """
        Download a HEC-RAS model from ScienceBase.

        Args:
            model_id: ScienceBase item ID
            output_folder: Where to save the model
            extract: Whether to extract ZIP archives
            overwrite: Whether to overwrite existing files
            credentials: Not required for public ScienceBase items

        Returns:
            DownloadResult with download status
        """
        if not SCIENCEBASEPY_AVAILABLE:
            return DownloadResult(
                success=False,
                model_path=None,
                message="sciencebasepy not available",
                metadata=None,
            )

        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        try:
            # Get item metadata
            logger.info(f"Fetching item {model_id} from ScienceBase")
            item = self._sb.get_item(model_id)

            if not item:
                return DownloadResult(
                    success=False,
                    model_path=None,
                    message=f"Item {model_id} not found",
                    metadata=None,
                )

            metadata = self._parse_item(item)

            # Download files
            files = item.get("files", [])
            if not files:
                return DownloadResult(
                    success=False,
                    model_path=None,
                    message="No files attached to this item",
                    metadata=metadata,
                )

            # Create model-specific folder
            safe_name = re.sub(r'[^\w\s-]', '', metadata.name).strip().replace(' ', '_')
            model_folder = output_folder / safe_name

            if model_folder.exists() and not overwrite:
                logger.warning(f"Model folder already exists: {model_folder}")
                return DownloadResult(
                    success=True,
                    model_path=model_folder,
                    message="Model already downloaded (use overwrite=True to re-download)",
                    metadata=metadata,
                    extracted=extract,
                )

            model_folder.mkdir(parents=True, exist_ok=True)

            # Download each file
            downloaded_files = []
            for file_info in files:
                file_name = file_info.get("name")
                file_url = file_info.get("url")

                if not file_url:
                    continue

                logger.info(f"Downloading: {file_name}")
                file_path = model_folder / file_name

                try:
                    self._sb.download_file(file_url, str(file_path))
                    downloaded_files.append(file_path)

                    # Extract if ZIP and extract=True
                    if extract and file_name.lower().endswith('.zip'):
                        logger.info(f"Extracting: {file_name}")
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(model_folder)

                except Exception as e:
                    logger.error(f"Error downloading {file_name}: {e}")
                    continue

            if not downloaded_files:
                return DownloadResult(
                    success=False,
                    model_path=None,
                    message="Failed to download any files",
                    metadata=metadata,
                )

            logger.info(f"Downloaded {len(downloaded_files)} files to {model_folder}")

            return DownloadResult(
                success=True,
                model_path=model_folder,
                message=f"Successfully downloaded {len(downloaded_files)} files",
                metadata=metadata,
                extracted=extract,
            )

        except Exception as e:
            logger.error(f"Error downloading model {model_id}: {e}")
            return DownloadResult(
                success=False,
                model_path=None,
                message=f"Download failed: {e}",
                metadata=None,
            )

    def _parse_item(self, item: dict) -> ModelMetadata:
        """
        Parse ScienceBase item into ModelMetadata.

        Args:
            item: ScienceBase item dictionary

        Returns:
            ModelMetadata object
        """
        # Extract basic info
        source_id = item.get("id", "")
        title = item.get("title", "Untitled")
        body = item.get("body", "")

        # Extract location from tags or title
        location = "Unknown"
        tags = []
        for tag in item.get("tags", []):
            tag_name = tag.get("name", "")
            tags.append(tag_name)
            # Try to extract location
            if any(term in tag_name.lower() for term in ["county", "river", "creek", "basin"]):
                location = tag_name

        # Extract DOI
        doi = None
        for link in item.get("webLinks", []):
            if "doi.org" in link.get("uri", ""):
                doi = link["uri"]
                break

        # Determine model type from keywords
        model_type = self._infer_model_type(title, body, tags)

        # Extract HEC-RAS version if mentioned
        hecras_version = None
        version_match = re.search(r'HEC-RAS\s+(\d+\.?\d*)', title + " " + body)
        if version_match:
            hecras_version = version_match.group(1)

        # Extract file size
        total_size = 0
        for file_info in item.get("files", []):
            total_size += file_info.get("size", 0)
        file_size_mb = total_size / (1024 * 1024) if total_size > 0 else None

        # Extract dates
        last_modified = None
        date_str = item.get("provenance", {}).get("lastUpdated")
        if date_str:
            try:
                last_modified = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except Exception:
                pass

        # Build URL
        url = f"https://www.sciencebase.gov/catalog/item/{source_id}"

        return ModelMetadata(
            source_id=source_id,
            name=title,
            description=body,
            location=location,
            model_type=model_type,
            hecras_version=hecras_version,
            doi=doi,
            url=url,
            file_size_mb=file_size_mb,
            last_modified=last_modified,
            tags=tags,
        )

    def _infer_model_type(self, title: str, body: str, tags: List[str]) -> ModelType:
        """
        Infer model type from text content.

        Args:
            title: Item title
            body: Item description
            tags: Item tags

        Returns:
            ModelType enum
        """
        text = (title + " " + body + " " + " ".join(tags)).lower()

        if "2d" in text or "two-dimensional" in text:
            return ModelType.UNSTEADY_2D
        elif "dam breach" in text or "dam break" in text:
            return ModelType.DAM_BREACH
        elif "steady" in text:
            return ModelType.STEADY_1D
        elif "unsteady" in text:
            return ModelType.UNSTEADY_1D
        elif "sediment" in text:
            return ModelType.SEDIMENT
        elif "water quality" in text:
            return ModelType.WATER_QUALITY
        else:
            return ModelType.UNKNOWN
