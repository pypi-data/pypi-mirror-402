# (c) 2022 DTU Wind Energy
"""Time series wind climate module

A time series wind climate is defined by dataset with a time series
``wind speed`` and ``wind direction``.

A valid time series wind climate therefore has a dimension ``time``.
Also it must have one of the valid :ref:`geospatial_structures`. This module contains
functions that operate on time series wind climates.
This includes the ability to create time series datasets from files and from
existing data.
"""

__all__ = [
    "validate_tswc",
    "is_tswc",
    "create_tswc",
    "read_tswc",
    "tswc_from_dataframe",
]

import collections
import re
import warnings

import numpy as np
import pandas as pd
import xarray as xr

from windkit.xarray_structures._validate import (
    _create_is_obj_function,
    _create_validation_wrapper_factory,
    _create_validator,
)
from windkit.xarray_structures.empty import (
    _copy_chunks,
    _define_std_arrays,
    _empty_unstack,
)
from windkit.xarray_structures.metadata import (
    _TS_ATTRS,
    _update_history,
    _update_var_attrs,
)
from windkit.spatial import to_stacked_point
from windkit.spatial._crs import set_crs
from windkit.utils import _infer_file_format
from windkit.wind import shear_extrapolate

SUPPORTED_TSWC_FILE_FORMATS_READ = ["csv", "txt", "nc"]
SUPPORTED_TSWC_FILE_FORMATS_WRITE = []

WS = "wind_speed"
WD = "wind_direction"
DIM_TIME = "time"
DATA_VAR_DICT_TS = {WS: [DIM_TIME], WD: [DIM_TIME]}
REQ_DIMS_TS = [DIM_TIME]
REQ_COORDS_TS = ["time"]

validate_tswc = _create_validator(
    variables=DATA_VAR_DICT_TS, dims=REQ_DIMS_TS, coords=REQ_COORDS_TS
)

_validate_tswc_wrapper_factory = _create_validation_wrapper_factory(validate_tswc)

is_tswc = _create_is_obj_function(validate_tswc)


def create_tswc(output_locs, date_range=None, not_empty=True, seed=9876538):
    """
    Create empty time series wind climate dataset.

    If not_empty=True, the data variables are filled with meaninful random numbers.

    Parameters
    ----------
    output_loc : xarray.Dataset
        Output geospatial information.
    time_range : pandas.DatetimeIndex or None
        time range as a pandas DateTimeIndex. If None is passed, a default range with 100
        entries is created. Defaults to None.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data. Defaults to True.
    seed : int
        Seed for the random data, defaults to 9876538.

    Returns
    -------
    ds : xarray.Dataset
        Time Series wind climate dataset either empty or filled with
        random numbers.
    """

    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs)
    if date_range is None:
        time_values = pd.date_range(
            "2001-01-01", "2010-01-01", freq="10min", inclusive="left"
        )
    elif type(date_range) is not pd.DatetimeIndex:
        raise TypeError("date_range must be of type pandas.DatetimeIndex")
    else:
        time_values = date_range

    ds = xr.Dataset(
        {
            "wind_speed": da_dict["da_3d_nosec"],
            "wind_direction": da_dict["da_3d_nosec"],
        },
        attrs=unstack_attrs,
    )

    ds["wind_speed"] = ds["wind_speed"].expand_dims({"time": time_values})
    ds["wind_direction"] = ds["wind_direction"].expand_dims({"time": time_values})

    n_pt = len(ds["point"])
    n_timesteps = len(ds["time"])
    if not_empty:
        rng = np.random.default_rng(seed)
        k = 2.0
        A = 8.0
        ws = rng.weibull(k, size=(n_timesteps, n_pt)) * A
        wd = rng.uniform(0, 360, (n_timesteps, n_pt))

        ds["wind_speed"].data = ws
        ds["wind_direction"].data = wd

    ustack_ds = _empty_unstack(ds, is_scalar)
    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _TS_ATTRS)

    return _update_history(ds)


def _read_ts_windpro_txt(fpath):
    """Parses windpro format txt file into a dataset.



    Parameters
    ----------
    fpath : [str]
        [file path to be parsed]

    Returns
    -------
    xarray.Dataset

    """

    def _is_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    # parse parameters from windpro header;
    lng, lat = 0.0, 0.0
    data_start_line = -1
    disp_height = -1
    with open(fpath, "r") as file:
        for i, line in enumerate(file):
            # parse coordinates
            if "Geographical Coordinates" in line:
                parts = line.split()
                for j, p in enumerate(parts):
                    if _is_float(p) and parts[j - 1] == "Longitude:":
                        lng = float(p)
                    if _is_float(p) and parts[j - 1] == "Latitude:":
                        lat = float(p)
            # parse height
            if "Displacement height" in line:
                parts = line.split()
                for p in parts:
                    if _is_float(p):
                        disp_height = float(p)
            # reached header
            if "TimeStamp" in line:
                data_start_line = i
                break

    if disp_height > 0:
        warnings.warn(
            "Displacement height cannot be used in WindKit. Set it up via the map instead."
        )
    if lng == 0.0 and lat == 0.0:
        raise Exception("Couldn't parse coordinates")

    ts = pd.read_csv(
        fpath,
        delimiter="\t{2}|\t",
        parse_dates=["TimeStamp"],
        skiprows=range(data_start_line),
        engine="python",
    )

    # parse height from the wind speed/direction column
    for col in ts.columns:
        if "Mean wind speed" in col:
            height = float(re.findall(r"[0-9]+.[0-9]+m", col)[0].replace("m", ""))
            ts = ts.rename({col: "ws"}, axis="columns")
        if "Wind direction" in col:
            ts = ts.rename({col: "wd"}, axis="columns")

    ts = ts[~ts.ws.str.contains("-")]
    ts = ts[ts["ws"].notna()]
    ts = ts[ts["wd"].notna()]
    ts["ws"] = ts["ws"].astype(float)
    ts["wd"] = ts["wd"].astype(float)

    ts_ds = xr.Dataset(
        {
            "wind_speed": (["time"], ts["ws"]),
            "wind_direction": (["time"], ts["wd"]),
        },
        coords={
            "time": ("time", ts["TimeStamp"]),
            "south_north": lat,
            "west_east": lng,
            "height": height,
            "crs": 0,
        },
    )

    set_crs(ts_ds, 4326)
    _update_var_attrs(ts_ds, {**_TS_ATTRS})
    # validate the dataset before returning
    validate_tswc(ts_ds)
    return ts_ds


def _read_csv(
    file_name,
    west_east=0.0,
    south_north=0.0,
    crs=4326,
    time_col=0,
    height_to_columns=None,
    pandas_kwargs=None,
):
    """
    Reads a csv file into a time series wind climate xarray.Dataset. The file must have one time
    entry per row, a column with a time stamp and at least one wind speed and one wind direction. It
    allows to create a dataset for several heights.

    Parameters
    ----------
    file_name : str
        file path to a csv file with wind speed and wind direction measurements for different timestamps.
    west_east: float, optional
        west east locaton of the measurement. Defaults to 0.0.
    south_north: float, optional
        south north location of the measurement. Defaults to 0.0.
    crs : int, dict, str or pyproj.crs.CRS, optional
        Value to initialize `pyproj.crs.CRS`. Defaults to 4326.
    time_col: int, str
        column position (integer) or header (str) where the timestamp is located. it can be overriden by
        using `pandas.read_csv` kwargs. Defaults to 0 (first column in the file).
    height_to_columns: dict
        dictionary to map the wind speed and directions to its corresponding height. The key is a float
        with the height, and the value is a tuple (str,str) with the header for the wind speed and the
        header for the wind direction, respectively. If the parameter is `None`, the columns are inferred
        from the column names in the files. The function will find wind speeds for different heights and
        after that will look for wind direction columns, matching them to the closest height.
        Examples of autodetected header formats:

            - ws_10, ws_10_mean, ws10, WS10 (wind speed at 10 m)
            - windagl10, windagl_10, windagl_10_mean (wind speed at 10 m)
            - wd_15, wd_15_mean, w15, WD15 (wind direction at 15m)
            - wdiragl15, wdiragl_15, wdiragl_15_mean (wind direction at 15 m)
    pandas_kwargs: None, dict, optional
        Optional arguments that are forwarded to `pandas.read_csv` for customizing its behavior.

    Returns
    -------
    da: xarray.Dataset
        Time series wind climate dataset  with variables 'wind_speed' and 'wind_direction'
        and with a coordinate and dimension 'time'.

    Raises
    ------
    RuntimeError
        If the time column cannot be parsed or if the wind speed and wind direction columns cannot
        be detected.
    """

    if pandas_kwargs is None:
        pandas_kwargs = {}

    default_pandas_kwargs = {
        "parse_dates": True,
        "index_col": time_col,
    }

    pandas_kwargs = {**default_pandas_kwargs, **pandas_kwargs}

    pd_df = pd.read_csv(file_name, **pandas_kwargs)

    return tswc_from_dataframe(pd_df, west_east, south_north, crs, height_to_columns)


def tswc_from_dataframe(
    pd_df,
    west_east,
    south_north,
    crs,
    height_to_columns=None,
):
    """
    transforms a pandas.DataFrame into a time series wind climate xarray.Dataset. The dataframe must have
    an index with time format and at least one wind speed and one wind direction. It allows to create a
    dataset for several heights.

    Parameters
    ----------
    pd_df : pandas.DataFrame
        pandas dataframe with wind speed and wind direction measurements for different timestamps and
        heights.
    west_east: float
        west east locaton of the measurement
    south_north: float
        south north location of the measurement
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
    height_to_columns: dict
        dictionary to map the wind speed and directions to its corresponding height. The key is a float
        with the height, and the value is a tuple (str,str) with the header for the wind speed and the
        header for the wind direction, respectively. If the parameter is `None`, the columns are inferred
        from the column names in the dataframe. The function will find wind speeds for different heights
        and after that will look for wind direction columns, matching them to the closest height.
        Examples of autodetected header formats:

           - ws_10, ws_10_mean, ws10, WS10 (wind speed at 10 m)

           - windagl10, windagl_10, windagl_10_mean (wind speed at 10 m)

           - wd_15, wd_15_mean, w15, WD15 (wind direction at 15m)

           - wdiragl15, wdiragl_15, wdiragl_15_mean (wind direction at 15 m)

    Returns
    -------
    da: xarray.Dataset
        Time series wind climate dataset with variables 'wind_speed' and 'wind_direction'
        and with a coordinate and dimension 'time'.
    Raises
    ------
    RuntimeError
        If it fails to autodetect the columns
    """
    # Check if index is datetime
    if not isinstance(pd_df.index, pd.DatetimeIndex):
        raise RuntimeError(
            "The dataframe index is not of type 'datetime'. Please provide a pandas.DataFrame with the time as index."
        )

    if height_to_columns is None:
        try:
            height_to_columns = _headers_to_dict(pd_df)
            print("Columns detected")
            print("{:<5} {:<12} {:<12}".format("h", "Wind speed", "Wind dir"))
            for k, v in height_to_columns.items():
                print("{:<5} {:<12} {:<12}".format(k, v[0], v[1]))

        except Exception as err:
            raise RuntimeError(
                str(err)
                + "\nColumns could not be detected automatically. Provide a height_to_columns dictionary."
            )

    ds_pieces = []
    for k, v in height_to_columns.items():
        ws = xr.DataArray(pd_df[v[0]], dims=["time"])
        wd = xr.DataArray(pd_df[v[1]], dims=["time"])
        ds_piece = xr.Dataset({"wind_speed": ws, "wind_direction": wd}).assign_coords(
            height=k,
        )
        ds_pieces.append(ds_piece)

    ds = xr.concat(ds_pieces, dim="height")
    ds = ds.assign_coords(
        {
            "west_east": west_east,
            "south_north": south_north,
        }
    )
    ds = ds.transpose("time", ...)
    ds = set_crs(ds, crs)
    ds = _update_history(ds)
    return to_stacked_point(_update_var_attrs(ds, {**_TS_ATTRS}))


def _headers_to_dict(df):
    """
    Tries to detect the wind speed and wind direction columns on a pandas dataframe
    and builds a dictionary

    Parameters
    ----------
    df : pandas.DataFrame
        dataframe with wind data

    Returns
    -------
    dict: Dictionary where the key is the height (float) and the value is a tuple (string,string)
    with the wind speed column header and the wind direction column header, or None if the headers
    format does not allow autodetection.
    """
    headers_list = df.columns
    vel_columns, dir_columns = _parse_heights_from_headers(headers_list)
    if len(vel_columns) == 0:
        raise RuntimeError("No wind speed columns were found.")
    if len(dir_columns) == 0:
        raise RuntimeError("No wind direction columns were found.")
    v_list = np.array([x[0] for x in vel_columns])
    d_list = np.array([x[0] for x in dir_columns])
    duplicate_heights = [
        x for x, count in collections.Counter(v_list).items() if count > 1
    ]
    if len(duplicate_heights) > 0:
        duplicate_heights_err_msg = ""
        for val in duplicate_heights:
            duplicate_heights_err_msg += (
                f"There are duplicate entries for height {val}\n"
            )
        raise RuntimeError(duplicate_heights_err_msg.rstrip())

    indices = _closest_dir_index(v_list, d_list)

    final_dict = {}
    for i, val in enumerate(vel_columns):
        final_dict.update({val[0]: (val[1], dir_columns[indices[i]][1])})

    return final_dict


def _parse_heights_from_headers(header_list):
    """Detect the wind speed and wind direction columns from a header list

    Parameters
    ----------
    header_list : list of string
        list with each header

    Returns
    -------
    list: list with tuples (float,string) with the height and the string header of the wind speed
    list: list with tuples (float,string) with the height and the string header of the wind direction
    """
    response_h = []
    response_d = []
    velocity_patterns_list = [
        r"(?:(?:windagl)|(?:ws))_*(?P<height>\d*\.*\d+).*(?:mean)*",
        r"a(?P<height>\d*\.*\d+)(:?(:?|:?T0deg))_wind_speed_mean",
    ]
    direction_patterns_list = [
        r"(?:(?:wdiragl)|(?:wd))_*(?P<height>\d*\.*\d+).*(?:mean)*",
        r"d(?P<height>\d*\.*\d+)(:?(:?|:?T0deg))_wind_direction_mean",
    ]

    while len(velocity_patterns_list) != 0:
        velocity_pattern = velocity_patterns_list.pop(0)
        direction_pattern = direction_patterns_list.pop(0)
        for val in header_list:
            match_vel = re.match(velocity_pattern, val, re.IGNORECASE)
            match_dir = re.match(direction_pattern, val, re.IGNORECASE)
            if match_vel is not None:
                height_vel = match_vel.group("height")
                response_h.append((float(height_vel), val))
            if match_dir is not None:
                height_dir = match_dir.group("height")
                response_d.append((float(height_dir), val))

    return response_h, response_d


def _closest_dir_index(vel_list, dir_list):
    """
    returns  a list with the indices with the closest value of wind
    direction for a given wind velocity

    Parameters
    ----------
    vel_list : numpy.array
        array with heights where the velocity was measured
    dir_list : numpy.array
        array with height where the direction was measured

    Returns
    -------
    list : list
        list with the indices in dir_list corresponding to vel_list
    """
    resp = []
    for val in vel_list:
        resp.append(np.argmin(abs(val - dir_list)))
    return resp


def read_tswc(filename, file_format="infer", **kwargs):
    """
    Reads a time series wind climate file into a xarray.Dataset.

    Parameters
    ----------
    filename : str
        path to the file to be read.
    file_format : str
        format of the file to be read. If 'infer' is passed, the function will try to infer the format
        from the file extension. Defaults to 'infer'.
    **kwargs : dict
        Additional arguments that are forwarded to the specific file reader.

    Returns
    -------
    xarray.Dataset
        Time series wind climate dataset.
    """
    if file_format == "infer":
        file_format = _infer_file_format(filename)

    if file_format == "csv":
        ds = _read_csv(filename, **kwargs)
    elif file_format == "txt":
        ds = _read_ts_windpro_txt(filename, **kwargs)
    elif file_format == "nc":
        ds = xr.open_dataset(filename, **kwargs)
    else:
        raise NotImplementedError(f"File format {file_format} is not supported.")

    ds = _update_var_attrs(ds, _TS_ATTRS)
    return _update_history(ds)


def _mean_ws_moment(tswc, moment=1, **kwargs):
    """Calculates mean wind speed moment from time series wind climate dataset."""
    result = (tswc[WS] ** moment).mean(dim=DIM_TIME)
    result = result.rename(f"mean_wind_speed_{moment}th_moment")
    return _update_history(result)


def _ws_cdf(tswc, **kwargs):
    """Calculates wind speed cumulative distribution function from time series wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")


def _ws_freq_gt_mean(tswc, **kwargs):
    """Calculates wind speed frequency greater than mean from time series wind climate dataset."""
    mean = tswc[WS].mean(dim=DIM_TIME)
    result = (tswc[WS] > mean).mean(dim=DIM_TIME)
    result = result.rename("wind_speed_fgtm")
    return _update_history(result)


def _mean_wind_speed(tswc, **kwargs):
    """Calculates mean wind speed from time series wind climate dataset."""
    result = tswc[WS].mean(dim=DIM_TIME)
    result = result.rename("mean_wind_speed")
    return _update_history(result)


def _mean_power_density(tswc, air_density=1.225, **kwargs):
    """Calculates mean power density from time series wind climate dataset."""
    result = 0.5 * air_density * tswc[WS] ** 3
    result = result.mean(dim=DIM_TIME)
    result = result.rename("mean_power_density")
    return _update_history(result)


def _extrapolate_to_height(tswc, height, shear_exponent=0.143):
    """Extrapolates wind speed and wind direction to a given height using power law for wind speed"""
    ws_extrapolated = shear_extrapolate(
        tswc["wind_speed"], height, shear_exponent=shear_exponent
    )
    wd_extrapolated = tswc["wind_direction"].interp(
        height=height, method="nearest", kwargs={"fill_value": "extrapolate"}
    )

    result = xr.Dataset(
        {
            "wind_speed": ws_extrapolated,
            "wind_direction": wd_extrapolated,
        }
    ).assign_attrs(tswc.attrs)

    result = result.transpose(*result.wind_direction.dims, ...)

    return result
