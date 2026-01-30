"""
SCAHpy Components
=================

Coupled model interfaces for oceanic and atmospheric submodules.

- atmos: WRF model utilities and diagnostics.
- ocean: CROCO model utilities and diagnostics.
"""

from . import atmos
from . import ocean

__all__ = ["atmos", "ocean"]
