# (c) 2023 DTU Wind Energy
"""
Validation code for using the ltc module
"""

import functools
import inspect

import numpy as np
import xarray as xr

from windkit._errors import WindkitValidationError
from windkit.spatial import count_spatial_points
from windkit.wind_climate.time_series_wind_climate import validate_tswc


def ltc_validate(n_args=2):
    def _validate(func):
        """This decorator validates that the input dataset have the right
        structure"""

        @functools.wraps(func)  # Apply the wraps decorator
        def wrapper(*args, **kwargs):
            if n_args not in [1, 2]:
                raise ValueError("Only 1 or 2 args are supported for ltc validation.")
            if "self" in inspect.getcallargs(func, *args):
                args_idx = [1, 2][:n_args]
            else:
                args_idx = [0, 1][:n_args]
            for i in args_idx:
                validate_dataset_ltc(args[i])
            result = func(*args, **kwargs)
            return result

        return wrapper

    return _validate


def validate_dataset_ltc(ds_ts):
    """validates the dataset
    Raises WindkitValidationError if any error is found, otherwise
    does nothing
    """
    errors = []
    # first check for valid xarray.Dataset
    if not isinstance(ds_ts, xr.Dataset):
        errors.append(f"{len(errors) + 1}. argument must be a xarray.Dataset.")
    if errors:
        raise WindkitValidationError(
            f"Validate found {len(errors)} errors \n" + "\n".join(errors)
        )
    # check whether it is a time series wind climate
    try:
        validate_tswc(ds_ts)
    except Exception:
        errors.append(
            f"{len(errors) + 1}. argument must be a valid time series wind climate xarray.Dataset."
        )

    if errors:
        raise WindkitValidationError(
            f"Validate found {len(errors)} errors \n" + "\n".join(errors)
        )

    # check wheter it is a single point
    if count_spatial_points(ds_ts) > 1:
        errors.append(
            f"{len(errors) + 1}. windkit.ltc module only support datasets with one point, argument has >1 point."
        )

    if errors:
        raise WindkitValidationError(
            f"Validate found {len(errors)} errors \n" + "\n".join(errors)
        )


def assert_timesteps_equal(ds_ref, ds_target):
    """This function validates that the dataset has the same time coordinates,
    i.e. the same number of samples and on the same timestamps.
    """
    if (ds_ref.sizes["time"] != ds_target.sizes["time"]) or np.any(
        ds_ref.time.values != ds_target.time.values
    ):
        raise WindkitValidationError("datasets do not have the same time coordinates.")


def assert_valid_values(ds_ts):
    """This function validates that the data is valid,
    i.e. floats, ranges, dimensions."""
    errors = []
    if ds_ts.wind_speed.min() < 0:
        errors.append(f"{len(errors) + 1}. dataset has negative wind speeds.")
    if ds_ts.wind_direction.min() < 0 or ds_ts.wind_direction.max() > 360:
        errors.append(
            f"{len(errors) + 1}. dataset has wind directions outside 360 degrees range."
        )
    missing_ws_wd = ds_ts.isnull()
    missing_time = ds_ts.time.isnull().values.any()
    missing_ws = missing_ws_wd.wind_speed.values.any()
    missing_wd = missing_ws_wd.wind_direction.values.any()

    if missing_time:
        errors.append(
            f"{len(errors) + 1}. dataset has missing values for coordinate 'time'."
        )
    if missing_ws:
        errors.append(
            f"{len(errors) + 1}. dataset has missing values for data variable 'wind_speed'."
        )
    if missing_wd:
        errors.append(
            f"{len(errors) + 1}. dataset has missing values for data variable 'wind_direction'."
        )
    if errors:
        raise WindkitValidationError(
            f"Validate found {len(errors)} errors \n" + "\n".join(errors)
        )
