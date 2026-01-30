import xarray as xr
from typing import Optional

def get_metadata_vars(
    dataset: str | xr.Dataset,
    model: str = "WRF",
    print_all: bool = False,
    engine: Optional[str] = "netcdf4"
) -> dict[str, list]:
    """
    Extracts metadata for each variable in a NetCDF dataset produced by
    the WRF or CROCO models.

    Parameters
    ----------
    dataset : str | xr.Dataset
        Path to a NetCDF file or an already opened xarray Dataset.

    model : {'WRF', 'CROCO'}, default='WRF'
        The model that produced the dataset. Accepts 'WRF' or 'CROCO'.

    print_all : bool, default=False
        If True, prints the metadata for each variable.
    
    engine : str or None, default='netcdf4'

    Returns
    -------
    dict[str, list]
        A dictionary where each key is a variable name and the value is 
        a list containing:
        
        For WRF:
            - dimensions (tuple of str)
            - units (str or None)
            - stagger (str or None)
            - description (str or None)
        
        For CROCO:
            - dimensions (tuple of str)
            - units (str or None)
            - long_name (str or None)
            - standard_name (str or None)
    """

    model = model.upper()

    if model not in {'WRF', 'CROCO'}:
        raise ValueError(f"Unrecognized '{model}'. Choose 'WRF' or 'CROCO'.")
    
    if isinstance(dataset, str):
        da = xr.open_dataset(dataset, engine=engine, 
                             mask_and_scale=False, decode_times=False)
        close_after = True
    else:
        da = dataset
        close_after = False

    metadata = {}
    try:
        for var in da:
            metadata.setdefault(var, [])
            dims = da[var].dims
            units = da[var].attrs.get('units', None)

            if model == 'WRF':
                stagger = da[var].attrs.get('stagger', None)
                description = da[var].attrs.get('description', None)
                metadata[var] = [dims, description, stagger, units]
                if print_all:
                    print(
                        f"{var}:\n Description --> {description}, "
                        f"Units: {units}, "
                        f"Dims: {dims}, "
                        f"Stagger: {stagger}, "
                    )

            elif model == 'CROCO':
                long_name = da[var].attrs.get('long_name', None)
                standard_name = da[var].attrs.get('standard_name', None)
                metadata[var] = [dims, long_name, units, standard_name]
                if print_all:
                    print(
                        f"{var}:\n Long name --> {long_name}, "
                        f"Units: {units}, "
                        f"Dims: {dims}, "
                        f"Standard name: {standard_name}, "
                    )
    finally:
        if close_after:
            da.close()
    return metadata

def drop_vars(
    file0: str | xr.Dataset,
    sel_vars: list[str],
    model: str = "WRF",
    engine: Optional[str] = "netcdf4"
) -> list[str]:
    """
    Identifies variables in a NetCDF dataset that are not included 
    in the user-specified selection `sel_vars`.

    Parameters
    ----------
    file0 : str | xr.Dataset
        Path to the NetCDF output file or an xarray.Dataset.

    sel_vars : list[str]
        List of variable names the user wants to keep.

    model : {'WRF', 'CROCO'}, default='WRF'
        Model that generated the dataset.

    engine : str or None, default='netcdf4'

    Returns
    -------
    list[str]
        List of variable names that are present in the dataset but not
        included in `sel_vars`

    """
    model_norm = model.upper()
    if model_norm not in {"WRF", "CROCO"}:
        raise ValueError(
            f"Unrecognized model '{model}'. Valid options: 'WRF' or 'CROCO'."
        )
    vars_not_selected = (
        set(get_metadata_vars(file0, model, engine=engine).keys()) 
        - set(sel_vars)
    )
    return list(vars_not_selected)