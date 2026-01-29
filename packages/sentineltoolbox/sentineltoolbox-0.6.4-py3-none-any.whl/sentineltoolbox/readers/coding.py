import numpy as np
import xarray as xr
from xarray.core.datatree import DataTree


def encode_cf_datetime(dt: DataTree) -> DataTree:
    """
    Recursively encode all time variables in a DataTree to CF-compliant format.

    Parameters
    ----------
    dt : DataTree
        The input DataTree with potential time variables.

    Returns
    -------
    DataTree
        A new DataTree with all time variables encoded to CF-compliant format.
    """
    changed = False

    def _encode_cf_datetime_ds(dataset: xr.Dataset, units: str = "nanoseconds since 1970-01-01 00:00:00") -> xr.Dataset:
        nonlocal changed
        dataset = dataset.copy(deep=False)

        for var in dataset.data_vars:
            data = dataset[var]
            if not _is_time_variable(data):
                continue
            if not _is_time_decoded(data):
                continue
            units = data.encoding.get("units", units)
            values, _, _ = xr.coding.times.encode_cf_datetime(data, units)
            dataset[var].data = values
            dataset[var].encoding.pop("units", None)
            dataset[var].attrs["units"] = units
            changed = True
        return dataset

    dt_encoded = dt.map_over_datasets(lambda ds: _encode_cf_datetime_ds(ds))

    if not changed:
        return dt

    return dt_encoded


def _is_time_decoded(data_array: xr.DataArray) -> bool:
    """
    Check if a DataArray contains time data that has been decoded.

    Parameters
    ----------
    data_array : xr.DataArray
        The DataArray to check.

    Returns
    -------
    bool
        True if the DataArray contains decoded time data.
    """
    # Check if dtype is datetime64 (indicates decoded time)
    if np.issubdtype(data_array.dtype, np.datetime64):
        return True
    else:
        return False


def _is_time_variable(data_array: xr.DataArray) -> bool:
    """
    Check if a DataArray contains time data that has been decoded.

    Parameters
    ----------
    data_array : xr.DataArray
        The DataArray to check.

    Returns
    -------
    bool
        True if the DataArray contains decoded time data.
    """
    # Check if dtype is datetime64 (indicates decoded time)
    if np.issubdtype(data_array.dtype, np.datetime64):
        return True

    # Check if the variable name suggests it's a time variable
    time_keywords = ["time", "timestamp", "date", "datetime", "epoch"]
    var_name_lower = str(data_array.name).lower()

    if any(keyword in var_name_lower for keyword in time_keywords):
        return True

    # Check attributes for time-related information
    attrs = data_array.attrs
    if "units" in attrs:
        units = str(attrs["units"]).lower()
        time_units = ["seconds", "minutes", "hours", "days", "microseconds", "nanoseconds"]
        if any(unit in units for unit in time_units):
            return True

    return False
