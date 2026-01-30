from __future__ import annotations
from typing import Optional, Tuple, List, Dict
import xarray as xr
import matplotlib.pyplot as plt

from ._helpers import set_style, area_mean, maybe_save

def _to_area_series(
    da: xr.DataArray,
    lat_range: Optional[Tuple[float, float]],
    lon_range: Optional[Tuple[float, float]],
) -> xr.DataArray:
    """
    Reduce a DataArray to a 1D time (or month) series using spatial means.

    If latitude and longitude ranges are provided and those dimensions exist,
    an area-mean is computed over the given box. Any remaining non-temporal
    dimensions are averaged out.

    Parameters
    ----------
    da : xr.DataArray
        Input data array (with 'time' or 'month' coordinate).
    lat_range, lon_range : tuple of float, optional
        Latitude and longitude bounds (min, max) for spatial averaging.

    Returns
    -------
    xr.DataArray
        One-dimensional series over 'time' or 'month'.
    """
    A = da
    if (
        lat_range is not None
        and lon_range is not None
        and ("lat" in A.dims)
        and ("lon" in A.dims)
    ):
        A = area_mean(A, lat_range, lon_range)

    if "time" in A.dims:
        other = [d for d in A.dims if d != "time"]
        if other:
            A = A.mean(dim=other, skipna=True)
    elif "month" in A.dims:
        other = [d for d in A.dims if d != "month"]
        if other:
            A = A.mean(dim=other, skipna=True)

    return A


def _apply_resample(series: xr.DataArray, resample: Optional[str]) -> xr.DataArray:
    """
    Optionally resample the series along the 'time' dimension.

    Parameters
    ----------
    series : xr.DataArray
        Input time series.
    resample : str, optional
        Resampling frequency (e.g., 'M', 'Y', 'Q').

    Returns
    -------
    xr.DataArray
        Resampled series if applicable; otherwise the original series.
    """
    if resample and ("time" in series.dims):
        return series.resample(time=resample).mean()
    return series


def _sel_point_nearest(da_like: xr.DataArray, la: float, lo: float) -> xr.DataArray:
    """
    Select a grid point using nearest neighbor search in two steps
    (lat first, then lon). This avoids xarray slice/method conflicts.

    Parameters
    ----------
    da_like : xr.DataArray
        Data array with 'lat' and 'lon' dimensions.
    la, lo : float
        Target latitude and longitude.

    Returns
    -------
    xr.DataArray
        Data at the nearest grid point to (la, lo).
    """
    da_tmp = da_like.copy(deep=False)
    try:
        out = da_tmp.sel(lat=la, method="nearest")
        out = out.sel(lon=lo, method="nearest")
        return out
    except NotImplementedError:
        lat_idx = abs(da_tmp["lat"] - la).argmin()
        lon_idx = abs(da_tmp["lon"] - lo).argmin()
        return da_tmp.isel(lat=lat_idx, lon=lon_idx)

def ts_area_1var(
    da: xr.DataArray,
    *,
    lat_range: Optional[Tuple[float, float]] = None,
    lon_range: Optional[Tuple[float, float]] = None,
    resample: Optional[str] = None,
    label: str = "Series",
    color: str = "#1b9e77",
    linestyle: str = "-",
    linewidth: float = 1.8,
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Plot a time series (or monthly climatological cycle) averaged over a lat–lon box.

    Parameters
    ----------
    da : xr.DataArray
        Input data array with 'time' or 'month' coordinate.
    lat_range, lon_range : tuple of float, optional
        Latitude/longitude bounds (min, max) for area averaging.
    resample : str, optional
        Resampling frequency (e.g., 'M', 'Y', 'Q'). Only if 'time' exists.
    label, color, linestyle, linewidth, title, ylabel, output_path : optional
        Plot styling and output controls.

    """
    set_style()
    s = _to_area_series(da, lat_range, lon_range)
    s = _apply_resample(s, resample=resample)

    fig, ax = plt.subplots(figsize=(16, 5))
    s.plot(ax=ax, label=label, color=color, linestyle=linestyle, linewidth=linewidth, zorder=10)

    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right")
    ax.set_xlabel("Month" if "month" in s.dims else "Time" if "time" in s.dims else "")
    ax.set_ylabel(ylabel or getattr(da, "units", ""))
    if title:
        ax.set_title(title)

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)


def ts_point_1var(
    da: xr.DataArray,
    *,
    lat: float | List[Tuple[float, float]] | List[float],
    lon: Optional[float] = None,
    resample: Optional[str] = None,
    labels: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    linestyles: Optional[List[str]] = None,
    linewidth: float = 1.8,
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Plot one or multiple point series (time or monthly) from a DataArray.

    Parameters
    ----------
    da : xr.DataArray
        Input data array with 'time' or 'month' coordinate.
    lat, lon : float | list | list[tuple]
        - Single point: lat=float and lon=float
        - Multiple points: [(lat1, lon1), (lat2, lon2), ...]
    resample : str, optional
        Resampling frequency (e.g., 'M', 'Y', 'Q'). Only if 'time' exists.
    labels, colors, linestyles : list, optional
        Styling per point series. Defaults will be generated if not provided.
    linewidth, title, ylabel, output_path : optional
        Plot styling and output controls.

    """
    set_style()
    fig, ax = plt.subplots(figsize=(16, 5))

    if isinstance(lat, (float, int)) and isinstance(lon, (float, int)):
        coords = [(float(lat), float(lon))]
    elif isinstance(lat, (list, tuple)) and lon is None:
        coords = [(float(la), float(lo)) for la, lo in lat]
    else:
        raise ValueError(
            "Provide either (lat, lon) as floats for a single point, "
            "or a list of coordinate pairs [(lat1, lon1), ...]."
        )

    n = len(coords)
    labels = labels or [f"Point {i+1}" for i in range(n)]
    colors = colors or [None] * n
    linestyles = linestyles or ["-"] * n

    last_series = None
    for i, (la, lo) in enumerate(coords):
        p = _sel_point_nearest(da, la, lo)

        if "time" in p.dims:
            other = [d for d in p.dims if d != "time"]
            if other:
                p = p.mean(dim=other, skipna=True)
        elif "month" in p.dims:
            other = [d for d in p.dims if d != "month"]
            if other:
                p = p.mean(dim=other, skipna=True)

        p = _apply_resample(p, resample=resample)

        p.plot(
            ax=ax,
            label=labels[i],
            color=colors[i],
            linestyle=linestyles[i],
            linewidth=linewidth,
        )
        last_series = p

    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right")
    if last_series is not None:
        ax.set_xlabel("Month" if "month" in last_series.dims else "Time" if "time" in last_series.dims else "")
    ax.set_ylabel(ylabel or getattr(da, "units", ""))
    if title:
        ax.set_title(title)

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)


def ts_area_multi(
    series: List[Dict],
    *,
    lat_range: Optional[Tuple[float, float]] = None,
    lon_range: Optional[Tuple[float, float]] = None,
    resample: Optional[str] = None,
    title: Optional[str] = None,
    ylabel: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Plot multiple series averaged over the same lat–lon box.

    Parameters
    ----------
    series : list of dict
        Each item must include {"da": DataArray, "label": str?, "color": str?, "linestyle": str?, "linewidth": float?}
    lat_range, lon_range : tuple of float, optional
        Latitude/longitude bounds (min, max) for area averaging.
    resample : str, optional
        Resampling frequency (e.g., 'M', 'Y', 'Q').
    title, ylabel, output_path : optional
        Plot styling and output controls.

    """

    set_style()
    fig, ax = plt.subplots(figsize=(18, 6))

    last_series = None
    for item in series:
        da_i = item["da"]
        label = item.get("label", getattr(da_i, "name", "Series"))
        color = item.get("color", None)
        linestyle = item.get("linestyle", "-")
        linewidth = item.get("linewidth", 1.8)

        s = _to_area_series(da_i, lat_range, lon_range)
        s = _apply_resample(s, resample=resample)
        s.plot(ax=ax, label=label, color=color, linestyle=linestyle, linewidth=linewidth)
        last_series = s

    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(loc="upper right")
    if last_series is not None:
        ax.set_xlabel("Month" if "month" in last_series.dims else "Time" if "time" in last_series.dims else "")
    ax.set_ylabel(ylabel or "")
    if title:
        ax.set_title(title)

    maybe_save(fig, output_path)
    if output_path is None:
        plt.show()
    plt.close(fig)
