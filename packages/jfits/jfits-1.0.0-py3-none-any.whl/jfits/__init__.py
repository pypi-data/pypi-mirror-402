"""
jfits: Interactive FITS viewer for astronomy

A Python package for interactive visualization and analysis of FITS images,
with support for WCS coordinates, Gaussian centroiding, and 3D cube viewing.

The name 'jfits' is simply a friendly, memorable name for this FITS toolkit.
"""

from .jfits import (
    get_fits_array,
    read_wcs,
    Display,
    InteractiveDisplay,
    InteractiveDisplayCube,
    quick_view,
    quick_view_cube,
    safer_log,
    make_format_coord_func,
    make_wcs_format_coord_func,
    _fit_gaussian_2d,
    _create_gaussian_model,
)

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "get_fits_array",
    "read_wcs",
    "Display",
    "InteractiveDisplay",
    "InteractiveDisplayCube",
    "quick_view",
    "quick_view_cube",
    "safer_log",
    "make_format_coord_func",
    "make_wcs_format_coord_func",
]
