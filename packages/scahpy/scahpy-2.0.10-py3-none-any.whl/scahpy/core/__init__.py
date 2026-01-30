"""
SCAHpy Core
===========

Core utilities for I/O, coordinates, spatial/temporal ops, and vertical interpolation.
"""

from .io import get_metadata_vars, drop_vars
from .coords import destagger_array
from .spatial_ops import extract_points
from .time_ops import aggregate_dmy, monthly_climatology, anomalies, monthly_to_daily_climatology
from .vertical import vertical_interp
from .utils import (
    to_celsius, to_kelvin, to_hpa, to_pa,
    ddx, ddy, rotate_to_EN, apply_mask,
    # central_diff  # internal function for now
)

__all__ = [
    "get_metadata_vars", "drop_vars",
    "destagger_array", "extract_points",
    "aggregate_dmy", "monthly_climatology", "anomalies", "monthly_to_daily_climatology",
    "vertical_interp",
    "to_celsius", "to_kelvin", "to_hpa", "to_pa",
    "ddx", "ddy", "rotate_to_EN", "apply_mask",
]
