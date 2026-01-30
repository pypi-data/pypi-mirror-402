# SCAHpy: System for Coupled Atmosphere–Hydrosphere Analysis in Python
# Copyright (C) 2025  Fiorela Castillón Lucas
# Instituto Geofísico del Perú (IGP)
#
# This file is part of SCAHpy and is distributed under the terms of
# the GNU General Public License v3.0 or later.
# See the LICENSE file for details.

__version__ = "2.0.10"

"""
SCAHpy is a scientific Python package for the analysis and visualization
of coupled climate model components, currently focusing on the atmosphere (WRF)
and ocean (CROCO) outputs of the RESM–COW regional model developed at the
Geophysical Institute of Peru (IGP).

The package provides modular functions for diagnostics, coordinate management,
and geospatial visualization using xarray, cartopy, and matplotlib, following
CF-conventions and reproducible analysis principles.

High-level API for reading, transforming and visualizing coupled OA data.
"""

# === Core === #
from .core import (
    get_metadata_vars, drop_vars,
    destagger_array, extract_points,
    aggregate_dmy, monthly_climatology, anomalies, monthly_to_daily_climatology,
    vertical_interp,
    to_celsius, to_kelvin, to_hpa, to_pa,
    ddx, ddy, rotate_to_EN, apply_mask,
)

# === Atmos / WRF === #
from .components.atmos.wrf_io import read_wrf
from .components.atmos.wrf_coords import vert_levs
from .components.atmos.wrf_diags import (
    precipitation, wind_speed, pressure, geopotential, geop_height, t_pot, t_air, rh
)

# === Ocean / CROCO === #
from .components.ocean.croco_io import read_croco
from .components.ocean.croco_coords import croco_depths, crocointerp_sigma_to_z
from .components.ocean.croco_diags import ke_sfc, grad_sst, vorticity_sfc

# === Plots === #
from .plots.maps import map_1var, map_1var_winds, map_2var_contours, map_2vars_winds
from .plots.sections import section_xz_1var, section_yz_1var, section_xz_1var_winds, section_yz_1var_winds
from .plots.timeseries import ts_area_1var, ts_point_1var, ts_area_multi

__all__ = [
    # Core
    "get_metadata_vars", "drop_vars",
    "destagger_array", "extract_points",
    "aggregate_dmy", "monthly_climatology", "anomalies", "monthly_to_daily_climatology",
    "vertical_interp",
    "to_celsius", "to_kelvin", "to_hpa", "to_pa",
    "ddx", "ddy", "rotate_to_EN", "apply_mask",
    # I/O components
    "read_wrf", "read_croco",
    # Coords/vertical components
    "vert_levs", "croco_depths", "crocointerp_sigma_to_z",
    # Diags
    "precipitation", "wind_speed", "pressure", "geopotential", "geop_height", "t_pot", "t_air", "rh",
    "ke_sfc", "grad_sst", "vorticity_sfc",
    # Plots
    "map_1var", "map_1var_winds", "map_2var_contours", "map_2vars_winds",
    "section_xz_1var", "section_yz_1var", "section_xz_1var_winds", "section_yz_1var_winds",
    "ts_area_1var", "ts_point_1var", "ts_area_multi",
]

