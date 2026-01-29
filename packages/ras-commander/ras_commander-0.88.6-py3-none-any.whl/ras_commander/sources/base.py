"""
Base classes and protocols for HEC-RAS model source integration.

This module defines the core abstractions for discovering and downloading
HEC-RAS models from various sources (federal, state, county, academic).
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Protocol, Tuple, Union

from ras_commander.RasValidation import ValidationReport


class ModelType(Enum):
    """HEC-RAS model types."""

    STEADY_1D = "1d_steady"
    UNSTEADY_1D = "1d_unsteady"
    UNSTEADY_2D = "2d_unsteady"
    MIXED_1D_2D = "mixed_1d_2d"
    DAM_BREACH = "dam_breach"
    SEDIMENT = "sediment"
    WATER_QUALITY = "water_quality"
    UNKNOWN = "unknown"


class SourceStatus(Enum):
    """Source availability status."""

    AVAILABLE = "available"           # Ready to use
    REQUIRES_AUTH = "requires_auth"   # Needs credentials
    UNAVAILABLE = "unavailable"       # Temporarily down
    DEPRECATED = "deprecated"         # No longer maintained


@dataclass(frozen=True)
class ModelMetadata:
    """
    Metadata for a HEC-RAS model from any source.

    Attributes:
        source_id: Unique identifier within source (e.g., DOI, database ID)
        name: Human-readable model name
        description: Model description and purpose
        location: Geographic location (city, county, watershed)
        model_type: Type of HEC-RAS model
        hecras_version: HEC-RAS version (e.g., "6.5", "5.0.7")
        doi: Digital Object Identifier (if available)
        url: Direct download or info URL
        file_size_mb: Estimated download size in megabytes
        last_modified: When model was last updated
        projection: Coordinate reference system (e.g., "EPSG:2248")
        tags: Keywords for categorization (e.g., ['steady', '2D', 'regulatory'])
        spatial_extent: Bounding box (minx, miny, maxx, maxy) in WGS84
        study_date: When the model study was performed (YYYY-MM-DD)
        effective_date: Regulatory effective date (YYYY-MM-DD)
    """

    source_id: str
    name: str
    description: str
    location: str
    model_type: ModelType
    hecras_version: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    file_size_mb: Optional[float] = None
    last_modified: Optional[datetime] = None
    projection: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    spatial_extent: Optional[Tuple[float, float, float, float]] = None
    study_date: Optional[str] = None
    effective_date: Optional[str] = None


@dataclass
class DownloadResult:
    """
    Result of a model download operation.

    Attributes:
        success: Whether download succeeded
        model_path: Path to downloaded model folder
        message: Human-readable result message
        metadata: Model metadata
        extracted: Whether archive was extracted
        validation_report: Optional validation of downloaded model
    """

    success: bool
    model_path: Optional[Path]
    message: str
    metadata: ModelMetadata
    extracted: bool = False
    validation_report: Optional[ValidationReport] = None


class ModelSource(Protocol):
    """
    Protocol for HEC-RAS model source implementations.

    All model sources (federal, state, county, academic) should implement
    this protocol to provide consistent discovery and download capabilities.
    """

    @property
    def source_name(self) -> str:
        """Human-readable source name (e.g., 'USGS ScienceBase')."""
        ...

    @property
    def source_type(self) -> str:
        """Source category (e.g., 'federal', 'state', 'county', 'academic')."""
        ...

    @abstractmethod
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
        List available models from this source.

        Args:
            location: Filter by location (city, county, state)
            model_type: Filter by model type
            hecras_version: Filter by HEC-RAS version
            tags: Filter by tags (AND logic)
            limit: Maximum number of results
            **kwargs: Source-specific filters

        Returns:
            List of model metadata matching filters
        """
        ...

    @abstractmethod
    def download_model(
        self,
        model_id: str,
        output_folder: Union[str, Path],
        extract: bool = True,
        overwrite: bool = False,
        credentials: Optional[dict] = None
    ) -> DownloadResult:
        """
        Download a model from this source.

        Args:
            model_id: Source-specific model identifier
            output_folder: Where to save the model
            extract: Whether to extract archives
            overwrite: Whether to overwrite existing files
            credentials: Optional authentication (username, password, API key)

        Returns:
            DownloadResult with success status and model path
        """
        ...

    @abstractmethod
    def get_source_status(self) -> SourceStatus:
        """
        Check if source is currently accessible.

        Returns:
            SourceStatus enum indicating availability
        """
        ...

    def verify_model(self, model_path: Path) -> ValidationReport:
        """
        Validate downloaded model integrity (optional).

        Args:
            model_path: Path to downloaded model folder

        Returns:
            ValidationReport with validation results
        """
        # Default implementation: basic existence check
        from ras_commander.RasValidation import (
            ValidationResult,
            ValidationSeverity,
            ValidationReport,
        )

        results = []

        if not model_path.exists():
            results.append(
                ValidationResult(
                    check_name="model_exists",
                    severity=ValidationSeverity.CRITICAL,
                    passed=False,
                    message=f"Model path does not exist: {model_path}"
                )
            )
        else:
            results.append(
                ValidationResult(
                    check_name="model_exists",
                    severity=ValidationSeverity.INFO,
                    passed=True,
                    message=f"Model path exists: {model_path}"
                )
            )

        return ValidationReport(
            target=str(model_path),
            timestamp=datetime.now(),
            results=results
        )


@dataclass
class ModelFilter:
    """
    Advanced filtering for model catalog queries.

    Attributes:
        location: Geographic location filter
        model_type: Model type filter
        hecras_version: HEC-RAS version filter
        tags: Tag filters (AND logic)
        spatial_extent: Bounding box filter (minx, miny, maxx, maxy)
        min_file_size_mb: Minimum file size
        max_file_size_mb: Maximum file size
        after_date: Models modified after this date
        before_date: Models modified before this date
    """

    location: Optional[str] = None
    model_type: Optional[ModelType] = None
    hecras_version: Optional[str] = None
    tags: Optional[List[str]] = None
    spatial_extent: Optional[Tuple[float, float, float, float]] = None
    min_file_size_mb: Optional[float] = None
    max_file_size_mb: Optional[float] = None
    after_date: Optional[datetime] = None
    before_date: Optional[datetime] = None

    def matches(self, metadata: ModelMetadata) -> bool:
        """
        Check if model metadata matches this filter.

        Args:
            metadata: Model metadata to check

        Returns:
            True if metadata matches all non-None filter criteria
        """
        # Location filter (case-insensitive substring match)
        if self.location and self.location.lower() not in metadata.location.lower():
            return False

        # Model type filter
        if self.model_type and metadata.model_type != self.model_type:
            return False

        # HEC-RAS version filter
        if self.hecras_version and metadata.hecras_version != self.hecras_version:
            return False

        # Tags filter (all tags must be present)
        if self.tags:
            if not all(tag in metadata.tags for tag in self.tags):
                return False

        # File size filters
        if metadata.file_size_mb is not None:
            if self.min_file_size_mb and metadata.file_size_mb < self.min_file_size_mb:
                return False
            if self.max_file_size_mb and metadata.file_size_mb > self.max_file_size_mb:
                return False

        # Date filters
        if metadata.last_modified is not None:
            if self.after_date and metadata.last_modified < self.after_date:
                return False
            if self.before_date and metadata.last_modified > self.before_date:
                return False

        # Spatial extent filter (bounding box intersection)
        if self.spatial_extent and metadata.spatial_extent:
            # Check if bounding boxes intersect
            f_minx, f_miny, f_maxx, f_maxy = self.spatial_extent
            m_minx, m_miny, m_maxx, m_maxy = metadata.spatial_extent

            # No intersection if boxes don't overlap
            if f_maxx < m_minx or f_minx > m_maxx:
                return False
            if f_maxy < m_miny or f_miny > m_maxy:
                return False

        return True
