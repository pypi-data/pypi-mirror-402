from __future__ import annotations

from typing import Callable

import pandas as pd
import xarray as xr

DEGREE_DAY_BASE_C = 18.0


def _require_datetime_index(data: xr.DataArray, dim: str = "time") -> pd.DatetimeIndex:
    """Validate that a data array uses a DatetimeIndex for its time dimension.

    Parameters:
        data: DataArray expected to be indexed by datetime.
        dim: Name of the time dimension to validate.

    Returns:
        The DatetimeIndex for the time dimension.

    Raises:
        ValueError: If the data array does not have a time dimension or if the
            coordinate is not a DatetimeIndex.
    """
    if dim not in data.dims:
        raise ValueError("data array must have a 'time' dimension")
    index = data.indexes.get(dim)
    if not isinstance(index, pd.DatetimeIndex):
        raise ValueError("data array 'time' dimension must be a DatetimeIndex")
    return index


def convert_m_to_mm(data: xr.DataArray) -> xr.DataArray:
    """Convert a length data array from meters to millimeters.

    Parameters:
        data: DataArray containing values in meters. If the data array has a ``units``
            attribute, it must be ``"m"``.

    Returns:
        The converted data array in millimeters with ``units`` set to ``"mm"``.

    Raises:
        ValueError: If a data array has a ``units`` attribute that is not ``"m"``.
    """
    units = data.attrs.get("units")
    if units not in (None, "m"):
        raise ValueError("data array units must be 'm' to convert to 'mm'")
    converted = data * 1000.0
    converted.attrs = dict(data.attrs)
    converted.attrs["units"] = "mm"
    return converted


def convert_kelvin_to_celsius(data: xr.DataArray) -> xr.DataArray:
    """Convert a temperature data array from Kelvin to Celsius.

    Parameters:
        data: DataArray containing values in Kelvin. If the data array has a ``units``
            attribute, it must be ``"K"``.

    Returns:
        The converted data array in Celsius with ``units`` set to ``"C"``.

    Raises:
        ValueError: If a data array has a ``units`` attribute that is not ``"K"``.
    """
    units = data.attrs.get("units")
    if units not in (None, "K"):
        raise ValueError("data array units must be 'K' to convert to 'C'")
    converted = data - 273.15
    converted.attrs = dict(data.attrs)
    converted.attrs["units"] = "C"
    return converted


def cumulative_to_increment(data: xr.DataArray) -> xr.DataArray:
    """Convert a cumulative data array to daily increments.

    Parameters:
        data: DataArray containing cumulative totals with a time dimension named
            ``time``.

    Returns:
        A daily data array of increments computed from the last value each day. If a
        daily difference is negative (reset), the daily last value is used instead.

    Raises:
        ValueError: If a data array is not indexed by datetime.
    """
    _require_datetime_index(data)
    daily_last = data.resample(time="1D").last()
    daily_diff = daily_last - daily_last.shift(time=1)
    mask = (daily_diff >= 0) | daily_diff.isnull()
    daily_diff = daily_diff.where(mask, daily_last)
    daily_diff.attrs = dict(data.attrs)
    return daily_diff


def daily_average(data: xr.DataArray) -> xr.DataArray:
    """Resample a data array to daily mean values.

    Parameters:
        data: DataArray indexed by datetime along ``time``.

    Returns:
        Daily mean data array with one value per day.

    Raises:
        ValueError: If a data array is not indexed by datetime.
    """
    _require_datetime_index(data)
    return data.resample(time="1D").mean()


def daily_sum(data: xr.DataArray) -> xr.DataArray:
    """Resample a data array to daily sum values.

    Parameters:
        data: DataArray indexed by datetime along ``time``.

    Returns:
        Daily sum data array with one value per day.

    Raises:
        ValueError: If a data array is not indexed by datetime.
    """
    _require_datetime_index(data)
    return data.resample(time="1D").sum()


def daily_max(data: xr.DataArray) -> xr.DataArray:
    """Resample a data array to daily maximum values.

    Parameters:
        data: DataArray indexed by datetime along ``time``.

    Returns:
        Daily maximum data array with one value per day.

    Raises:
        ValueError: If a data array is not indexed by datetime.
    """
    _require_datetime_index(data)
    return data.resample(time="1D").max()


def daily_min(data: xr.DataArray) -> xr.DataArray:
    """Resample a data array to daily minimum values.

    Parameters:
        data: DataArray indexed by datetime along ``time``.

    Returns:
        Daily minimum data array with one value per day.

    Raises:
        ValueError: If a data array is not indexed by datetime.
    """
    _require_datetime_index(data)
    return data.resample(time="1D").min()


def hdd(data: xr.DataArray) -> xr.DataArray:
    """Compute heating degree days using a base of 18 C.

    Parameters:
        data: Daily average temperature data array in Celsius.

    Returns:
        DataArray of heating degree days where values below 18 C contribute positively.
    """
    return (DEGREE_DAY_BASE_C - data).clip(min=0)


def cdd(data: xr.DataArray) -> xr.DataArray:
    """Compute cooling degree days using a base of 18 C.

    Parameters:
        data: Daily average temperature data array in Celsius.

    Returns:
        DataArray of cooling degree days where values above 18 C contribute positively.
    """
    return (data - DEGREE_DAY_BASE_C).clip(min=0)


def sum_value(data: xr.DataArray) -> float:
    """Sum a data array and return a scalar.

    Parameters:
        data: DataArray of numeric values.

    Returns:
        Sum of all values as a float.
    """
    return float(data.sum().item())


def avg(data: xr.DataArray) -> float:
    """Average a data array and return a scalar.

    Parameters:
        data: DataArray of numeric values.

    Returns:
        Mean of the data array as a float.
    """
    return float(data.mean().item())


def max_value(data: xr.DataArray) -> float:
    """Maximum value of a data array as a scalar.

    Parameters:
        data: DataArray of numeric values.

    Returns:
        Maximum value as a float.
    """
    return float(data.max().item())


def index_of_max_value(data: xr.DataArray) -> int:
    """Index of the maximum value in a 1-dimensional data array.

    Parameters:
        data: DataArray of numeric values.

    Returns:
        Integer index of the first maximum value.

    Raises:
        ValueError: If the data array is empty or not 1-dimensional.
    """
    if data.size == 0:
        raise ValueError("data array must not be empty")
    if data.ndim != 1:
        raise ValueError("data array must be 1-dimensional")
    return int(data.argmax(dim=data.dims[0]).item())


def min_value(data: xr.DataArray) -> float:
    """Minimum value of a data array as a scalar.

    Parameters:
        data: DataArray of numeric values.

    Returns:
        Minimum value as a float.
    """
    return float(data.min().item())


def date_max(data: xr.DataArray) -> pd.Timestamp:
    """Return the timestamp of the maximum value in a data array.

    Parameters:
        data: DataArray of numeric values indexed by a ``time`` coordinate.

    Returns:
        Timestamp corresponding to the maximum value.

    Raises:
        ValueError: If the data array is empty or not indexed by datetime.
    """
    _require_datetime_index(data)
    if data.size == 0:
        raise ValueError("data array must not be empty")
    if data.ndim != 1:
        raise ValueError("data array must be 1-dimensional")
    return pd.Timestamp(data.idxmax("time").item())


def date_first(data: xr.DataArray, threshold: float) -> pd.Timestamp:
    """Return the timestamp of the first value above a threshold.

    Parameters:
        data: DataArray of numeric values indexed by a ``time`` coordinate.
        threshold: Threshold to exceed.

    Returns:
        Timestamp of the first value greater than the threshold. If no values
        exceed the threshold, returns ``pd.Timestamp(0)``.

    Raises:
        ValueError: If the data array is not 1-dimensional or not indexed by
            datetime.
    """
    _require_datetime_index(data)
    if data.ndim != 1:
        raise ValueError("data array must be 1-dimensional")
    matches = data.where(data > threshold, drop=True)
    if matches.size == 0:
        return pd.Timestamp(0)
    return pd.Timestamp(matches["time"].values[0])


def runlen_lt(data: xr.DataArray, threshold: float) -> int:
    """Length of the longest run where values are below a threshold.

    Parameters:
        data: DataArray of numeric values.
        threshold: Threshold that values must stay below.

    Returns:
        The length of the longest consecutive run below the threshold.
    """
    mask = (data < threshold).fillna(False).to_numpy()
    max_run = 0
    current = 0
    for value in mask:
        if value:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return int(max_run)


def runlen_gt(data: xr.DataArray, threshold: float) -> int:
    """Length of the longest run where values are above a threshold.

    Parameters:
        data: DataArray of numeric values.
        threshold: Threshold that values must exceed.

    Returns:
        The length of the longest consecutive run at or above the threshold.
    """
    mask = (data > threshold).fillna(False).to_numpy()
    max_run = 0
    current = 0
    for value in mask:
        if value:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return int(max_run)


def abs_scalar(value: float) -> float:
    """Absolute value of a scalar.

    Parameters:
        value: Numeric scalar.

    Returns:
        Absolute value as a float.
    """
    return float(abs(value))


def subtract_v(value: float, threshold: float) -> float:
    """Subtract a fixed threshold from a scalar.

    Parameters:
        value: Numeric scalar.
        threshold: Threshold to subtract.

    Returns:
        The difference ``value - threshold`` as a float.
    """
    return float(value - threshold)


TRANSFORM_REGISTRY: dict[str, Callable[..., object]] = {
    "CONVERT_M_TO_MM": convert_m_to_mm,
    "CONVERT_KELVIN_TO_CELSIUS": convert_kelvin_to_celsius,
    "CUMULATIVE_TO_INCREMENT": cumulative_to_increment,
    "DAILY_AVERAGE": daily_average,
    "DAILY_SUM": daily_sum,
    "DAILY_MAX": daily_max,
    "DAILY_MIN": daily_min,
    "HDD": hdd,
    "CDD": cdd,
    "SUM": sum_value,
    "AVG": avg,
    "MAX": max_value,
    "INDEX_OF_MAX_VALUE": index_of_max_value,
    "MIN": min_value,
    "DATE_MAX": date_max,
    "DATE_FIRST": date_first,
    "RUNLEN_LT": runlen_lt,
    "RUNLEN_GT": runlen_gt,
    "ABS": abs_scalar,
    "SUBTRACT_V": subtract_v,
}
