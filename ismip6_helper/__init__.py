"""
ISMIP6 Helper Package

A utility package for working with ISMIP6 (Ice Sheet Model Intercomparison Project for CMIP6) data.

This package provides:
- Grid utilities for correcting ISMIP6 grid coordinates
- File indexing and caching for ISMIP6 datasets on Google Cloud Storage

Main modules:
- grid_utils: Functions for handling ISMIP6 grid coordinates and projections
- index: Functions for indexing and caching ISMIP6 file metadata
"""

from .grid_utils import (
    correct_grid_coordinates,
    detect_grid_resolution,
    create_coordinates,
    verify_latlon_consistency,
    GRID_BOUNDS,
    STANDARD_RESOLUTIONS,
)

from .index import (
    get_file_index,
    parse_ismip6_path,
    build_file_index,
)

__version__ = "0.1.0"

__all__ = [
    # Grid utils
    "correct_grid_coordinates",
    "detect_grid_resolution",
    "create_coordinates",
    "verify_latlon_consistency",
    "GRID_BOUNDS",
    "STANDARD_RESOLUTIONS",
    # Index utils
    "get_file_index",
    "parse_ismip6_path",
    "build_file_index",
]
