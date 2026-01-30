import numpy as np
import xarray as xr
from typing import Iterable, Optional


def _interp1d_core(
    y: np.ndarray,
    x: np.ndarray,
    x_new: np.ndarray,
    nan_opt:str = 'both',
) -> np.ndarray:
    """
    1D core interpolation routine using np.interp.

    - Filters out non-finite pairs (x, y).
    - Sorts x in ascending order.
    - Returns NaN for extrapolation outside the range of x.

    Parameters
    ----------
    y : np.ndarray
        Values to interpolate.
    x : np.ndarray
        Coordinates corresponding to `y`.
    x_new : np.ndarray
        New coordinate values where interpolation is desired.
    nan_opt : {"both", "left", "right", "none"}, default "both"
        - "both": no extrapolation (NaN on both sides)
        - "left": NaN on the left, extrapolate on the right
        - "right": extrapolate on the left, NaN on the right
        - "none": extrapolate on both sides


    Returns
    -------
    np.ndarray
        Interpolated values of y at `x_new`. Shape matches `x_new`.
    """
    m = np.isfinite(x) & np.isfinite(y)
    x = x[m]
    y = y[m]
    if x.size < 2:
        return np.full(x_new.shape, np.nan, dtype=np.result_type(y, np.float32))

    order = np.argsort(x)
    x = np.asarray(x[order], dtype=np.float64)
    y = np.asarray(y[order], dtype=np.float64)
    x_new = np.asarray(x_new, dtype=np.float64)

    if nan_opt == 'both':
        return np.interp(x_new, x, y, left=np.nan, right=np.nan)
    elif nan_opt == 'left':
        return np.interp(x_new, x, y, left=np.nan)
    elif nan_opt == 'right':
        return np.interp(x_new, x, y, right=np.nan)
    elif nan_opt == 'none':
        return np.interp(x_new, x, y)
    else:
        raise ValueError(
            f"Invalid int_opt='{nan_opt}'. "
            "Valid options are: 'both', 'left', 'right', 'none'."
        )    

def _apply_interp(
    da: xr.DataArray,
    coord: xr.DataArray,
    target_levels: Iterable[float] | np.ndarray | xr.DataArray,
    dim: str,
    new_dim: str,
    *,
    keep_attrs: bool = True,
    allow_rechunk: bool = False,
    nan_opt: str = "both",
) -> xr.DataArray:
    """
    Apply `_interp1d_core` along a given dimension of a DataArray.

    Parameters
    ----------
    da : xr.DataArray
        Variable to interpolate.
    coord : xr.DataArray
        Coordinate array of the same length as `da[dim]`.
    target_levels : array-like
        Target levels along the new dimension.
    dim : str
        Input dimension to be collapsed (interpolated).
    new_dim : str
        Name of the output dimension (target levels).
    keep_attrs : bool, default=True
        If True, preserve attributes and name of the input DataArray.
    allow_rechunk : bool, default=False
        If True, allows internal rechunking in `apply_ufunc`
          for Dask arrays.
    nan_opt : {"both", "left", "right", "none"}, default "both"
        Controls extrapolation behavior in `_interp1d_core`:
        - "both": no extrapolation (NaN on both sides)
        - "left": NaN on the left, extrapolate on the right
        - "right": extrapolate on the left, NaN on the right
        - "none": extrapolate on both sides

    Returns
    -------
    xr.DataArray
        Interpolated DataArray with dimension `new_dim`.
    """
    if dim not in da.dims:
        raise ValueError(
            f"Dimension '{dim}' not found in DataArray: {list(da.dims)}"
        )
    if dim not in coord.dims:
        raise ValueError(
            f"Dimension '{dim}' not found in coord: {list(coord.dims)}"
        )
    if da.sizes[dim] != coord.sizes[dim]:
        raise ValueError(
            f"Incompatible sizes along '{dim}': "
            f"da={da.sizes[dim]} vs coord={coord.sizes[dim]}"
        )


    target_levels = xr.DataArray(np.asarray(target_levels), dims=(new_dim,))

    _name = da.name
    _attrs = da.attrs.copy() if keep_attrs else {}

    gufunc_kwargs = {"allow_rechunk": True} if allow_rechunk else None

    out = xr.apply_ufunc(
        _interp1d_core,
        da,
        coord,
        target_levels,
        input_core_dims=[[dim], [dim], [new_dim]],
        output_core_dims=[[new_dim]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[np.result_type(da.dtype, np.float64)],
        dask_gufunc_kwargs=gufunc_kwargs,
        kwargs={"nan_opt": nan_opt},
    ).assign_coords({new_dim: target_levels})

    if keep_attrs:
        out = out.assign_attrs(_attrs)
        out.name = _name

    return out

def vertical_interp(
    da: xr.DataArray,
    coord: xr.DataArray,
    new_levels: Iterable[float] | np.ndarray | xr.DataArray,
    dim: str,
    new_dim: Optional[str] = None,
    *,
    keep_attrs: bool = True,
    allow_rechunk: bool = False,
    nan_opt: str = 'both',
) -> xr.DataArray:
    """
    Generic 1D interpolation along a given dimension.

    Notes
    -----
    - Values outside the range of `coord` return NaN (no extrapolation).
    - When working with Dask, if you get the error:
      "dimension ... consists of multiple chunks, but is also a 
      core dimension",
      use:
        `da = da.chunk({dim: -1}); coord = coord.chunk({dim: -1})`
      or pass `allow_rechunk=True`.

    Parameters
    ----------
    da : xr.DataArray
        Variable to interpolate.
    coord : xr.DataArray
        Coordinate array (must share dimension `dim` with `da`).
    new_levels : array-like
        Target levels for interpolation.
    dim : str
        Dimension of `da` along which to interpolate.
    new_dim : str, optional
        Name of the new dimension. If None, `dim` is reused (overwritten).
    keep_attrs : bool, default=True
        If True, preserve attributes and name of the input DataArray.
    allow_rechunk : bool, default=False
        If True, allows internal rechunking in `apply_ufunc` for
        Dask arrays.
    nan_opt : {"both", "left", "right", "none"}, default "both"
        Extrapolation behavior passed to `_interp1d_core`.

    Returns
    -------
    xr.DataArray
        Interpolated DataArray with dimension `new_dim`.

    """
    new_dim = new_dim or dim
    return _apply_interp(
        da=da,
        coord=coord,
        target_levels=new_levels,
        dim=dim,
        new_dim=new_dim,
        keep_attrs=keep_attrs,
        allow_rechunk=allow_rechunk,
        nan_opt=nan_opt,
    )



