import pandas as pd
import xarray as xr
import shapefile
from typing import Union, Optional

def extract_points(
    ds_out: xr.Dataset,
    station: str,
    lon_col: str,
    lat_col: str,
    name_col: str,
    ds_lon_name: str = "lon",
    ds_lat_name: str = "lat",
    output_format: str = "netcdf",
    save_path: Optional[str] = None,
) -> Union[xr.Dataset, pd.DataFrame]:
    """
    Extract data from a model output dataset (e.g., WRF/CROCO) at the nearest
    grid point(s) to a set of station locations provided via CSV or Shapefile.

    Parameters
    ----------
    ds_out : xr.Dataset
        Model dataset already loaded in memory.
        The dataset must contain longitude and latitude variables whose names
        are provided via `ds_lon_name` and `ds_lat_name`. These may be 1D or 2D
        variables and will be promoted to coordinates if they are not already.
    station : str
        Path to a CSV ('.csv') or ESRI Shapefile ('.shp') with station metadata.
        The CSV/Shapefile must provide, at minimum, station name, longitude,
        and latitude columns as specified by `name_col`, `lon_col`, `lat_col`.
        For Shapefiles, the function reads the first point of each geometry
        as (lon, lat).
    lon_col : str
        Column name in the stations file for longitudes (degrees East).
    lat_col : str
        Column name in the stations file for latitudes (degrees North).
    name_col : str
        Column name in the stations file for station identifiers.
    ds_lon_name : str, optional
        Variable name of longitudes in `ds_out` (e.g., 'XLONG', 'lon_rho').
        Default is 'lon'.
    ds_lat_name : str, optional
        Variable name of latitudes in `ds_out` (e.g., 'XLAT', 'lat_rho').
        Default is 'lat'.
    output_format : {'netcdf', 'dataframe'}, optional
        Output format. If 'dataframe', returns a tidy pandas.DataFrame;
        otherwise returns an xarray.Dataset. Default is 'netcdf'.
    save_path : str, optional
        If provided, the result is written to disk. Uses CSV when
        `output_format='dataframe'` and NetCDF otherwise.

    Returns
    -------
    xr.Dataset or pandas.DataFrame
        Extracted data at nearest grid point for each station.
    """

    if station.lower().endswith(".csv"):
        station_df = pd.read_csv(station)
    elif station.lower().endswith(".shp"):
        sf = shapefile.Reader(station)
        fields = [f[0] for f in sf.fields[1:]]          
        records = sf.records()
        shapes = sf.shapes()
        station_df = pd.DataFrame(records, columns=fields)

        station_df[lon_col] = [shp.points[0][0] for shp in shapes]
        station_df[lat_col] = [shp.points[0][1] for shp in shapes]
    else:
        raise ValueError("Unsupported stations file. Use '.csv' or '.shp'.")

    crd_ix = station_df.set_index(name_col).to_xarray()

    if ds_lon_name not in ds_out.variables or ds_lat_name not in ds_out.variables:
        raise KeyError(
            f"Longitude/latitude variables '{ds_lon_name}' / '{ds_lat_name}' "
            f"were not found in the dataset."
        )

    if ds_lon_name not in ds_out.coords:
        ds_out = ds_out.assign_coords({ds_lon_name: ds_out[ds_lon_name]})
    if ds_lat_name not in ds_out.coords:
        ds_out = ds_out.assign_coords({ds_lat_name: ds_out[ds_lat_name]})

    extracted = ds_out.sel(
        {ds_lon_name: crd_ix[lon_col], ds_lat_name: crd_ix[lat_col]},
        method="nearest",
    )

    if output_format.lower() == "dataframe":
        out_obj: Union[xr.Dataset, pd.DataFrame] = extracted.to_dataframe().reset_index()
    else:
        out_obj = extracted

    if save_path is not None:
        if isinstance(out_obj, pd.DataFrame):
            out_obj.to_csv(save_path, index=False)
        else:
            out_obj.to_netcdf(save_path)

    return out_obj