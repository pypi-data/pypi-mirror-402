import xarray as xr
import numpy as np
import pandas as pd
import datetime

from ...core.io import get_metadata_vars
from .croco_coords import _new_croco_coords

def read_croco(file_paths: list[str], 
               drop_vars: list[str],
               destag: bool = True, 
               parallel: bool = True,
               engine: str = 'netcdf4',
               save_path: str | None = None) -> xr.Dataset:
    """
    Reads and processes multiple CROCO NetCDF output files as a merged dataset.

    Applies optional destaggering, coordinate standardization, and conversion of model time.

    Parameters
    ----------
    file_paths : list[str]
        List of paths to CROCO NetCDF files (e.g., 'croco_avg_*.nc').

    drop_vars : list[str]
        List of variable names to drop during loading.

    destag : bool, default=True
        Whether to perform destaggering and coordinate re-alignment.

    save_path : str or None, default=None
        Optional path to save the final dataset as NetCDF.

    Returns
    -------
    xr.Dataset
        Combined and standardized CROCO dataset.
    """
    if not file_paths:
        raise ValueError("No input files provided.")

    metadata = get_metadata_vars(file_paths[0], model='CROCO', print_all=False)
    
    vert_vars = ['h','hc','zeta','Vtransform','sc_r','Cs_rho','Cs_w','Cs_r']

    for elemento in vert_vars:
        if elemento in drop_vars:
            drop_vars.remove(elemento)

    with xr.open_dataset(file_paths[0], engine='netcdf4') as ds_sample:
        lats = ds_sample.lat_rho.isel(xi_rho=0).values
        lons = ds_sample.lon_rho.isel(eta_rho=0).values

        lats_v = ds_sample.lat_v[:, 0].values if not destag and 'lat_v' in ds_sample else None
        lons_u = ds_sample.lon_u[0, :].values if not destag and 'lon_u' in ds_sample else None

    ds = xr.open_mfdataset(file_paths, 
                           combine='nested', concat_dim='time', parallel=parallel, 
                           engine=engine, 
                           drop_variables=drop_vars,
                           data_vars="minimal", coords="minimal", 
                           compat="override", join="override")

    base_time = datetime.datetime(1900, 1, 1)
    time_values = [base_time + datetime.timedelta(seconds=int(s)) for s in ds.time.values]
    ds['time'] = pd.to_datetime(time_values)

    _, unique_indices = np.unique(ds['time'], return_index=True)
    ds = ds.isel(time=unique_indices)

    if destag:
        ds_final = _new_croco_coords(ds, metadata, lats, lons)
    else:
        ds_final = _new_croco_coords(ds, metadata, lats, lons, destag=False, lats_v=lats_v, lons_u=lons_u)

    ds_final.encoding['unlimited_dims'] = ('time',)

    if save_path:
        ds_final.to_netcdf(save_path)

    return ds_final
