"""
SCAHpy Atmos Component
======================

Atmospheric component for WRF model data.

Includes:
- wrf_io: Input/output utilities for reading WRF files.
- wrf_coords: Vertical coordinate extraction and interpolation.
- wrf_diags: Derived atmospheric diagnostics (e.g., wind speed, geopotential, RH).
"""

from .wrf_io import read_wrf
from .wrf_coords import vert_levs
from .wrf_diags import (
    precipitation, wind_speed, pressure, geopotential, geop_height, t_pot, t_air, rh
)

__all__ = [
    "read_wrf",
    "vert_levs",
    "precipitation", "wind_speed", "pressure", "geopotential", "geop_height",
    "t_pot", "t_air", "rh",
]
