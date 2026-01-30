from __future__ import annotations
from typing import Iterable, Optional, Sequence
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import cmocean

from ._helpers import (
    set_style, cmo_light, boundary_norm, maybe_save, pick_tframe
)

def _get_zcoord(da: xr.DataArray,
                candidates: Sequence[str] = ('level', 'levels', 'zlevel',
                                              'pressure','lev', 'bottom_top',
                                              'bottom_top_stag','z')) -> str:
    """
    Return the name of the vertical coordinate from a set of common candidates.

    Raises
    ------
    ValueError
        If none of the candidate coordinates are present in the DataArray.
    """
    for c in candidates:
        if c in da.coords or (c in da.dims):
            return c
    raise ValueError(
        "Could not find a vertical coordinate. Tried: " + ", ".join(candidates)
    )

def _norm_from_levels(levels: Iterable[float], cmap: mcolors.Colormap) -> mcolors.BoundaryNorm:
    """Create a BoundaryNorm from discrete levels."""
    return boundary_norm(list(levels), cmap)

def section_xz_1var(
    da: xr.DataArray,
    *,
    lat: float,
    levels: Iterable[float],
    cmap: str = 'thermal',
    time=None,
    month=None,
    yinv: bool = True,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Plot an X–Z vertical section at a fixed latitude (lon vs vertical).

    Parameters
    ----------
    da : xarray.DataArray
        Scalar variable with coordinates (time|month?, z, lat, lon).
    lat : float
        Fixed latitude at which the section is extracted (nearest selection).
    levels : iterable of float
        Discrete color levels for the filled section.
    cmap : str
        cmocean colormap name (lightened internally).
    time : int or str, optional
        Select a single `time` frame if available (index or timestamp string).
    month : int, optional
        Select a single `month` if available (1–12) for climatologies.
    title : str, optional
        Figure title.
    colorbar_label : str, optional
        Label for the colorbar; defaults to `da.units` if present.
    output_path : str or None
        If provided, the figure is saved; otherwise it is shown.
    """
    set_style()
    A = pick_tframe(da, time=time, month=month)
    zname = _get_zcoord(A)

    sec = A.sel(lat=lat, method='nearest')

    X = sec['lon'].values
    Z = sec[zname].values if zname in sec.coords else np.arange(sec.sizes[zname])

    if sec.dims != (zname, 'lon'):
        sec_plot = sec.transpose(zname, 'lon').values
    else:
        sec_plot = sec.values

    cm = cmo_light(cmap, .85)
    norm = _norm_from_levels(levels, cm)

    fig, ax = plt.subplots(figsize=(8, 10))
    pcm = ax.contourf(X, Z, sec_plot, levels=levels, cmap=cm, norm=norm, extend='both')
    cb = fig.colorbar(pcm, ax=ax, orientation='horizontal', shrink=.9,
                       pad=.08, aspect=25, fraction=0.05)
    label = colorbar_label or getattr(A, 'units', '')
    cb.set_label(label, labelpad=7)           
    cb.ax.tick_params(length=4, width=1.0, pad=2)

    if yinv:
        ax.invert_yaxis()

    ax.set_xlabel('Longitude (°)')
    ax.set_ylabel(zname)
    ax.set_title(title or f'X–Z section at lat={float(sec["lat"].values):.2f}')

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)

def section_yz_1var(
    da: xr.DataArray,
    *,
    lon: float,
    levels: Iterable[float],
    cmap: str = 'thermal',
    yinv: bool = True,
    time=None,
    month=None,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Plot a Y–Z vertical section at a fixed longitude (lat vs vertical).

    Parameters
    ----------
    da : xarray.DataArray
        Scalar variable with coordinates (time|month?, z, lat, lon).
    lon : float
        Fixed longitude at which the section is extracted (nearest selection).
    levels : iterable of float
        Discrete color levels for the filled section.
    cmap : str
        cmocean colormap name (lightened internally).
    time, month, title, colorbar_label, output_path
        See `section_xz_1var`.
    """
    set_style()
    A = pick_tframe(da, time=time, month=month)
    zname = _get_zcoord(A)

    sec = A.sel(lon=lon, method='nearest')

    Y = sec['lat'].values
    Z = sec[zname].values if zname in sec.coords else np.arange(sec.sizes[zname])

    if sec.dims != (zname, 'lat'):
        sec_plot = sec.transpose(zname, 'lat').values
    else:
        sec_plot = sec.values

    cm = cmo_light(cmap, .85)
    norm = _norm_from_levels(levels, cm)

    fig, ax = plt.subplots(figsize=(8, 10))
    pcm = ax.contourf(Y, Z, sec_plot, levels=levels, cmap=cm, norm=norm, extend='both')
    cb = fig.colorbar(pcm, ax=ax, orientation='horizontal', shrink=.9,
                       pad=.08, aspect=25, fraction=0.05)
    label = colorbar_label or getattr(A, 'units', '')
    cb.set_label(label, labelpad=7)           
    cb.ax.tick_params(length=4, width=1.0, pad=2)

    if yinv:
        ax.invert_yaxis()

    ax.set_xlabel('Latitude (°)')
    ax.set_ylabel(zname)
    ax.set_title(title or f'Y–Z section at lon={float(sec["lon"].values):.2f}')

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)


def section_xz_1var_winds(
    da: xr.DataArray,
    U: xr.DataArray,
    W: xr.DataArray,
    *,
    lat: float,
    levels: Iterable[float],
    cmap: str = 'thermal',
    time=None,
    month=None,
    w_scale: float = 1000.0,
    yinv: bool = True,
    quiver_density: int = 4,
    quiver_scale: float = 170.0,
    quiverkey_speed: float = 5.0,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Plot an X–Z section (fixed latitude) of a scalar field and overlay wind vectors (U, W).

    Parameters
    ----------
    da : xarray.DataArray
        Scalar field (time|month?, z, lat, lon).
    U : xarray.DataArray
        Zonal wind component on the same grid (time|month?, z, lat, lon).
    W : xarray.DataArray
        Vertical wind component on the same grid; will be scaled by `w_scale`.
    lat : float
        Fixed latitude for the section (nearest selection).
    levels : iterable of float
        Discrete color levels for the filled section.
    cmap : str
        cmocean colormap name (lightened internally).
    time, month : optional
        Uniform temporal selector applied to all inputs.
    w_scale : float
        Multiplicative factor for W (e.g., 1000 to convert m/s to mm/s for better visual balance).
    quiver_density : int
        Subsampling step for the quiver field (larger -> fewer arrows).
    quiver_scale : float
        Matplotlib quiver scaling parameter.
    quiverkey_speed : float
        Reference speed (m/s) shown in the quiver key.
    title, colorbar_label, output_path
        See `section_xz_1var`.

    Returns
    -------
    None
    """
    set_style()
    A  = pick_tframe(da, time=time, month=month)
    U_ = pick_tframe(U,  time=time, month=month)
    W_ = pick_tframe(W,  time=time, month=month)
    zname = _get_zcoord(A)

    sec  = A .sel(lat=lat, method='nearest')
    Usec = U_.sel(lat=lat, method='nearest')
    Wsec = W_.sel(lat=lat, method='nearest') * w_scale

    X = sec['lon'].values
    Z = sec[zname].values if zname in sec.coords else np.arange(sec.sizes[zname])

    sec_plot  = sec .transpose(zname, 'lon').values if sec .dims != (zname, 'lon') else sec .values
    U_plot    = Usec.transpose(zname, 'lon').values if Usec.dims != (zname, 'lon') else Usec.values
    W_plot    = Wsec.transpose(zname, 'lon').values if Wsec.dims != (zname, 'lon') else Wsec.values

    cm = cmo_light(cmap, .85)
    norm = _norm_from_levels(levels, cm)

    fig, ax = plt.subplots(figsize=(8, 10))
    pcm = ax.contourf(X, Z, sec_plot, levels=levels, cmap=cm, norm=norm, extend='both')
    cb = fig.colorbar(pcm, ax=ax, orientation='horizontal', shrink=.9,
                       pad=.08, aspect=25, fraction=0.05)
    label = colorbar_label or getattr(A, 'units', '')
    cb.set_label(label, labelpad=7)           
    cb.ax.tick_params(length=4, width=1.0, pad=2)

    Q = ax.quiver(X[::quiver_density], Z,
                  U_plot[:, ::quiver_density], W_plot[:, ::quiver_density],
                  scale=quiver_scale, headwidth=4, headlength=4)
    ax.quiverkey(Q, 0.87, 1.02, quiverkey_speed, f'{quiverkey_speed} m/s',
                 labelpos='E', coordinates='axes', labelsep=0.05)
    
    if yinv:
        ax.invert_yaxis()
    
    ax.set_xlabel('Longitude (°)')
    ax.set_ylabel(zname)
    ax.set_title(title or f'X–Z section (lat={float(sec["lat"].values):.2f}) with winds (U,W)')



    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)

def section_yz_1var_winds(
    da: xr.DataArray,
    V: xr.DataArray,
    W: xr.DataArray,
    *,
    lon: float,
    levels: Iterable[float],
    cmap: str = 'thermal',
    yinv: bool = True,
    time=None,
    month=None,
    w_scale: float = 1000.0,
    quiver_density: int = 4,
    quiver_scale: float = 170.0,
    quiverkey_speed: float = 5.0,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Plot a Y–Z section (fixed longitude) of a scalar field and overlay wind vectors (V, W).

    Parameters
    ----------
    da : xarray.DataArray
        Scalar field (time|month?, z, lat, lon).
    V : xarray.DataArray
        Meridional wind component on the same grid (time|month?, z, lat, lon).
    W : xarray.DataArray
        Vertical wind component on the same grid; scaled by `w_scale`.
    lon : float
        Fixed longitude for the section (nearest selection).
    levels : iterable of float
        Discrete color levels for the filled section.
    cmap : str
        cmocean colormap name (lightened internally).
    time, month, w_scale, quiver_density, quiver_scale, quiverkey_speed
        See `section_xz_1var_winds`.
    title, colorbar_label, output_path
        See `section_xz_1var`.

    Returns
    -------
    None
    """
    set_style()
    A  = pick_tframe(da, time=time, month=month)
    V_ = pick_tframe(V,  time=time, month=month)
    W_ = pick_tframe(W,  time=time, month=month)
    zname = _get_zcoord(A)

    sec  = A .sel(lon=lon, method='nearest')
    Vsec = V_.sel(lon=lon, method='nearest')
    Wsec = W_.sel(lon=lon, method='nearest') * w_scale

    Y = sec['lat'].values
    Z = sec[zname].values if zname in sec.coords else np.arange(sec.sizes[zname])

    sec_plot = sec .transpose(zname, 'lat').values if sec .dims != (zname, 'lat') else sec .values
    V_plot   = Vsec.transpose(zname, 'lat').values if Vsec.dims != (zname, 'lat') else Vsec.values
    W_plot   = Wsec.transpose(zname, 'lat').values if Wsec.dims != (zname, 'lat') else Wsec.values

    cm = cmo_light(cmap, .85)
    norm = _norm_from_levels(levels, cm)

    fig, ax = plt.subplots(figsize=(8, 10))
    pcm = ax.contourf(Y, Z, sec_plot, levels=levels, cmap=cm, norm=norm, extend='both')
    cb = fig.colorbar(pcm, ax=ax, orientation='horizontal', shrink=.9,
                       pad=.08, aspect=25, fraction=0.05)
    label = colorbar_label or getattr(A, 'units', '')
    cb.set_label(label, labelpad=7)           
    cb.ax.tick_params(length=4, width=1.0, pad=2)

    Q = ax.quiver(Y[::quiver_density], Z,
                  V_plot[:, ::quiver_density], W_plot[:, ::quiver_density],
                  scale=quiver_scale, headwidth=4, headlength=4)
    ax.quiverkey(Q, 0.87, 1.02, quiverkey_speed, f'{quiverkey_speed} m/s',
                 labelpos='E', coordinates='axes', labelsep=0.05)
    if yinv:
        ax.invert_yaxis()

    ax.set_xlabel('Latitude (°)')
    ax.set_ylabel(zname)
    ax.set_title(title or f'Y–Z section (lon={float(sec["lon"].values):.2f}) with winds (V,W)')

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)