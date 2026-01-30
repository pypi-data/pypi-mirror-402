import numpy as np
import pandas as pd
import xarray as xr
from typing import Literal

def aggregate_dmy(
    ds: xr.Dataset,
    tiempo: str = None,
    accum: list | None = None,
    avg: list | None = None,
    mediana: list | None = None,
) -> xr.Dataset:
    """
    Resample WRF hourly data to coarser time intervals using sum, mean, or median
    operations for selected variables.

    This function provides a flexible interface to resample a Dataset using any
    time frequency supported by xarray's `.resample()` (e.g., "D" for daily,
    "M" for monthly, "6H" for 6-hourly). Different groups of variables may be
    aggregated with different operations like: sum, mean, or median.

    Parameters
    ----------
    ds : xr.Dataset
        Input Dataset containing time-dependent variables (typically hourly WRF outputs).
    tiempo : str, optional
        Resampling frequency string accepted by `Dataset.resample()`. Examples:
        "D"  (daily), "M" (monthly), "3H" (3-hourly), "Y" (yearly).
        If None, the function will return an error message.
    accum : list of str, optional
        List of variable names to aggregate using the sum over each resample interval.
        Useful for accumulated or flux-like variables.
    avg : list of str, optional
        List of variable names to aggregate using the mean.
    mediana : list of str, optional
        List of variable names to aggregate using the median.
    
    Returns
    -------
    xr.Dataset
        Dataset containing the resampled variables merged together.
        The resulting Dataset includes only the variables specified in `accum`,
        `avg`, and `mediana`.

    Notes
    -----
    - If no variables are provided in `accum`, `avg`, or `mediana`, the function
      returns `None` with a warning message.
    - The function relies on xarray's `.resample()`, which requires the `time`
      coordinate to be properly formatted as a datetime64 index.
    - Each aggregation type is applied only to the variables specified in its
      corresponding list.

    Examples
    --------
    >>> # Daily sums of rainfall and daily means of temperature
    >>> ds_daily = dmy_var(
    ...     ds,
    ...     tiempo="D",
    ...     accum=["RAINC", "RAINNC"],
    ...     avg=["T2"]
    ... )
    
    >>> # Monthly means for several atmospheric variables
    >>> ds_month = dmy_var(ds, tiempo="M", avg=["U10", "V10", "T2"])

    """
    
    if tiempo is None:
        print("Please provide a valid resampling frequency (e.g., 'D', 'M', '3H').")
        return None

    datasets = []

    if accum:
        ds_ac = ds[accum].resample(time=tiempo).sum()
        datasets.append(ds_ac)

    if avg:
        ds_avg = ds[avg].resample(time=tiempo).mean()
        datasets.append(ds_avg)

    if mediana:
        ds_med = ds[mediana].resample(time=tiempo).median()
        datasets.append(ds_med)

    if not datasets:
        print("Please specify at least one group of variables (accum, avg, mediana).")
        return None

    try:
        ds_all = xr.merge(datasets)
    except ValueError:
        print("Invalid resampling frequency or misaligned time coordinate.")
        return None

    return ds_all

def monthly_climatology(
    data: xr.DataArray | xr.Dataset,
    *,
    calendar: Literal["standard", "noleap", "all_leap", "360_day"] | None = None,
    freq: str = "D",
) -> xr.DataArray | xr.Dataset:
    """
    Compute a 12-month climatology using groupby on calendar months.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Input object with a ``time`` dimension.
    calendar : {"standard", "noleap", "all_leap", "360_day"}, optional
        If provided, converts the time index to the specified CF calendar
        using ``xr.cftime_range``.
    freq : str, optional
        Temporal frequency (e.g., 'D' for daily, 'H' for hourly, 'MS' for monthly start).
        Used only when a CF calendar is applied. Default is 'D'.

    Returns
    -------
    xr.DataArray or xr.Dataset
        12-step climatology indexed by ``month`` (1–12), preserving variable
        attributes and metadata.
    """

    if calendar:
        data = data.copy()
        data["time"] = xr.cftime_range(
            start=str(data.time.values[0])[:19],
            periods=data.sizes["time"],
            freq=freq,
            calendar=calendar
        )[: data.sizes["time"]]

    if isinstance(data, xr.Dataset):
        ds_result = data.groupby("time.month").mean("time", skipna=True)
        for v in data.data_vars:
            if v in ds_result:
                ds_result[v].attrs.update(data[v].attrs)
                ds_result[v].attrs.setdefault("long_name", f"{v} monthly climatology")
        ds_result.attrs.update(data.attrs)
        return ds_result

    else:
        da_result = data.groupby("time.month").mean("time", skipna=True)
        varname = data.name if getattr(data, "name", None) else "var"
        da_result.name = f"{varname}_clim_monthly"
        da_result.attrs.update(data.attrs)
        da_result.attrs.setdefault("long_name", f"{varname} monthly climatology")
        return da_result


def anomalies(
    data: xr.DataArray | xr.Dataset,
    clim: xr.DataArray | xr.Dataset,
    *,
    kind: Literal["monthly", "daily"] = "monthly",
) -> xr.DataArray | xr.Dataset:
    """
    Compute anomalies relative to a provided climatology.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Original data with time dimension.
    clim : xr.DataArray or xr.Dataset
        Climatology with coord 'month' (monthly) or 'dayofyear' (daily).
    kind : {"monthly", "daily"}, default "monthly"
        Controls the grouping key used to match climatology to data.

    Returns
    -------
    xr.DataArray or xr.Dataset
        Anomalies with the same structure and units as `data`.
    """
    if kind not in {"monthly", "daily"}:
        raise ValueError("kind must be 'monthly' or 'daily'")

    group_key = "time.month" if kind == "monthly" else "time.dayofyear"
    clim_coord = "month" if kind == "monthly" else "dayofyear"
    if clim_coord not in clim.coords:
        raise KeyError(
            f"Expected climatology to have coord '{clim_coord}' for kind='{kind}'."
        )

    if isinstance(data, xr.Dataset):
        result_ds = data.groupby(group_key) - clim
        for v in data.data_vars:
            if v in result_ds:
                result_ds[v].attrs.update(data[v].attrs)
                result_ds[v].attrs.setdefault("long_name", f"{v} anomaly ({kind})")
        result_ds.attrs.update(data.attrs)
        return result_ds

    else:
        result_da = data.groupby(group_key) - clim
        varname = data.name if getattr(data, "name", None) else "var"
        result_da.name = f"{varname}_anom"
        result_da.attrs.update(data.attrs)
        result_da.attrs.setdefault("long_name", f"{varname} anomaly ({kind})")
        return result_da
    
def monthly_to_daily_climatology(
    data: xr.DataArray | xr.Dataset,
    *,
    method: Literal["linear", "harmonic"] = "harmonic",
    harmonics: int = 2,
    target_year: int | None = None,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
) -> xr.DataArray | xr.Dataset:
    """Upsample a monthly climatology to daily frequency for DataArray or Dataset.

    Supports two methods:
      1) ``method='linear'`` – time-based linear interpolation using pandas/xarray.
      2) ``method='harmonic'`` – fit a seasonal cycle with a small set of harmonics
         (annual, semiannual, etc.) via least squares using NumPy only.

    Parameters
    ----------
    data : xr.DataArray or xr.Dataset
        Monthly time series with a ``time`` coordinate. Can be multi-year.
    method : {"linear", "harmonic"}, default "harmonic"
        Interpolation method.
    harmonics : int, default 2
        Number of harmonics used by the seasonal fit (ignored if ``linear``).
    target_year : int, optional
        If provided, return a daily series for that calendar year.
    start, end : str or pandas.Timestamp, optional
        Explicit start/end dates for daily output (used when ``target_year`` is None).

    Returns
    -------
    xr.DataArray or xr.Dataset
        Daily climatology with the same structure as input and updated attrs.
    """
    if "time" not in data.dims:
        raise ValueError("Input must have a 'time' dimension.")

    if target_year is not None:
        start = pd.Timestamp(f"{target_year}-01-01")
        end = pd.Timestamp(f"{target_year}-12-31")
    else:
        start = pd.Timestamp(start) if start is not None else pd.to_datetime(data.time.values.min()).normalize()
        end = pd.Timestamp(end) if end is not None else pd.to_datetime(data.time.values.max()).normalize()
    daily_index = pd.date_range(start=start, end=end, freq="D")

    def _process_da(da: xr.DataArray) -> xr.DataArray:
        if method == "linear":
            ds_tmp = da.to_dataset(name=da.name or "var")
            ds_daily = ds_tmp.resample(time="D").asfreq()
            ds_daily = ds_daily.interpolate("time")
            out = ds_daily[da.name or "var"]
            out.name = (da.name or "var") + "_daily"
            out.attrs.update(da.attrs)
            return out

        if method == "harmonic":
            t = pd.to_datetime(da.time.values)
            year_len = t.to_series().groupby(t.year).transform(
                lambda s: (pd.Timestamp(year=s.iloc[0].year + 1, month=1, day=1)
                           - pd.Timestamp(year=s.iloc[0].year, month=1, day=1)).days
            )
            frac = (t.dayofyear - 1) / year_len.to_numpy()

            cols = [np.ones_like(frac)]
            for k in range(1, harmonics + 1):
                cols.append(np.cos(2 * np.pi * k * frac))
                cols.append(np.sin(2 * np.pi * k * frac))
            X = np.column_stack(cols)

            def _fit_eval(y: np.ndarray, X: np.ndarray, target_days: np.ndarray) -> np.ndarray:
                mask = np.isfinite(y)
                if mask.sum() < X.shape[1]:
                    a0 = np.nanmean(y)
                    return np.full(target_days.shape[0], a0, dtype=float)
                coef, *_ = np.linalg.lstsq(X[mask, :], y[mask], rcond=None)
                tt = pd.to_datetime(target_days)
                ylen = tt.to_series().groupby(tt.year).transform(
                    lambda s: (pd.Timestamp(year=s.iloc[0].year + 1, month=1, day=1)
                               - pd.Timestamp(year=s.iloc[0].year, month=1, day=1)).days
                )
                frac_d = (tt.dayofyear - 1) / ylen.to_numpy()
                cols_d = [np.ones_like(frac_d)]
                H = (X.shape[1] - 1) // 2
                for k in range(1, H + 1):
                    cols_d.append(np.cos(2 * np.pi * k * frac_d))
                    cols_d.append(np.sin(2 * np.pi * k * frac_d))
                Xd = np.column_stack(cols_d)
                return Xd @ coef

            out = xr.apply_ufunc(
                _fit_eval,
                da,
                xr.DataArray(X, dims=("time", "col")),
                xr.DataArray(daily_index.values, dims=("time_out",)),
                input_core_dims=[["time"], ["time", "col"], ["time_out"]],
                output_core_dims=[["time_out"]],
                vectorize=True,
                dask="parallelized",
                output_dtypes=[float],
            )
            out = out.rename({"time_out": "time"}).assign_coords(time=daily_index)
            out.name = (da.name or "var") + "_daily"
            out.attrs.update(da.attrs)
            return out

        raise ValueError("method must be 'linear' or 'harmonic'")

    if isinstance(data, xr.Dataset):
        results = []
        for v in data.data_vars:
            results.append(_process_da(data[v]).to_dataset(name=v))
        out_ds = xr.merge(results)
        out_ds.attrs.update(data.attrs)
        return out_ds
    else:
        return _process_da(data)
