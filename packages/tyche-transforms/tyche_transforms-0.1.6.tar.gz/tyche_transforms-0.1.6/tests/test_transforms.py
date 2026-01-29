import numpy as np
import pandas as pd
import pytest
import xarray as xr

from tyche_transforms.transforms import (
    abs_scalar,
    avg,
    cdd,
    convert_m_to_mm,
    convert_kelvin_to_celsius,
    cumulative_to_increment,
    daily_average,
    daily_max,
    daily_min,
    daily_sum,
    date_first,
    date_max,
    hdd,
    index_of_max_value,
    max_value,
    min_value,
    runlen_gt,
    runlen_lt,
    subtract_v,
    sum_value,
)


def test_convert_m_to_mm_series():
    data = xr.DataArray([0.0, 0.001])
    data.attrs["units"] = "m"

    result = convert_m_to_mm(data)

    np.testing.assert_allclose(result.values, [0.0, 1.0])
    assert result.attrs["units"] == "mm"


def test_convert_m_to_mm_rejects_units():
    data = xr.DataArray([1.0])
    data.attrs["units"] = "mm"

    with pytest.raises(ValueError, match="units"):
        convert_m_to_mm(data)


def test_convert_kelvin_to_celsius_series():
    data = xr.DataArray([0.0, 273.15, 300.0])
    data.attrs["units"] = "K"

    result = convert_kelvin_to_celsius(data)

    np.testing.assert_allclose(result.values, [-273.15, 0.0, 26.85])
    assert result.attrs["units"] == "C"


def test_convert_kelvin_to_celsius_rejects_units():
    data = xr.DataArray([273.15])
    data.attrs["units"] = "C"

    with pytest.raises(ValueError, match="units"):
        convert_kelvin_to_celsius(data)


def test_cumulative_to_increment_daily_with_reset():
    times = pd.date_range("2024-01-01", periods=30, freq="h")
    values = np.concatenate(
        [
            np.linspace(0.0, 5.0, 24),
            np.linspace(0.2, 1.2, 6),
        ]
    )
    data = xr.DataArray(values, dims="time", coords={"time": times})

    result = cumulative_to_increment(data)

    non_nan = result.values[~np.isnan(result.values)]
    assert len(non_nan) == 1
    assert non_nan[0] == pytest.approx(1.2)


def test_cumulative_to_increment_requires_datetime_index():
    data = xr.DataArray([1.0, 2.0, 3.0], dims="time", coords={"time": [1, 2, 3]})

    with pytest.raises(ValueError, match="DatetimeIndex"):
        cumulative_to_increment(data)


def test_daily_average_sum_max():
    times = pd.date_range("2024-01-01", periods=24, freq="h")
    data = xr.DataArray(np.arange(24), dims="time", coords={"time": times})

    mean_result = daily_average(data)
    sum_result = daily_sum(data)
    max_result = daily_max(data)
    min_result = daily_min(data)

    assert mean_result.values[0] == pytest.approx(11.5)
    assert sum_result.values[0] == pytest.approx(np.sum(np.arange(24)))
    assert max_result.values[0] == 23
    assert min_result.values[0] == 0


def test_hdd_cdd():
    data = xr.DataArray([10.0, 18.0, 25.0])

    hdd_result = hdd(data)
    cdd_result = cdd(data)

    np.testing.assert_allclose(hdd_result.values, [8.0, 0.0, 0.0])
    np.testing.assert_allclose(cdd_result.values, [0.0, 0.0, 7.0])


def test_scalar_aggregations():
    data = xr.DataArray([1.0, 2.0, 3.0])

    assert sum_value(data) == 6.0
    assert avg(data) == 2.0
    assert max_value(data) == 3.0
    assert min_value(data) == 1.0
    assert index_of_max_value(data) == 2


def test_index_of_max_value_picks_first_max():
    data = xr.DataArray([1.0, 4.0, 4.0, 2.0])

    assert index_of_max_value(data) == 1


def test_index_of_max_value_requires_1d_nonempty():
    with pytest.raises(ValueError, match="empty"):
        index_of_max_value(xr.DataArray([]))

    with pytest.raises(ValueError, match="1-dimensional"):
        index_of_max_value(xr.DataArray([[1.0, 2.0], [3.0, 4.0]]))


def test_date_max():
    times = pd.date_range("2024-01-01", periods=3, freq="D")
    data = xr.DataArray([1.0, 5.0, 5.0], dims="time", coords={"time": times})

    assert date_max(data) == times[1]


def test_date_first():
    times = pd.date_range("2024-01-01", periods=3, freq="D")
    data = xr.DataArray([1.0, 5.0, 7.0], dims="time", coords={"time": times})

    assert date_first(data, threshold=4.0) == times[1]


def test_date_first_returns_epoch_when_missing():
    times = pd.date_range("2024-01-01", periods=2, freq="D")
    data = xr.DataArray([1.0, 2.0], dims="time", coords={"time": times})

    assert date_first(data, threshold=10.0) == pd.Timestamp(0)


def test_runlen_lt():
    data = xr.DataArray([0.0, 0.0, 1.0, 0.5, 0.4, 2.0])

    assert runlen_lt(data, threshold=1.0) == 2


def test_runlen_gt():
    data = xr.DataArray([0.0, 2.1, 2.2, 2.0, 2.3, 1.9])

    assert runlen_gt(data, threshold=2.0) == 2


def test_abs_subtracts():
    assert abs_scalar(-5.0) == 5.0
    assert subtract_v(10.0, 3.5) == 6.5
