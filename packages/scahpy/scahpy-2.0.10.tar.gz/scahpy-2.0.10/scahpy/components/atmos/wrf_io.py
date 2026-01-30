import xarray as xr
import numpy as np
import pandas as pd
from functools import partial

from ...core.io import get_metadata_vars
from .wrf_coords import _new_wrf_coords

def _select_time(ds_input: xr.Dataset, dif_hours: int, sign: int) -> xr.Dataset:
    """
    Ensure a 'time' coordinate exists and apply a time offset.

    This function handles the common WRF cases:
    - Rename XTIME -> time and swap Time -> time when both are present.
    - Rename XTIME -> time if 'Time' dim is not present.
    - If 'time' already exists, it just applies the offset.

    Parameters
    ----------
    ds_input : xr.Dataset
        Input dataset as opened from a WRF NetCDF file.
    dif_hours : int
        Number of hours to offset the time coordinate.
    sign : int
        +1 to add hours, -1 to subtract hours.

    Returns
    -------
    xr.Dataset
        Dataset with a 'time' coordinate adjusted by the offset.
    """
    if "XTIME" in ds_input.variables and "Time" in ds_input.dims:
        ds_adjusted = ds_input.rename({"XTIME": "time"}).swap_dims({"Time": "time"})
    elif "XTIME" in ds_input.variables:
        ds_adjusted = ds_input.rename({"XTIME": "time"})
    elif "time" in ds_input:
        ds_adjusted = ds_input
    else:
        raise KeyError("Dataset must contain 'XTIME' (and 'Time') or an existing 'time' coordinate.")

    if dif_hours != 0:
        adjusted_time = pd.to_datetime(ds_adjusted["time"].values) + pd.Timedelta(
            hours=sign * dif_hours
        )
        ds_adjusted = ds_adjusted.assign_coords(time=adjusted_time)

    return ds_adjusted


def read_wrf(
    file_paths: list[str],
    drop_vars: list[str],
    dif_hours: int = 0,
    sign: int = 1,
    destag: bool = True,
    parallel: bool = True,
    engine: str = 'netcdf4',
    save_path: str | None = None,
) -> xr.Dataset:
    """
    Read WRF outputs, fix/standardize the time coordinate, (optionally) destagger
    variables, and attach 2D lat/lon coordinates.

    Parameters
    ----------
    file_paths : list of str
        Paths to WRF NetCDF files (same domain).
    drop_vars : list of str
        Variable names to drop at open time (memory-friendly).
    dif_hours : int, default 0
        Time offset (in hours) to apply to the 'time' coordinate.
    sign : {1, -1}, default 1
        Sign of the time offset (+1 add hours, -1 subtract hours).
    destag : bool, default True
        If True, destagger U, V, W, and other *_stag variables.
    save_path : str or None, default None
        If provided, writes the resulting dataset to NetCDF.

    Returns
    -------
    xr.Dataset
        Merged, time-unique WRF dataset with standardized coordinates.
    """
    if not file_paths:
        raise ValueError("No input files provided.")

    with xr.open_dataset(file_paths[0], engine="netcdf4") as ds_sample:
        metadata = get_metadata_vars(ds_sample, model="WRF")
        lats = ds_sample.XLAT[0, :, 0].values
        lons = ds_sample.XLONG[0, 0, :].values
        lats_v = ds_sample.XLAT_V[0, :, 0].values if (not destag and "XLAT_V" in ds_sample) else None
        lons_u = ds_sample.XLONG_U[0, 0, :].values if (not destag and "XLONG_U" in ds_sample) else None

    ds = xr.open_mfdataset(
        file_paths,
        combine="nested",
        concat_dim="time",
        parallel=parallel,
        engine=engine,
        data_vars="minimal",
        coords="minimal",
        compat="override",
        join="override",
        drop_variables=drop_vars,
        preprocess=partial(_select_time, dif_hours=dif_hours, sign=sign),
    )

    _, unique_indices = np.unique(ds["time"], return_index=True)
    ds = ds.isel(time=np.sort(unique_indices)).sortby("time")

    ds_final = _new_wrf_coords(
        ds,
        metadata,
        lats,
        lons,
        destag=destag,
        lats_v=lats_v,
        lons_u=lons_u,
    )

    ds_final.encoding["unlimited_dims"] = ("time",)

    if save_path:
        ds_final.to_netcdf(save_path)

    return ds_final
