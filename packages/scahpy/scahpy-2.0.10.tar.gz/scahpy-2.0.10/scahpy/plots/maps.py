from __future__ import annotations
from typing import Iterable, Optional, Tuple
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from ._helpers import (
    set_style, sa_feature, cmo_light, boundary_norm, format_geoaxes,
    maybe_save, quiver_on_map, DEFAULT_EXTENT, pick_tframe
)

def map_1var(
    da: xr.DataArray,
    *,
    levels: Iterable[float],
    cmap: str = 'rain',
    shapefile: Optional[str] = None,
    extent: Optional[Tuple[float, float, float, float]] = None,
    xticks: Optional[Iterable[float]] = None,
    yticks: Optional[Iterable[float]] = None,
    tick_step: Optional[Tuple[float, float]] = (5, 5),
    draw_grid: bool = False,
    time=None,
    month=None,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Draw a filled map of a single scalar variable.

    The same temporal selection is applied to the data via:
        - `month` (for climatological datasets with a `month` coordinate), or
        - `time` (for datasets with a `time` coordinate; can be int index or str timestamp).

    Parameters
    ----------
    da : xarray.DataArray
        Scalar field with coordinates `(lat, lon)` and optionally `time` or `month`.
    levels : iterable of float
        Discrete color levels for the filled contours.
    cmap : str
        Name of the cmocean colormap to use (lightened internally).
    shapefile : str or None
        Path to a custom shapefile. If None, uses the default South America shape.
    extent : tuple or None
        Map extent `(lon_min, lon_max, lat_min, lat_max)`. If None, uses DEFAULT_EXTENT.
    time : int or str or None
        If dataset has `time`, selects a single frame: index (int) or timestamp (str).
    month : int or None
        If dataset has `month`, selects that month (1-12).
    title : str or None
        Figure title. If None, uses `long_name` or variable name.
    colorbar_label : str or None
        Colorbar label. If None, uses `da.units` if available.
    output_path : str or None
        If provided, saves the figure to disk; otherwise shows the figure.

    """
    set_style()
    extent = extent or DEFAULT_EXTENT
    sa = sa_feature(shapefile)
    A = pick_tframe(da, time=time, month=month)

    cm = cmo_light(cmap, .85)
    norm = boundary_norm(levels, cm)
    lons = A['lon'].values
    lats = A['lat'].values

    fig, ax = plt.subplots(figsize=(13, 12), subplot_kw=dict(projection=ccrs.PlateCarree()))
    pcm = ax.contourf(lons, lats, A, levels=levels, cmap=cm, norm=norm,
                      extend='both', transform=ccrs.PlateCarree())
    cb = fig.colorbar(pcm, ax=ax, orientation='vertical', shrink=.7, pad=0.03, aspect=20)
    cb.ax.set_ylabel(colorbar_label or getattr(A, 'units', ''))

    ax.add_feature(sa, linewidth=.7, zorder=7)

    format_geoaxes(
        ax,
        extent,
        xticks=xticks,
        yticks=yticks,
        tick_step=tick_step,
        draw_grid=draw_grid,
    )
    ax.set_title(title or getattr(A, 'long_name', str(A.name)))

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)


def map_1var_winds(
    da: xr.DataArray,
    U: xr.DataArray,
    V: xr.DataArray,
    *,
    levels: Iterable[float],
    cmap: str = 'rain',
    shapefile: Optional[str] = None,
    extent: Optional[Tuple[float, float, float, float]] = None,
    xticks: Optional[Iterable[float]] = None,
    yticks: Optional[Iterable[float]] = None,
    tick_step: Optional[Tuple[float, float]] = (5, 5),
    draw_grid: bool = False,
    time=None,
    month=None,
    quiver_subsample: int = 7,
    quiverkey_speed: float = 5.0,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Draw a filled map of a scalar variable and overlay wind vectors (U, V).

    The same temporal selection (`time` or `month`) is applied uniformly to `da`, `U`, and `V`.

    Parameters
    ----------
    da : xarray.DataArray
        Scalar field with `(lat, lon)` and optionally `time`/`month`.
    U, V : xarray.DataArray
        Vector components with the same horizontal grid as `da`.
    levels : iterable of float
        Discrete color levels for the filled contours.
    cmap : str
        Name of the cmocean colormap (lightened internally).
    shapefile : str or None
        Custom shapefile path; None uses default SA shapefile.
    extent : tuple or None
        Map extent `(lon_min, lon_max, lat_min, lat_max)`.
    time, month : see `map_1var`
        Temporal selector (applied to all inputs).
    quiver_subsample : int
        Arrow subsampling step to reduce density.
    quiverkey_speed : float
        Reference speed (m/s) shown in the quiver key.
    title, colorbar_label, output_path : see `map_1var`.

    """
    set_style()
    extent = extent or DEFAULT_EXTENT
    sa = sa_feature(shapefile)

    A = pick_tframe(da, time=time, month=month)
    Uv = pick_tframe(U, time=time, month=month)
    Vv = pick_tframe(V, time=time, month=month)

    cm = cmo_light(cmap, .85)
    norm = boundary_norm(levels, cm)
    lons = A['lon'].values
    lats = A['lat'].values

    fig, ax = plt.subplots(figsize=(13, 12), subplot_kw=dict(projection=ccrs.PlateCarree()))
    pcm = ax.contourf(lons, lats, A, levels=levels, cmap=cm, norm=norm,
                      extend='both', transform=ccrs.PlateCarree())
    cb = fig.colorbar(pcm, ax=ax, orientation='vertical', shrink=.7, pad=0.03, aspect=20)
    cb.ax.set_ylabel(colorbar_label or getattr(A, 'units', ''))

    quiver_on_map(ax, lons, lats, Uv, Vv, step=quiver_subsample, qkey_speed=quiverkey_speed)

    ax.add_feature(sa, linewidth=.7, zorder=7)

    format_geoaxes(
        ax,
        extent,
        xticks=xticks,
        yticks=yticks,
        tick_step=tick_step,
        draw_grid=draw_grid,
    )

    ax.set_title(title or getattr(A, 'long_name', str(A.name)))

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)


def map_2var_contours(
    da_fill: xr.DataArray,
    da_contour: xr.DataArray,
    *,
    levels_fill: Iterable[float],
    levels_contour: Iterable[float],
    cmap_fill: str = 'rain',
    colors_contour=('k',),
    linewidths_contour=(1.4,),
    alpha_contour: float = 0.9,
    shapefile: Optional[str] = None,
    extent: Optional[Tuple[float, float, float, float]] = None,
    xticks: Optional[Iterable[float]] = None,
    yticks: Optional[Iterable[float]] = None,
    tick_step: Optional[Tuple[float, float]] = (5, 5),
    draw_grid: bool = False,
    time=None,
    month=None,
    label_levels: bool = True,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Draw a filled map of a scalar variable and overlay contours
    (either of the same variable or another one).

    The same temporal selection (`time` or `month`) is applied to both layers.

    Parameters
    ----------
    da_fill : xarray.DataArray
        Scalar field for filled contours (background).
    da_contour : xarray.DataArray
        Field for line contours.
    levels_fill : iterable of float
        Levels for filled contours.
    levels_contour : iterable of float
        Levels for the contour lines.
    cmap_fill : str
        cmocean colormap name for the filled layer (lightened internally).
    colors_contour : tuple
        Colors for contour lines.
    linewidths_contour : tuple
        Line widths for contour lines.
    alpha_contour : float
        Alpha for contour lines.
    shapefile, extent, time, month, title, colorbar_label, output_path
        See `map_1var`.

    Returns
    -------
    None
    """
    set_style()
    extent = extent or DEFAULT_EXTENT
    sa = sa_feature(shapefile)

    A = pick_tframe(da_fill, time=time, month=month)
    C = pick_tframe(da_contour, time=time, month=month)

    cm = cmo_light(cmap_fill, .85)
    norm = boundary_norm(levels_fill, cm)
    lons = A['lon'].values
    lats = A['lat'].values

    fig, ax = plt.subplots(figsize=(13, 12), subplot_kw=dict(projection=ccrs.PlateCarree()))
    pcm = ax.contourf(lons, lats, A, levels=levels_fill, cmap=cm, norm=norm,
                      extend='both', transform=ccrs.PlateCarree())
    cb = fig.colorbar(pcm, ax=ax, orientation='vertical', shrink=.7, pad=0.03, aspect=20)
    cb.ax.set_ylabel(colorbar_label or getattr(A, 'units', ''))

    cc = ax.contour(lons, lats, C, levels=levels_contour,
                    colors=colors_contour, linewidths=linewidths_contour,
                    alpha=alpha_contour, transform=ccrs.PlateCarree(), zorder=7)
    if label_levels:
        ax.clabel(cc, levels=levels_contour, inline=False, colors='k', fontsize=11, zorder=9)

    ax.add_feature(sa, linewidth=.7, zorder=7)
    format_geoaxes(
        ax,
        extent,
        xticks=xticks,
        yticks=yticks,
        tick_step=tick_step,
        draw_grid=draw_grid,
    )
    ax.set_title(title or getattr(A, 'long_name', str(A.name)))

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)


def map_2vars_winds(
    da_fill: xr.DataArray,
    da_contour: xr.DataArray,
    U: xr.DataArray,
    V: xr.DataArray,
    *,
    levels_fill: Iterable[float],
    levels_contour: Iterable[float],
    cmap_fill: str = 'rain',
    colors_contour=('#F29727', '#C70039', '#511F73'),
    linewidths_contour=(1.5, 1.6, 1.8),
    alpha_contour: float = 0.45,
    quiver_subsample: int = 7,
    quiverkey_speed: float = 5.0,
    shapefile: Optional[str] = None,
    extent: Optional[Tuple[float, float, float, float]] = None,
    xticks: Optional[Iterable[float]] = None,
    yticks: Optional[Iterable[float]] = None,
    tick_step: Optional[Tuple[float, float]] = (5, 5),
    draw_grid: bool = False,
    time=None,
    month=None,
    title: Optional[str] = None,
    colorbar_label: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Draw a filled map (1 variable) + contour overlays (another variable)
    + wind vectors (U, V) — ideal for ocean–atmosphere mixed maps.

    The same temporal selection (`time` or `month`) is applied uniformly to all layers.

    Parameters
    ----------
    da_fill : xarray.DataArray
        Scalar field for the filled layer (background).
    da_contour : xarray.DataArray
        Field for contour lines.
    U, V : xarray.DataArray
        Vector components (same horizontal grid).
    levels_fill, levels_contour : iterable of float
        Levels for background and contour lines respectively.
    cmap_fill : str
        cmocean colormap name for the filled layer (lightened internally).
    colors_contour, linewidths_contour, alpha_contour
        Style parameters for contour lines.
    quiver_subsample : int
        Arrow subsampling step.
    quiverkey_speed : float
        Reference speed (m/s) shown in the quiver key.
    shapefile, extent, time, month, title, colorbar_label, output_path
        See `map_1var`.

    Returns
    -------
    None
    """
    set_style()
    extent = extent or DEFAULT_EXTENT
    sa = sa_feature(shapefile)

    A = pick_tframe(da_fill, time=time, month=month)
    C = pick_tframe(da_contour, time=time, month=month)
    Uv = pick_tframe(U, time=time, month=month)
    Vv = pick_tframe(V, time=time, month=month)

    cm = cmo_light(cmap_fill, .85)
    norm = boundary_norm(levels_fill, cm)
    lons = A['lon'].values
    lats = A['lat'].values

    fig, ax = plt.subplots(figsize=(13, 12), subplot_kw=dict(projection=ccrs.PlateCarree()))
    pcm = ax.contourf(lons, lats, A, levels=levels_fill, cmap=cm, norm=norm,
                      extend='both', transform=ccrs.PlateCarree())
    cb = fig.colorbar(pcm, ax=ax, orientation='vertical', shrink=.7, pad=0.03, aspect=20)
    cb.ax.set_ylabel(colorbar_label or getattr(A, 'units', ''))

    cc = ax.contour(lons, lats, C, levels=levels_contour,
                    colors=colors_contour, linewidths=linewidths_contour,
                    alpha=alpha_contour, transform=ccrs.PlateCarree(), zorder=7)
    ax.clabel(cc, levels=levels_contour, inline=False, colors='k', fontsize=11, zorder=9)

    quiver_on_map(ax, lons, lats, Uv, Vv, step=quiver_subsample, qkey_speed=quiverkey_speed)

    ax.add_feature(sa, linewidth=.7, zorder=7)

    format_geoaxes(
        ax,
        extent,
        xticks=xticks,
        yticks=yticks,
        tick_step=tick_step,
        draw_grid=draw_grid,
    )

    ax.set_title(title or 'Map: filled + contours + winds')

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)
