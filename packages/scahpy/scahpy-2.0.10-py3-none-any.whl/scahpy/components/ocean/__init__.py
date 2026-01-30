"""
SCAHpy Ocean Component
======================

Oceanic component for CROCO model data.

Includes:
- croco_io: Input/output utilities for CROCO NetCDF files.
- croco_coords: Vertical coordinates and sigma-to-z interpolation.
- croco_diags: Derived ocean diagnostics (e.g., KE, vorticity, SST gradients).
"""

from .croco_io import read_croco
from .croco_coords import croco_depths, crocointerp_sigma_to_z
from .croco_diags import ke_sfc, grad_sst, vorticity_sfc

__all__ = [
    "read_croco",
    "croco_depths", "crocointerp_sigma_to_z",
    "ke_sfc", "grad_sst", "vorticity_sfc",
]
