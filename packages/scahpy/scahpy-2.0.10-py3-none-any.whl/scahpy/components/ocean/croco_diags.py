import numpy as np
import xarray as xr

from ...core.utils import ddx, ddy, apply_mask

def _attach_attrs(da: xr.DataArray, name: str, units: str, long_name: str) -> xr.DataArray:
    da.name = name
    da.attrs.update({
        "units": units,
        "long_name": long_name,
        "standard_name": name,
    })
    return da


def ke_sfc(
    u: xr.DataArray,
    v: xr.DataArray,
    *,
    mask: xr.DataArray | None = None,
    name: str = "ke_sfc",
) -> xr.DataArray:
    """Surface kinetic energy ``KE = 0.5 * (u**2 + v**2)``.

    Assumes that ``u`` and ``v`` are already on the same unstaggered grid and in
    earth-relative coordinates if needed (East–North). For purely scalar KE this
    rotation is not strictly necessary (KE is rotation-invariant), but ensure
    consistent pre-processing if you plan to overlay quivers.

    Parameters
    ----------
    u, v : xr.DataArray
        Horizontal velocity components at the surface (m s⁻¹).
    mask : xr.DataArray, optional
        Ocean mask (1=sea, 0=land) to apply to the result.
    name : str, default "ke_sfc"
        Output variable name.

    Returns
    -------
    xr.DataArray
        Surface kinetic energy (m² s⁻²) with the same dimensions as ``u``/``v``.
    """
    ke = 0.5 * (u ** 2 + v ** 2)
    ke = apply_mask(ke, mask)
    return _attach_attrs(ke, name=name, units="m2 s-2", long_name="surface kinetic energy")


def grad_sst(
    sst: xr.DataArray,
    pm: xr.DataArray,
    pn: xr.DataArray,
    *,
    x_dim: str = "lon",
    y_dim: str = "lat",
    mask: xr.DataArray | None = None,
    to_per_100km: bool = True,
    name: str = "grad_sst_mag",
) -> xr.DataArray:
    """Magnitude of the horizontal SST gradient ``|∇T|``.

    Uses centered differences and CROCO/ROMS metric coefficients ``pm=1/Δx`` and
    ``pn=1/Δy``. Units are °C per 100 km by default (set ``to_per_100km=False``
    to keep °C m⁻¹).

    Parameters
    ----------
    sst : xr.DataArray
        Sea surface temperature (°C or K) on the ρ-grid.
    pm, pn : xr.DataArray
        Metric coefficients 1/Δx and 1/Δy (m⁻¹), broadcastable to ``sst``.
    x_dim, y_dim : str, default ("lon", "lat")
        Names of horizontal dimensions.
    mask : xr.DataArray, optional
        Ocean mask (1=sea, 0=land) to apply to the result.
    to_per_100km : bool, default True
        If True, scales the magnitude to per 100 km.
    name : str, default "grad_sst_mag"
        Output variable name.

    Returns
    -------
    xr.DataArray
        ``|∇T|`` in °C per 100 km (default) or °C m⁻¹.
    """
    dTdx = ddx(sst, pm, x_dim=x_dim)
    dTdy = ddy(sst, pn, y_dim=y_dim)
    mag = xr.apply_ufunc(np.hypot, dTdx, dTdy)
    mag = apply_mask(mag, mask)

    sst_units = str(sst.attrs.get("units", "")).lower()
    is_celsius = sst_units in {"c", "degc", "°c", "celsius"}

    if to_per_100km:
        mag = mag * 1e5  # 100 km = 1e5 m
        units = "degC per 100 km" if is_celsius else "K per 100 km"
    else:
        units = "degC m-1" if is_celsius else "K m-1"

    return _attach_attrs(mag, name=name, units=units, long_name="SST horizontal gradient magnitude")


def vorticity_sfc(
    u: xr.DataArray,
    v: xr.DataArray,
    pm: xr.DataArray,
    pn: xr.DataArray,
    *,
    x_dim: str = "lon",
    y_dim: str = "lat",
    mask: xr.DataArray | None = None,
    f: xr.DataArray | None = None,
    normalize_by_f: bool = False,
    name: str | None = None,
) -> xr.DataArray:
    """Surface relative vorticity ``ζ = ∂v/∂x − ∂u/∂y``.

    Derivatives are computed with centered differences and multiplied by the
    metric coefficients (``pm``, ``pn``). If ``normalize_by_f=True`` the result
    is divided by the local Coriolis parameter ``f`` to obtain the adimensional
    quantity ``ζ/f``.

    Parameters
    ----------
    u, v : xr.DataArray
        Horizontal velocity components at the surface (m s⁻¹).
    pm, pn : xr.DataArray
        Metric coefficients 1/Δx and 1/Δy (m⁻¹), broadcastable to ``u``/``v``.
    x_dim, y_dim : str, default ("lon", "lat")
        Names of horizontal dimensions.
    mask : xr.DataArray, optional
        Ocean mask (1=sea, 0=land) to apply to the result.
    f : xr.DataArray, optional
        Coriolis parameter (s⁻¹). Required if ``normalize_by_f=True``.
    normalize_by_f : bool, default False
        If True, returns ``ζ/f`` (dimensionless).
    name : str, optional
        Output variable name. Inferred from ``normalize_by_f`` if not provided.

    Returns
    -------
    xr.DataArray
        Relative vorticity (s⁻¹) or normalized vorticity ``ζ/f`` (dimensionless).
    """
    dvdx = ddx(v, pm, x_dim=x_dim)
    dudy = ddy(u, pn, y_dim=y_dim)
    zeta = dvdx - dudy
    zeta = apply_mask(zeta, mask)

    if normalize_by_f:
        if f is None:
            raise ValueError("normalize_by_f=True requires 'f' (Coriolis) provided.")
        out = zeta / f
        out_name = name or "zeta_over_f_sfc"
        units = "1"
        long_name = "surface relative vorticity normalized by f"
    else:
        out = zeta
        out_name = name or "zeta_sfc"
        units = "s-1"
        long_name = "surface relative vorticity"

    return _attach_attrs(out, name=out_name, units=units, long_name=long_name)
