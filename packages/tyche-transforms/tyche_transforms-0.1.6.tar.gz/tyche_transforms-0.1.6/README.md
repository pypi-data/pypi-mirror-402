# Tyche Transforms

This package provides the transformation functions defined in `MARKETS_INFO.md` for Tyche market data pipelines,
operating on xarray DataArray inputs.
The intent is to keep the same implementations between local development and the Chainlink adapter.

## Install
```bash
uv pip install tyche-transforms
```

For development:
```bash
uv pip install -e ".[test]"
```

## Usage
```python
import pandas as pd
import xarray as xr
from tyche_transforms.transforms import daily_average, hdd, runlen_lt

times = pd.date_range("2024-01-01", periods=3)
data = xr.DataArray([15.0, 10.0, 8.0], dims="time", coords={"time": times})
print(daily_average(data))
print(hdd(data))
print(runlen_lt(data, threshold=9.0))
```

## GitHub Actions
This repo includes a workflow that runs tests on every push/PR and publishes to PyPI when you push a tag
matching `v*` (for example `v0.2.0`). To enable publishing:

1) Add a repository secret named `PYPI_API_TOKEN` containing your PyPI token.
2) Push a version tag:
```bash
git tag v0.2.0
git push origin v0.2.0
```

## Transformation Functions

**DataArray -> DataArray**
- `CONVERT_M_TO_MM` (0 args): convert meters to millimeters.
- `CONVERT_KELVIN_TO_CELSIUS` (0 args): convert Kelvin to Celsius.
- `CUMULATIVE_TO_INCREMENT` (0 args): convert cumulative totals to daily increments.
- `DAILY_AVERAGE` (0 args): resample to daily mean values.
- `DAILY_SUM` (0 args): resample to daily sum values.
- `DAILY_MAX` (0 args): resample to daily maximum values.
- `DAILY_MIN` (0 args): resample to daily minimum values.
- `HDD` (0 args): daily temperature -> HDD series (base 18 C).
- `CDD` (0 args): daily temperature -> CDD series (base 18 C).

**DataArray -> Scalar**
- `SUM` (0 args): sum over window -> scalar.
- `AVG` (0 args): average over window -> scalar.
- `MAX` (0 args): max over window -> scalar.
- `INDEX_OF_MAX_VALUE` (0 args): index of the max value -> scalar.
- `MIN` (0 args): min over window -> scalar.
- `DATE_MAX` (0 args): timestamp of the max value -> scalar (timestamp).
- `DATE_FIRST:threshold` (1 arg): timestamp of first value > threshold, or epoch `pd.Timestamp(0)` if none -> scalar (timestamp).
- `RUNLEN_LT:threshold` (1 arg): longest run length where value < threshold -> scalar.
- `RUNLEN_GT:threshold` (1 arg): longest run length where value > threshold -> scalar.

**Scalar -> Scalar**
- `ABS` (0 args): absolute value of a scalar -> scalar.
- `SUBTRACT_V:threshold` (1 arg): subtract a scalar to the given threshold -> scalar.
