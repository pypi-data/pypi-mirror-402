import numpy as np
import xarray as xr
from typing import Union, Hashable, Iterable

def to_kelvin(
    temp: float | np.ndarray | xr.DataArray | xr.Dataset,
    var_names: Hashable | Iterable[Hashable] | None = None,
):
    """
    Convert temperature from Celsius to Kelvin.

    Parameters
    ----------
    temp : float | np.ndarray | xr.DataArray | xr.Dataset
        Temperature in Celsius.
    var_names : hashable or iterable of hashable, optional
        Only used when `temp` is a Dataset. Names of the data variables
        to convert. Other variables remain unchanged.

    Returns
    -------
    float | np.ndarray | xr.DataArray | xr.Dataset
        Temperature in Kelvin. For xarray objects, only the 'units'
        attribute is updated to 'K'; other attributes are preserved.
    """
    if isinstance(temp, xr.Dataset):
        if var_names is None:
            raise ValueError(
                "When passing a Dataset, you must specify 'vars=[\"var1\", ...]'."
            )

        if isinstance(var_names, (str, bytes)) or not isinstance(var_names, Iterable):
            var_names = [var_names]

        new_vars = {}
        for v in var_names:
            if v not in temp.data_vars:
                raise KeyError(f"Variable '{v}' not found in Dataset.")
            da = temp[v]
            out_da = da + 273.15
            out_da.attrs = da.attrs.copy()
            out_da.attrs["units"] = "K"
            new_vars[v] = out_da

        return temp.assign(**new_vars)

    if isinstance(temp, xr.DataArray):
        out = temp + 273.15
        out.attrs = temp.attrs.copy()
        out.attrs["units"] = "K"
        return out

    return temp + 273.15

def to_celsius(
    temp: float | np.ndarray | xr.DataArray | xr.Dataset,
    var_names: Hashable | Iterable[Hashable] | None = None,
):
    """
    Convert temperature from Kelvin to Celsius.

    Parameters
    ----------
    temp : float | np.ndarray | xr.DataArray | xr.Dataset
        Temperature in Kelvin.
    var_names : hashable or iterable of hashable, optional
        Only used when `temp` is a Dataset. Names of the data variables
        to convert. Other variables remain unchanged.

    Returns
    -------
    float | np.ndarray | xr.DataArray | xr.Dataset
        Temperature in Celsius. For xarray objects, only the 'units'
        attribute is updated to '°C'; other attributes are preserved.
    """
    if isinstance(temp, xr.Dataset):
        if var_names is None:
            raise ValueError(
                "When passing a Dataset, you must specify 'vars=[\"var1\", ...]'."
            )

        if isinstance(var_names, (str, bytes)) or not isinstance(var_names, Iterable):
            var_names = [var_names]

        new_vars = {}
        for v in var_names:
            if v not in temp.data_vars:
                raise KeyError(f"Variable '{v}' not found in Dataset.")
            da = temp[v]
            out_da = da - 273.15
            out_da.attrs = da.attrs.copy()
            out_da.attrs["units"] = "°C"
            new_vars[v] = out_da

        return temp.assign(**new_vars)

    if isinstance(temp, xr.DataArray):
        out = temp - 273.15
        out.attrs = temp.attrs.copy()
        out.attrs["units"] = "°C"
        return out

    return temp - 273.15


def to_hpa(pres):
    """
    Convert pressure from Pascals (Pa) to hectoPascals (hPa).
    
    Parameters
    ----------
    pres : float | np.ndarray | xr.DataArray
        Pressure in Pascals.

    Returns
    -------
    float | np.ndarray | xr.DataArray
        Pressure in hectoPascals, preserving attributes if input is DataArray.

    """
    result = pres / 100.0

    if isinstance(pres, xr.DataArray):
        out = result
        out.attrs = pres.attrs.copy()
        out.attrs.update({"units": "hPa", "description": "Pressure in hPa"})
        return out
    else:
        return result


def to_pa(pres):
    """
    Convert pressure from hectoPascals (hPa) to Pascals (Pa).

    Parameters
    ----------
    pres : float | np.ndarray | xr.DataArray
        Pressure in hectoPascals.

    Returns
    -------
    float | np.ndarray | xr.DataArray
        Pressure in Pascals, preserving attributes if input is DataArray.
    """
    result = pres * 100.0

    if isinstance(pres, xr.DataArray):
        out = result
        out.attrs = pres.attrs.copy()
        out.attrs.update({"units": "Pa", "description": "Pressure in Pa"})
        return out
    else:
        return result

def central_diff(da: xr.DataArray, dim: str) -> xr.DataArray:
    """
    Compute the centered finite difference along a given dimension.

    This returns the simple centered stencil (f[i+1] - f[i-1]) / 2, i.e.
    without dividing by the grid spacing. The caller can later scale by
    metric coefficients (e.g., pm = 1/Δx, pn = 1/Δy).

    Edge handling:
        The first and last points along `dim` are set to NaN because a
        centered derivative is not defined there (missing neighbors).
        Coordinates are preserved; only data values at the edges become NaN.

    Parameters
    ----------
    da : xr.DataArray
        Input array. Must contain dimension `dim`.
    dim : str
        Name of the dimension along which to compute the derivative.

    Returns
    -------
    xr.DataArray
        Centered difference with the same dimensions and coordinates as `da`,
        except that the two edge points along `dim` are NaN. Variable name and
        attributes are preserved.
    """
    if dim not in da.dims:
        raise ValueError(f"Dimension '{dim}' not present in DataArray: {list(da.dims)}")

    fwd = da.shift({dim: -1})
    bwd = da.shift({dim:  1})
    out = 0.5 * (fwd - bwd)

    out = out.where(~(fwd.isnull() | bwd.isnull()))

    out = out.transpose(*da.dims)
    out.name = getattr(da, "name", None)
    out.attrs = da.attrs.copy()
    return out


def ddx(field: xr.DataArray, metric_x: xr.DataArray | float, *, x_dim: str = "x") -> xr.DataArray:
    """
    Compute the partial derivative ∂(field)/∂x using a provided grid metric.

    Parameters
    ----------
    field : xr.DataArray
        Input variable defined on a rectilinear or curvilinear grid.
    metric_x : xr.DataArray or float
        Grid metric in the x-direction (typically 1/Δx).
        For CROCO/ROMS, this corresponds to `pm`; for WRF, to `mapfac_m / dx`.
    x_dim : str, optional
        Name of the x dimension. Default is "x".

    Returns
    -------
    xr.DataArray
        Zonal derivative scaled by the x-direction metric.
    """
    return metric_x * central_diff(field, x_dim)


def ddy(field: xr.DataArray, metric_y: xr.DataArray | float, *, y_dim: str = "y") -> xr.DataArray:
    """
    Compute the partial derivative ∂(field)/∂y using a provided grid metric.

    Parameters
    ----------
    field : xr.DataArray
        Input variable defined on a rectilinear or curvilinear grid.
    metric_y : xr.DataArray or float
        Grid metric in the y-direction (typically 1/Δy).
        For CROCO/ROMS, this corresponds to `pn`; for WRF, to `mapfac_n / dy`.
    y_dim : str, optional
        Name of the y dimension. Default is "y".

    Returns
    -------
    xr.DataArray
        Meridional derivative scaled by the y-direction metric.
    """
    return metric_y * central_diff(field, y_dim)


def rotate_to_EN(
    u: xr.DataArray,
    v: xr.DataArray,
    *,
    angle: xr.DataArray | None = None,
    cosang: xr.DataArray | None = None,
    sinang: xr.DataArray | None = None,
) -> tuple[xr.DataArray, xr.DataArray]:
    """
    Rotate horizontal velocity components from grid-relative to
    East–North coordinates.

    Parameters
    ----------
    u, v : xr.DataArray
        Zonal and meridional components on the model grid.
    angle : xr.DataArray, optional
        Grid orientation angle in radians (used in CROCO/ROMS).
    cosang, sinang : xr.DataArray, optional
        Cosine and sine of the grid angle (used in WRF).

    Returns
    -------
    (u_east, v_north) : tuple of xr.DataArray
        Velocity components rotated into true east–north coordinates.
    """
    if angle is not None:
        cosang, sinang = np.cos(angle), np.sin(angle)
    if cosang is None or sinang is None:
        raise ValueError("Either `angle` or both `cosang` and `sinang` must be provided.")
    u_east = u * cosang - v * sinang
    v_north = u * sinang + v * cosang
    u_east.attrs = u.attrs.copy(); v_north.attrs = v.attrs.copy()
    return u_east, v_north

def apply_mask(
    da: Union[xr.DataArray, xr.Dataset],
    mask: xr.DataArray,
    *,
    var_names: Hashable | Iterable[Hashable] | None = None,
    sea_is_one: bool = True,
    lakemask: xr.DataArray | None = None,
    exclude_lakes: bool = True,
) -> Union[xr.DataArray, xr.Dataset]:
    """
    Apply a land–sea mask (and optionally a lake mask) to one or multiple variables.

    This function accepts either:
      - a single ``xarray.DataArray`` (returns a masked DataArray), or
      - an ``xarray.Dataset`` (applies the mask to selected data variables and
        returns a Dataset where other variables remain unchanged).

    Masking follows the convention determined by ``sea_is_one``:
      - ``sea_is_one=True``  → mask==1 indicates ocean (ROMS/CROCO style)
      - ``sea_is_one=False`` → mask==1 indicates land  (WRF style),
        so the mask is logically inverted.

    If a lake mask is provided with ``exclude_lakes=True`` (default),
    points classified as lakes (``lakemask==1``) are also set to NaN.

    Parameters
    ----------
    da : xr.DataArray or xr.Dataset
        Input variable(s) to be masked. If a Dataset is provided, the mask
        is applied only to the variables listed in ``vars``.
    mask : xr.DataArray
        Land–sea mask. Values should be 0/1.
    var_names : hashable or iterable of hashable, optional
        Only used when ``da`` is a Dataset. Names of data variables to mask.
        Other variables are left unchanged. If None, the mask is applied to
        all data variables.
    sea_is_one : bool, optional
        Indicates whether ``1`` represents ocean (True) or land (False).
        Default is True.
    lakemask : xr.DataArray, optional
        Optional lake mask (1 = lake, 0 = not lake). If provided and
        ``exclude_lakes=True``, lake points will be masked as NaN.
    exclude_lakes : bool, optional
        Whether to mask out lake-covered grid cells when ``lakemask`` is provided.
        Default is True.

    Returns
    -------
    xr.DataArray or xr.Dataset
        A masked version of the input variable(s). For Datasets, only the
        selected variables are masked; the rest remain unchanged.
    """

    m = mask.astype(bool)

    if not sea_is_one:
        m = ~m

    if exclude_lakes and (lakemask is not None):
        m = m & (~lakemask.astype(bool))

    if isinstance(da, xr.DataArray):
        return da.where(m)

    if isinstance(da, xr.Dataset):
        if var_names is None:
            var_list: list[Hashable] = list(da.data_vars)
        else:
            if isinstance(var_names, (str, bytes)):
                var_list = [var_names]
            elif not isinstance(var_names, Iterable):
                var_list = [var_names]
            else:
                var_list = list(var_names)

        missing = [v for v in var_list if v not in da.data_vars]
        if missing:
            raise KeyError(
                f"The following variables are not present in the Dataset: {missing}"
            )

        masked_vars = {name: da[name].where(m) for name in var_list}
        return da.assign(**masked_vars)

    raise TypeError("`da` must be an xarray.DataArray or xarray.Dataset.")
