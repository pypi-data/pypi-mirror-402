"""
Unified catalog for discovering HEC-RAS models across all sources.

The ModelCatalog provides a single interface for searching and downloading
models from federal, state, county, and academic sources.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from ras_commander.Decorators import log_call
from ras_commander.sources.base import (
    DownloadResult,
    ModelFilter,
    ModelMetadata,
    ModelSource,
    ModelType,
    SourceStatus,
)

logger = logging.getLogger(__name__)


class ModelCatalog:
    """
    Unified catalog for discovering HEC-RAS models across all sources.

    The catalog manages multiple ModelSource implementations and provides
    a unified search interface with lazy loading and error handling.

    Example:
        >>> catalog = ModelCatalog()
        >>> catalog.register_source(UsgsScienceBase())
        >>> catalog.register_source(VirginiaVFRIS())
        >>> models = catalog.search_models(location="Virginia")
        >>> result = catalog.download_model(models[0], output_folder="models")
    """

    def __init__(self):
        """Initialize empty catalog."""
        self._sources: Dict[str, ModelSource] = {}
        self._source_status: Dict[str, SourceStatus] = {}

    @log_call
    def register_source(self, source: ModelSource) -> None:
        """
        Register a model source with the catalog.

        Args:
            source: ModelSource implementation to register
        """
        source_name = source.source_name
        self._sources[source_name] = source

        # Check source status
        try:
            status = source.get_source_status()
            self._source_status[source_name] = status
            logger.info(f"Registered source '{source_name}' with status: {status.value}")
        except Exception as e:
            logger.warning(f"Could not check status for '{source_name}': {e}")
            self._source_status[source_name] = SourceStatus.UNAVAILABLE

    @log_call
    def list_sources(self, include_unavailable: bool = False) -> List[str]:
        """
        List all registered sources.

        Args:
            include_unavailable: Whether to include unavailable sources

        Returns:
            List of source names
        """
        if include_unavailable:
            return list(self._sources.keys())

        return [
            name
            for name, status in self._source_status.items()
            if status not in [SourceStatus.UNAVAILABLE, SourceStatus.DEPRECATED]
        ]

    @log_call
    def get_source_status(self, source_name: str) -> Optional[SourceStatus]:
        """
        Get status of a specific source.

        Args:
            source_name: Name of source to check

        Returns:
            SourceStatus or None if source not found
        """
        return self._source_status.get(source_name)

    @log_call
    def search_models(
        self,
        location: Optional[str] = None,
        model_type: Optional[ModelType] = None,
        hecras_version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        limit_per_source: Optional[int] = None,
        model_filter: Optional[ModelFilter] = None,
    ) -> List[ModelMetadata]:
        """
        Search for models across all registered sources.

        Args:
            location: Filter by location
            model_type: Filter by model type
            hecras_version: Filter by HEC-RAS version
            tags: Filter by tags
            sources: Limit search to specific sources (default: all available)
            limit_per_source: Max results per source
            model_filter: Advanced filtering with ModelFilter

        Returns:
            List of matching model metadata from all sources
        """
        # Determine which sources to query
        if sources:
            source_names = [s for s in sources if s in self._sources]
        else:
            source_names = self.list_sources(include_unavailable=False)

        if not source_names:
            logger.warning("No available sources to search")
            return []

        # Query each source
        all_results = []
        for source_name in source_names:
            source = self._sources[source_name]

            try:
                logger.debug(f"Querying source: {source_name}")
                results = source.list_models(
                    location=location,
                    model_type=model_type,
                    hecras_version=hecras_version,
                    tags=tags,
                    limit=limit_per_source,
                )

                # Apply additional filtering if model_filter provided
                if model_filter:
                    results = [m for m in results if model_filter.matches(m)]

                logger.info(f"Found {len(results)} models from {source_name}")
                all_results.extend(results)

            except Exception as e:
                logger.error(f"Error querying {source_name}: {e}")
                continue

        return all_results

    @log_call
    def download_model(
        self,
        metadata: ModelMetadata,
        output_folder: Union[str, Path],
        extract: bool = True,
        overwrite: bool = False,
        credentials: Optional[dict] = None,
    ) -> DownloadResult:
        """
        Download a model using its metadata.

        Args:
            metadata: Model metadata from search results
            output_folder: Where to save the model
            extract: Whether to extract archives
            overwrite: Whether to overwrite existing files
            credentials: Optional authentication credentials

        Returns:
            DownloadResult with success status and model path
        """
        # Find the source that provided this metadata
        # (metadata doesn't store source name directly, so we need to infer)
        source = self._find_source_for_model(metadata)

        if source is None:
            return DownloadResult(
                success=False,
                model_path=None,
                message=f"Could not find source for model: {metadata.name}",
                metadata=metadata,
            )

        # Download from source
        try:
            result = source.download_model(
                model_id=metadata.source_id,
                output_folder=output_folder,
                extract=extract,
                overwrite=overwrite,
                credentials=credentials,
            )
            return result

        except Exception as e:
            logger.error(f"Error downloading model {metadata.name}: {e}")
            return DownloadResult(
                success=False,
                model_path=None,
                message=f"Download failed: {e}",
                metadata=metadata,
            )

    def _find_source_for_model(self, metadata: ModelMetadata) -> Optional[ModelSource]:
        """
        Find the source that can provide this model.

        Args:
            metadata: Model metadata

        Returns:
            ModelSource that can download this model, or None
        """
        # Strategy: Query each source to see if it has this model
        for source_name, source in self._sources.items():
            try:
                # Check if source has this model_id
                results = source.list_models(limit=1)
                if any(m.source_id == metadata.source_id for m in results):
                    return source
            except Exception:
                continue

        return None

    @log_call
    def get_model_by_id(
        self, source_name: str, model_id: str
    ) -> Optional[ModelMetadata]:
        """
        Get model metadata by source and ID.

        Args:
            source_name: Name of source to query
            model_id: Source-specific model identifier

        Returns:
            ModelMetadata if found, None otherwise
        """
        if source_name not in self._sources:
            logger.error(f"Source not found: {source_name}")
            return None

        source = self._sources[source_name]

        try:
            # Query source for all models and find matching ID
            # (Sources could implement get_model_by_id for efficiency)
            models = source.list_models()
            for model in models:
                if model.source_id == model_id:
                    return model

            logger.warning(f"Model {model_id} not found in {source_name}")
            return None

        except Exception as e:
            logger.error(f"Error querying {source_name}: {e}")
            return None

    @log_call
    def refresh_source_status(self) -> None:
        """Refresh availability status for all registered sources."""
        for source_name, source in self._sources.items():
            try:
                status = source.get_source_status()
                self._source_status[source_name] = status
                logger.info(f"Source '{source_name}' status: {status.value}")
            except Exception as e:
                logger.warning(f"Could not check status for '{source_name}': {e}")
                self._source_status[source_name] = SourceStatus.UNAVAILABLE


# Global catalog instance
_catalog: Optional[ModelCatalog] = None


def get_catalog(auto_register: bool = True) -> ModelCatalog:
    """
    Get the global model catalog instance.

    Args:
        auto_register: Whether to auto-register available sources

    Returns:
        ModelCatalog instance
    """
    global _catalog

    if _catalog is None:
        _catalog = ModelCatalog()

        if auto_register:
            # Register available sources
            # (Import here to avoid circular dependencies)
            try:
                from ras_commander.sources.federal.usgs_sciencebase import (
                    UsgsScienceBase,
                )

                _catalog.register_source(UsgsScienceBase())
            except ImportError:
                logger.debug("UsgsScienceBase not available")

            # Add other sources as implemented
            # try:
            #     from ras_commander.sources.state.virginia_vfris import VirginiaVFRIS
            #     _catalog.register_source(VirginiaVFRIS())
            # except ImportError:
            #     pass

    return _catalog
