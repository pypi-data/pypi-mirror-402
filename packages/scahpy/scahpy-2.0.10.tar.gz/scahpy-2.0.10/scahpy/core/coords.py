import numpy as np
import xarray as xr

def destagger_array(da: xr.DataArray, axis: str, pad: bool = False) -> xr.DataArray:
    """
    Removes staggering along a given dimension by averaging adjacent values.
    Optionally (CROCO) expands the coordinate by one step on each side before averaging.

    Parameters
    ----------
    da : xr.DataArray
        Staggered variable to be destaggered.
    axis : str
        Name of the staggered dimension (e.g., 'xi_u', 'eta_v', 's_w').
    pad : bool, optional
        If True, expands the coordinate by one inferred step on each edge
        and fills new points with NaN (default: False).

    Returns
    -------
    xr.DataArray
        Destaggered array with the specified dimension reduced by one
        and coordinate reassigned to midpoints.
    """
    if axis not in da.dims:
        raise ValueError(f"Axis '{axis}' not found in DataArray dimensions: {da.dims}")
    if da.sizes[axis] < 2:
        raise ValueError(f"Cannot destagger '{axis}' with size < 2.")
        
    coord = da[axis].values 
    
    if pad:
        step = float(np.median(np.diff(coord)))
        new_coord = np.concatenate(([coord[0]-step], coord, [coord[-1]+step]))
        ds = da.reindex({axis: new_coord}, fill_value=np.nan)
    else:
        ds = da
        new_coord = coord
        
    mid_coord = 0.5 * (new_coord[:-1] + new_coord[1:]) 
    
    left  = ds.isel({axis: slice(0, -1)}).assign_coords({axis: mid_coord})
    right = ds.isel({axis: slice(1,  None)}).assign_coords({axis: mid_coord})

    da_unstagg = 0.5 * (left + right)
    da_unstagg.name = ds.name
    da_unstagg.attrs = ds.attrs.copy()

    return da_unstagg

