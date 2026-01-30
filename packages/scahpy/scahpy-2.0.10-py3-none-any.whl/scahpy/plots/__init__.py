"""
SCAHpy Plots
============

Visualization utilities for model diagnostics and analyses.

Submodules:
- maps: Horizontal map visualizations.
- sections: Vertical cross-sections.
- timeseries: Temporal evolution at points or regions.
"""

from .maps import map_1var, map_1var_winds, map_2var_contours, map_2vars_winds
from .sections import (
    section_xz_1var, section_yz_1var, section_xz_1var_winds, section_yz_1var_winds,
)
from .timeseries import ts_area_1var, ts_point_1var, ts_area_multi

__all__ = [
    "map_1var", "map_1var_winds", "map_2var_contours", "map_2vars_winds",
    "section_xz_1var", "section_yz_1var", "section_xz_1var_winds", "section_yz_1var_winds",
    "ts_area_1var", "ts_point_1var", "ts_area_multi",
]
