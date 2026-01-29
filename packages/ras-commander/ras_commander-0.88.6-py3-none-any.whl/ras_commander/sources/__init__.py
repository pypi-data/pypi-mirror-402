"""
HEC-RAS Model Sources - Unified discovery and download.

This submodule provides access to HEC-RAS models from various sources:
- Federal: USGS ScienceBase, FEMA BLE, USACE examples
- State: Virginia VFRIS, Wisconsin DNR, West Virginia, etc.
- County: Henrico VA, Harris TX, Fort Bend TX, etc.
- Academic: HydroShare, university repositories

Quick Start:
    >>> from ras_commander.sources import get_catalog
    >>>
    >>> # Get unified catalog
    >>> catalog = get_catalog()
    >>>
    >>> # Search for models
    >>> models = catalog.search_models(location="Colorado", limit=10)
    >>>
    >>> # Download a model
    >>> result = catalog.download_model(models[0], output_folder="my_models")

Available Sources (as implemented):
    - USGS ScienceBase (federal): Peer-reviewed data releases with DOIs
    - More sources being added in phases

See Also:
    - Sources_for_RAS_Models/ - Research on available sources
    - examples/ - Example notebooks (planned: 600-series)
"""

from ras_commander.sources.base import (
    DownloadResult,
    ModelFilter,
    ModelMetadata,
    ModelSource,
    ModelType,
    SourceStatus,
)
from ras_commander.sources.catalog import ModelCatalog, get_catalog

# Re-export from submodules
from .federal import RasEbfeModels, RasEbfeExamples
from .county import M3Model

__all__ = [
    # Core classes
    "ModelCatalog",
    "get_catalog",
    # Base types
    "ModelMetadata",
    "ModelType",
    "ModelSource",
    "DownloadResult",
    "SourceStatus",
    "ModelFilter",
    # Federal sources
    "RasEbfeModels",
    "RasEbfeExamples",
    # County sources
    "M3Model",
]

# Version info
__version__ = "0.1.0"  # Sources submodule version
