import numpy as np
import xarray as xr
from typing import Sequence

from ...core.coords import destagger_array
from ...core.vertical import vertical_interp
from .wrf_diags import pressure,geop_height

def _new_wrf_coords(
    ds_wrf: xr.Dataset,
    ds_meta: dict[str, list],
    lats,
    lons,
    destag: bool = True,
    lats_v=None,
    lons_u=None,
) -> xr.Dataset:
    """
    Build standard coordinates and (optionally) destagger WRF variables.

    Parameters
    ----------
    ds_wrf : xr.Dataset
        WRF dataset after concatenation and time processing.
    ds_meta : dict[str, list]
        Metadata dictionary from `get_metadata_vars` (model='WRF').
    lats, lons :
        1D latitude and longitude arrays for centered grid coordinates.
    destag : bool, default True
        If True, destagger variables along their *_stag dimensions.
    lats_v, lons_u :
        1D coordinates for V and U staggered dimensions (only used if destag=False).

    Returns
    -------
    xr.Dataset
        Dataset with standardized coordinates (lat, lon, time) and
        (optionally) destaggered variables.
    """
    list_X_keys = [k for k, v in ds_meta.items() if "west_east_stag" in v[0]]
    list_Y_keys = [k for k, v in ds_meta.items() if "south_north_stag" in v[0]]
    list_Z_keys = [k for k, v in ds_meta.items() if "bottom_top_stag" in v[0]]
    list_S_keys = [k for k, v in ds_meta.items() if "soil_layers_stag" in v[0]]

    if destag:
        for var in ds_wrf:
            if var in list_X_keys:
                ds_wrf[var] = destagger_array(ds_wrf[var], "west_east_stag").rename(
                    {"west_east_stag": "west_east"}
                )
            elif var in list_Y_keys:
                ds_wrf[var] = destagger_array(ds_wrf[var], "south_north_stag").rename(
                    {"south_north_stag": "south_north"}
                )
            elif var in list_Z_keys:
                ds_wrf[var] = destagger_array(ds_wrf[var], "bottom_top_stag").rename(
                    {"bottom_top_stag": "bottom_top"}
                )
            elif var in list_S_keys:
                ds_wrf[var] = destagger_array(ds_wrf[var], "soil_layers_stag").rename(
                    {"soil_layers_stag": "soil_layers"}
                )
    else:
        for var in ds_wrf:
            if var in list_X_keys and lons_u is not None:
                ds_wrf[var] = ds_wrf[var].assign_coords(
                    west_east_stag=("west_east_stag", lons_u)
                )
            elif var in list_Y_keys and lats_v is not None:
                ds_wrf[var] = ds_wrf[var].assign_coords(
                    south_north_stag=("south_north_stag", lats_v)
                )

    ds_wrf = ds_wrf.assign_coords(
        south_north=("south_north", lats),
        west_east=("west_east", lons),
    )

    drop_coords = ["XLAT", "XLONG", "XLAT_U", "XLONG_U", "XLAT_V", "XLONG_V"]
    ds_wrf = ds_wrf.drop_vars([c for c in drop_coords if c in ds_wrf.variables], errors="ignore")

    ds_wrf = ds_wrf.rename({"south_north": "lat", "west_east": "lon"})
    ds_wrf["lat"].attrs = {
        "units": "degrees_north",
        "axis": "Y",
        "long_name": "Latitude",
        "standard_name": "latitude",
    }
    ds_wrf["lon"].attrs = {
        "units": "degrees_east",
        "axis": "X",
        "long_name": "Longitude",
        "standard_name": "longitude",
    }

    for var in ds_wrf.data_vars:
        coords = ds_wrf[var].coords
        if all(c in coords for c in ["lat", "lon", "time"]):
            ds_wrf[var].encoding["coordinates"] = "time lat lon"

    return ds_wrf

def vert_levs(
    ds: xr.Dataset,
    varis: Sequence[str],
    lvls: Sequence[float] | None = None,
    coord_kind: str = "pressure",   # "pressure" | "height"
    vert_dim: str = "bottom_top",
    new_dim: str = "levels",
    mask_outside: bool = True,
    persist: bool = False,
    nan_opt: str = 'both',
) -> xr.Dataset:
    """
    Interpolate WRF variables from model (sigma) levels to fixed
    pressure or height levels.

    This function performs a 1D vertical interpolation for one or more
    3-D variables contained in a WRF dataset. The vertical coordinate can be
    total pressure (P + PB) or geopotential height ((PH + PHB)/g), and the
    interpolation is handled through `interp1d_along_dim` from `scahpy.core.vertical`.

    Parameters
    ----------
    ds : xr.Dataset
        WRF dataset containing 3-D fields and native vertical coordinates
        (P, PB, PH, PHB, etc.).
    varis : sequence of str
        Names of variables to interpolate vertically.
    lvls : sequence of float, optional
        Target levels. If ``None``, a default list is used depending on
        ``coord_kind``:
            - For ``"pressure"`` → [1000, 975, 950, ..., 200] hPa  
            - For ``"height"``   → [0, 50, 100, ..., 5000] m
    coord_kind : {"pressure", "height"}, default "pressure"
        Type of target coordinate:
        - ``"pressure"`` → interpolates to isobaric levels (hPa)
        - ``"height"`` → interpolates to constant height levels (m a.s.l.)
    vert_dim : str, default "bottom_top"
        Name of the native WRF vertical dimension.
    new_dim : str, default "levels"
        Name of the new vertical dimension for the interpolated fields.
    mask_outside : bool, default True
        If True, sets to NaN values outside the valid range between local
        minimum and maximum of the native coordinate (avoids extrapolation).
    persist : bool, default False
        If True, calls ``.persist()`` on output arrays (useful when working
        with Dask-backed datasets).
    nan_opt : {"both", "left", "right", "none"}, default "both"
        - "both": no extrapolation (NaN on both sides)
        - "left": NaN on the left, extrapolate on the right
        - "right": extrapolate on the left, NaN on the right
        - "none": extrapolate on both sides

    Returns
    -------
    xr.Dataset
        Dataset containing all requested variables interpolated to the new
        vertical coordinate ``new_dim``, with propagated ``lat``, ``lon`` and
        ``time`` coordinates and CF-compliant metadata.
    """

    if coord_kind == "pressure":
        coord = pressure(ds.P,ds.PB,units='hPa')
        coord_units = "hPa"
    elif coord_kind == "height":
        coord = geop_height(ds.PH,ds.PHB)
        coord_units = "m.a.s.l"
    else:
        raise ValueError("coord_kind debe ser 'pressure' o 'height'.")
        
    if lvls is None:
        if coord_kind == "pressure":
            lvls = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 200] 
        if coord_kind == "height":
            lvls = [0, 50, 100, 250, 500, 750, 1000, 1500, 2000, 3000, 5000]
            
    lvls = np.asarray(lvls, dtype=float)

    outs = []
    for v in varis:
        if v not in ds:
            raise KeyError(f"La variable '{v}' no existe en el Dataset.")
        da = ds[v]
        if vert_dim not in da.dims:
            raise ValueError(f"La variable '{v}' no contiene la dimensión '{vert_dim}'.")

        da_i = vertical_interp(
            da=da,
            coord=coord,
            new_levels=lvls,
            dim=vert_dim,
            new_dim=new_dim,
            keep_attrs=True,
            nan_opt=nan_opt,
        )

        if mask_outside:
            top = coord.min(dim=vert_dim)
            bot = coord.max(dim=vert_dim)
            if coord_kind == "pressure":
                valid = (da_i[new_dim] >= top) & (da_i[new_dim] <= bot)
            else:
                z_bot = coord.min(dim=vert_dim); z_top = coord.max(dim=vert_dim)
                valid = (da_i[new_dim] >= z_bot) & (da_i[new_dim] <= z_top)
            da_i = da_i.where(valid)

        da_i.name = v
        da_i.attrs.update(ds[v].attrs)
        da_i.attrs["interp_coord"] = coord_kind
        da_i.attrs["levels_units"] = coord_units
        da_i.attrs["long_name"] = ds[v].attrs.get("long_name", v) + f" (interpolado en {coord_kind})"

        if persist:
            da_i = da_i.persist()
        outs.append(da_i.to_dataset())

    ds_out = xr.merge(outs).assign_coords({new_dim: lvls})
    if "lat" in ds: ds_out = ds_out.assign_coords(lat=ds["lat"])
    if "lon" in ds: ds_out = ds_out.assign_coords(lon=ds["lon"])
    if "time" in ds:
        ds_out = ds_out.assign_coords(time=ds["time"])
        ds_out.encoding["unlimited_dims"] = ("time",)
    if "lat" in ds_out:
        ds_out["lat"].attrs = {"units":"degrees_north","axis":"Y","long_name":"Latitude","standard_name":"latitude"}
    if "lon" in ds_out:
        ds_out["lon"].attrs = {"units":"degrees_east","axis":"X","long_name":"Longitude","standard_name":"longitude"}
    return ds_out