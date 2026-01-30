from __future__ import annotations
from typing import Iterable, Optional, Tuple, Union
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfe
from cartopy.io.shapereader import Reader
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
import cmocean
import importlib.resources
from pathlib import Path

DEFAULT_EXTENT = (-93.8, -68.0, -21.9, 4.1)  # Peru and surrounding region

def set_style(fontsize: int = 14, family: str = "Monospace"):
    """
    Apply a clean, publication-quality visual style for all SCAHPy plots.

    Parameters
    ----------
    fontsize : int, optional
        Base font size for ticks, labels, and legends.
        Titles and axis labels will scale automatically from this base.
        Defaults to 14 for paper-ready figures.
    family : str, optional
        Font family to use (e.g., "DejaVu Sans", "monospace", "Arial").
    """

    # Escalas relativas para jerarquía tipográfica
    title_size = fontsize + 2      # títulos ligeramente más grandes
    label_size = fontsize + 0      # ejes igual al base
    tick_size  = fontsize - 1      # ticks un poco más pequeños
    legend_size = fontsize - 2

    plt.style.use("seaborn-v0_8-whitegrid")

    plt.rcParams.update({
        # === Fuentes y tamaños ===
        "font.family": family,
        "font.size": fontsize,
        "axes.titlesize": title_size,
        "axes.labelsize": label_size,
        "xtick.labelsize": tick_size,
        "ytick.labelsize": tick_size,
        "legend.fontsize": legend_size,
        "figure.titlesize": title_size,

        # === Colores y fondo ===
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "text.color": "#222222",
        "axes.labelcolor": "#222222",
        "xtick.color": "#222222",
        "ytick.color": "#222222",

        # === Líneas, spines y ticks ===
        "axes.linewidth": 1.5,
        "axes.edgecolor": "#303030",
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 7,
        "ytick.major.size": 7,
        "xtick.minor.size": 4,
        "ytick.minor.size": 4,
        "xtick.major.width": 1.5,
        "ytick.major.width": 1.5,
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,

        # === Grillas sutiles ===
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.8,
        "grid.linestyle": ":",
        "axes.axisbelow": True,

        # === Líneas y colores por defecto ===
        "lines.linewidth": 1.5,
        "lines.color": "#2b2b2b",

        # === Figuras y guardado ===
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.transparent": False,
    })

def sa_feature(shapefile: Optional[str] = None) -> cfe.ShapelyFeature:
    """
    Load the default South America shapefile or a user-provided one.

    Parameters
    ----------
    shapefile : str or None, optional
        Path to a custom shapefile (.shp). If None, loads the default 
        'SA_paises.shp' distributed within the scahpy.data module.

    Returns
    -------
    cartopy.feature.ShapelyFeature
        A ready-to-use Cartopy feature (coastlines, borders, etc.)
        for geographic map plotting.

    Raises
    ------
    FileNotFoundError
        If the specified shapefile path does not exist.
    """
    if shapefile is None:
        try:
            data_dir = importlib.resources.files("scahpy.data")
            shp = Path(data_dir, "SA_paises.shp")
        except Exception as e:
            raise FileNotFoundError(
                "Could not locate the default South America shapefile. "
                "Ensure 'scahpy.data/SA_paises.shp' is packaged correctly."
            ) from e
    else:
        shp = Path(shapefile)

    if not shp.exists():
        raise FileNotFoundError(f"Shapefile not found: {shp}")

    return cfe.ShapelyFeature(
        Reader(shp).geometries(),
        ccrs.PlateCarree(),
        edgecolor="k",
        facecolor="none",
        linewidth=0.6,
        zorder=5
    )

def format_geoaxes(
    ax,
    extent: tuple,
    *,
    xticks: Optional[Iterable[float]] = None,
    yticks: Optional[Iterable[float]] = None,
    tick_step: Optional[tuple] = (5, 5),
    draw_grid: bool = False,
) -> None:
    """
    Set extent, longitude/latitude formatters, and (optionally) ticks/grid.

    Parameters
    ----------
    ax : cartopy GeoAxes
    extent : (lon_min, lon_max, lat_min, lat_max)
    xticks, yticks : explicit tick positions (in degrees). If None and
        tick_step is provided, ticks are generated every tick_step degrees.
    tick_step : (dx, dy) in degrees. Ignored if xticks/yticks are provided.
    draw_grid : if True, draw light gridlines using the same tick locators.
    """
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter())
    ax.yaxis.set_major_formatter(LatitudeFormatter())

    if (xticks is None or yticks is None) and (tick_step is not None):
        lon_min, lon_max, lat_min, lat_max = extent
        dx, dy = tick_step
        if xticks is None:
            start = np.ceil(lon_min / dx) * dx
            xticks = np.arange(start, lon_max + 1e-9, dx)
        if yticks is None:
            start = np.ceil(lat_min / dy) * dy
            yticks = np.arange(start, lat_max + 1e-9, dy)

    if xticks is not None:
        ax.set_xticks(xticks, crs=ccrs.PlateCarree())
    if yticks is not None:
        ax.set_yticks(yticks, crs=ccrs.PlateCarree())

    if draw_grid:
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(), linewidth=0.6, color='0.6',
            alpha=0.5, linestyle=':'
        )
        if xticks is not None:
            gl.xlocator = mticker.FixedLocator(xticks)
        if yticks is not None:
            gl.ylocator = mticker.FixedLocator(yticks)

def cmo_light(name_or_cmap: Union[str, mcolors.Colormap], lighten: float = 0.85) -> mcolors.Colormap:
    """
    Return a lightened version of a cmocean colormap for better readability.

    Parameters
    ----------
    name_or_cmap : str or matplotlib.colors.Colormap
        - If str: the name of a cmocean colormap (e.g., "thermal", "haline", "balance").
        - If Colormap: an existing matplotlib Colormap instance.
    lighten : float, optional
        Lightening factor between 0 (no change) and 1 (completely white).
        Defaults to 0.85 (≈15% lighter).

    Returns
    -------
    matplotlib.colors.Colormap
        A lightened copy of the specified colormap.

    """
    if isinstance(name_or_cmap, str):
        try:
            cm = getattr(cmocean.cm, name_or_cmap)
        except AttributeError:
            cm = plt.get_cmap(name_or_cmap)
    else:
        cm = name_or_cmap
    return cmocean.tools.lighten(cm, lighten)

def boundary_norm(levels: Iterable[float], cmap: mcolors.Colormap) -> mcolors.BoundaryNorm:
    """
    Create a BoundaryNorm object for discrete contour levels.

    Parameters
    ----------
    levels : iterable of float
        Contour or color levels to use.
    cmap : matplotlib.colors.Colormap
        The colormap associated with the data.

    Returns
    -------
    matplotlib.colors.BoundaryNorm
    """
    return mcolors.BoundaryNorm(list(levels), cmap.N)

def pick_tframe(da: xr.DataArray, *, time=None, month=None) -> xr.DataArray:
    """
    Select a single time or month frame from a DataArray.
    Works transparently for datasets with either a `time` or `month` dimension.

    Parameters
    ----------
    da : xarray.DataArray
        Input data array.
    time : str or int, optional
        If str, selects by timestamp (nearest). If int, selects by index.
    month : int, optional
        Month index (1–12) if working with climatological datasets.

    Returns
    -------
    xarray.DataArray
        The selected frame or the unmodified DataArray if no valid selector is provided.
    """
    out = da
    if month is not None and ('month' in out.dims or 'month' in out.coords):
        return out.sel(month=month)
    if time is not None and ('time' in out.dims or 'time' in out.coords):
        if isinstance(time, (int, np.integer)):
            return out.isel(time=int(time))
        return out.sel(time=time, method='nearest')
    return out

def area_mean(da: xr.DataArray, lat_range: Tuple[float, float], lon_range: Tuple[float, float]) -> xr.DataArray:
    """
    Compute the mean value of a DataArray within a given latitude–longitude box.

    Parameters
    ----------
    da : xarray.DataArray
        Input variable.
    lat_range : tuple
        (lat_min, lat_max)
    lon_range : tuple
        (lon_min, lon_max)

    Returns
    -------
    xarray.DataArray
        Area-averaged time series.
    """
    sub = da.sel(lat=slice(lat_range[0], lat_range[1]),
                 lon=slice(lon_range[0], lon_range[1]))
    return sub.mean(dim=('lat', 'lon'), skipna=True)

def maybe_save(fig, path: Optional[str]) -> None:
    """
    Save a figure to disk if a path is provided.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    path : str or None
        Output file path (e.g., 'output/map.png'). If None, the figure is not saved.
    """
    if path:
        fig.savefig(path, bbox_inches='tight', dpi=300, facecolor='white', transparent=False)

def quiver_on_map(ax, lons, lats, U, V, step: int = 7, qkey_speed: float = 5.0):
    """
    Plot a vector (quiver) field on a Cartopy map and add a quiver key.

    Parameters
    ----------
    ax : cartopy.mpl.geoaxes.GeoAxesSubplot
        Target axis for the quiver plot.
    lons, lats : numpy.ndarray
        Longitude and latitude coordinate arrays.
    U, V : xarray.DataArray or numpy.ndarray
        Zonal and meridional components of the vector field.
    step : int
        Subsampling step to reduce arrow density.
    qkey_speed : float
        Reference speed displayed in the quiver key (m/s).

    Returns
    -------
    matplotlib.quiver.Quiver
        The quiver object created.
    """
    Q = ax.quiver(lons[::step], lats[::step],
                  U[::step, ::step], V[::step, ::step],
                  headwidth=5, headlength=7)
    ax.quiverkey(Q, 0.92, 1.02, qkey_speed, f'{qkey_speed} m/s',
                 labelpos='E', coordinates='axes', labelsep=0.05)
    return Q
