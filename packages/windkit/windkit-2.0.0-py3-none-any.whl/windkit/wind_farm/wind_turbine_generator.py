# (c) 2022 DTU Wind Energy
"""
Wind Turbine classs defines the parameters of a certain type of wind turbine.

"""

__all__ = [
    "validate_wtg",
    "is_wtg",
    "RegulationType",
    "estimate_regulation_type",
    "read_wtg",
    "wtg_power",
    "wtg_cp",
    "wtg_ct",
]

import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path

import numpy as np
import xarray as xr

from windkit.xarray_structures._validate import (
    _create_is_obj_function,
    _create_validation_wrapper_factory,
    _create_validator,
)
from windkit.xarray_structures.metadata import _ALL_VARS_META, _update_var_attrs
from windkit.wind_farm.power_curve import _unify_power_curves


class RegulationType(Enum):
    UNDEFINED = 0
    STALL = 1
    PITCH = 2


DATA_VAR_DICT_WTG = {
    "power_output": ["mode", "wind_speed"],
    "thrust_coefficient": ["mode", "wind_speed"],
    "air_density": ["mode"],
    "stationary_thrust_coefficient": ["mode"],
    "wind_speed_cutin": ["mode"],
    "wind_speed_cutout": ["mode"],
    "rated_power": ["mode"],
    "name": [],
    "rotor_diameter": [],
    "hub_height": [],
    "regulation_type": [],
}

REQ_DIMS_WTG = ["mode", "wind_speed"]

REQ_COORDS_WTG = [
    "wind_speed",
    "mode",
]

validate_wtg = _create_validator(
    variables=DATA_VAR_DICT_WTG,
    dims=REQ_DIMS_WTG,
    coords=REQ_COORDS_WTG,
    extra_checks=[],
)

_validate_wtg_wrapper_factory = _create_validation_wrapper_factory(validate_wtg)

is_wtg = _create_is_obj_function(validate_wtg)


def estimate_regulation_type(wtg: xr.Dataset):
    """Estimate the regulation type of a WTG

    Use the power_output array, to see how many points equal the max power output. This
    does a good job detecting manufacturers power curves, but doesn't detect pitch
    regulation from power curves derived from measurements.

    Parameters
    ----------
    wtg : xr.Dataset
        Wind Turbine Generator object

    Returns
    -------
    RegulationType
        Estimated regulation type object
    """
    if (wtg.power_output == wtg.power_output.max()).sum() >= 3:
        return RegulationType.PITCH
    else:
        return RegulationType.STALL


def _read_windpro_wtg_element(wt_element):  # pragma: no cover not implemented yet
    """Parse the ET element from WindPRO to initilize an WT_cls object.

    Parameters
    ----------
    WT_element : ET element
        Extracted from .xml file in the .optireq file from WindPRO.

    Returns
    -------
    WT : an object of WT_cls
    """
    name = wt_element.attrib["TurbineTypeUID"]
    diameter = np.float64(wt_element.attrib["RotorDiameter"])
    hub_height = np.float64(wt_element.attrib["HubHeight"])

    turbine_modes = wt_element.findall("TurbineMode")
    num_modes = len(turbine_modes)
    wind_speed_cutin = [0.0 for i in range(num_modes)]
    wind_speed_cutout = [0.0 for i in range(num_modes)]
    air_density = [1.225 for i in range(num_modes)]
    dts = [None for i in range(num_modes)]
    mode_ids = [None for i in range(num_modes)]
    for i in range(num_modes):
        turbine_mode = turbine_modes[i]
        air_density[i] = np.float64(turbine_mode.attrib["AirDensity"])
        mode_ids[i] = turbine_mode.attrib["ModeID"]
        wind_speed_cutout[i] = turbine_mode.attrib["StopWindSpeed"]

        power_curve = turbine_mode.find("PowerCurve")
        thrust_curve = turbine_mode.find("ThrustCurve")

        pc = []
        for data in power_curve.findall("Data"):
            ws = np.float64(data.attrib["windSpeed"])
            power = np.float64(data.attrib["power"])
            pc.append([ws, power])

        tc = []
        for data in thrust_curve.findall("Data"):
            ws = np.float64(data.attrib["windSpeed"])
            Ct = np.float64(data.attrib["CT"])
            tc.append([ws, Ct])

        if pc[0][1] == 0:
            pc = pc[1:]

        assert len(pc) == len(tc)
        pc = np.array(pc)
        tc = np.array(tc)

        dt = np.hstack((tc, pc))
        dt = dt[:, (0, 1, 3)]

        dts[i] = dt
        wind_speed_cutin[i] = tc[0, 0]

    rated_power = np.max(dts[0][:, 2])

    # change kW to W for wind speed
    if rated_power > 100:
        rated_power = rated_power * 1000
        for dt in dts:
            dt[:, -1] = dt[:, -1] * 1000

    rated_power = np.max(dts[0][:, 2])

    wind_speed_curves = np.array(dts)

    n_modes, n_wspd, n_vars = wind_speed_curves.shape
    wind_speed = wind_speed_curves[0, :, 0]
    thrust_coefficient = wind_speed_curves[:, :, 1]
    power_output = wind_speed_curves[:, :, 2]

    wtg = xr.Dataset(
        data_vars={
            "name": name,
            "rotor_diameter": diameter,
            "hub_height": hub_height,
            "wind_speed_cutin": (("mode",), wind_speed_cutin),
            "wind_speed_cutout": (("mode",), wind_speed_cutout),
            "rated_power": (("mode",), rated_power),
            "power_output": (("mode", "wind_speed"), power_output),
            "thrust_coefficient": (("mode", "wind_speed"), thrust_coefficient),
        },
        coords={
            "wind_speed": (("wind_speed",), wind_speed),
            "mode": (("mode",), np.arange(n_modes)),
            "air_density": (("mode",), air_density),
        },
    )

    return wtg


def _read_windpro_wtg(wtg_file):  # pragma: no cover not implemented yet
    """Read a windpro-formatted XML ".wtg" file.

    Parameters
    ----------
    wtg_file : string, pathlib.Path
        A string or pathlib.Path denoting the location of the .wtg file

    Returns
    -------
    xr.Dataset
        Wind Turbine Generator dataset as an xarray.Dataset

    """
    tree = ET.parse(wtg_file)
    root = tree.getroot()
    return _read_windpro_wtg_element(root)


def _wasp_wtg_data_points_to_dataset(data_points, wind_speed=None, stat_ct=None):
    """Read power and ct curves from the
    "DataPoint" part of a wasp xml WTG object

    Parameters
    ----------
    data_points : ET element
        "DataPoint" element from WAsP WTG ET

    Returns
    -------
    xr.Dataset
        power and ct curves formatted as xarray.Dataset for a
        specific turbine mode
    """
    wind_speed_ = []
    power_output = []
    thrust_coeff = []
    for row in data_points:
        wind_speed_.append(float(row.attrib["WindSpeed"]))
        power_output.append(float(row.attrib["PowerOutput"]))
        thrust_coeff.append(float(row.attrib["ThrustCoEfficient"]))

    wind_speed_ = np.array(wind_speed_)
    power_output = np.array(power_output)
    thrust_coeff = np.array(thrust_coeff)

    # interpolate to specific wind speed values, if provided.
    if wind_speed is not None:
        power_output = np.interp(
            wind_speed, wind_speed_, power_output, left=0.0, right=0.0
        )
        # if stat_ct is not given, we use the minimum value in the curve.
        if stat_ct is None:
            stat_ct = thrust_coeff.min()
        thrust_coeff = np.interp(
            wind_speed,
            wind_speed_,
            thrust_coeff,
            left=stat_ct,
            right=stat_ct,
        )
    else:
        wind_speed = wind_speed_

    return xr.Dataset(
        {
            "power_output": (("wind_speed",), power_output),
            "thrust_coefficient": (("wind_speed",), thrust_coeff),
        },
        coords={"wind_speed": (("wind_speed",), wind_speed)},
    )


def _combine_wind_speed_arrays(wind_speed_arrays, delta=0.00001):
    """Combine wind speed arrays from multiple WTG modes into a single array

    The steps are:
      1. Find all wind speed start and end points (ws minimums and maximums)
      2. Make a combined wind speed array with all unique values, sorted
      3. If we have different wind speed start and end points, we insert
         all the end points smaller than the greatest one + a very small number
         and all the start points greater than the smallest one - a very small number.
         This is to ensure any interpolation near the start and end points
         will have correct behavior for the tables with missing values.
         For example, if one table ends at 25 m/s, but the max is at 30 m/s,
         any power output interpolation at 25.1 m/s should result in the
         value 0.0, not a value between P_rated and 0.0...

    Parameters
    ----------
    wind_speed_arrays : list
        List of arrays to combine

    delta : float
        Size of small number added to inserted wind speed ends
        and subtracted from inserted wind speed starts

    Returns
    -------
    numpy.array : 1D array of floats, containing the combined wind speed values.

    """

    # check if all max wind speeds are the same
    if not all(
        np.max(wind_speed_arrays[0]) == np.max(wind_speed_arrays[i])
        for i in range(len(wind_speed_arrays))
    ):
        ws_maxs = [np.max(wind_speed_arrays[i]) for i in range(len(wind_speed_arrays))]
    else:
        ws_maxs = None

    # check if all min winds speeds are the same
    if not all(
        np.min(wind_speed_arrays[0]) == np.min(wind_speed_arrays[i])
        for i in range(len(wind_speed_arrays))
    ):
        ws_mins = [np.min(wind_speed_arrays[i]) for i in range(len(wind_speed_arrays))]
    else:
        ws_mins = None

    # Now we get all the unique values from all the individual arrays
    wind_speed = np.sort(np.unique(np.concatenate(wind_speed_arrays)))

    # add any maxes mins to wind speed array by adding small max/min +/- small value
    if ws_maxs is not None:
        for ws_max in ws_maxs:
            if ws_max + delta not in wind_speed and ws_max < wind_speed.max():
                wind_speed = np.append(wind_speed, ws_max + delta)

    if ws_mins is not None:
        for ws_min in ws_mins:
            if ws_min - delta not in wind_speed and ws_min > wind_speed.min():
                wind_speed = np.append(wind_speed, ws_min - delta)

    wind_speed = np.sort(wind_speed)
    return wind_speed


def _read_wasp_wtg_element(wtg_element):
    """Convert a wasp-formatted XML WindTurbineGenator element
    to a WindKit wtg xarray.Dataset.

    Parameters
    ----------
    wtg_element : WTG  ET element
        Extracted from WindTurbineGenerator element of
        the .xml object in the .wwh file.

    Returns
    -------
    xr.Dataset
        Wind Turbine Generator dataset as an xarray.Dataset

    """
    datasets = []

    # Find all wind speed values
    wind_speed_arrays = []
    for mode, table in enumerate(wtg_element.iter("PerformanceTable")):
        wind_speed = []
        for row in table.iter("DataPoint"):
            wind_speed.append(float(row.attrib["WindSpeed"]))
        wind_speed_arrays.append(np.array(wind_speed))

    # check if all wind_speed arrays are the same:
    if all(
        np.array_equal(wind_speed_arrays[0], wind_speed_arrays[i])
        for i in range(len(wind_speed_arrays))
    ):
        wind_speed = None
    else:
        wind_speed = _combine_wind_speed_arrays(wind_speed_arrays)

    for mode, table in enumerate(wtg_element.iter("PerformanceTable")):
        if "StationaryThrustCoEfficient" in table.attrib:
            stat_ct = np.float64(table.attrib["StationaryThrustCoEfficient"])
        else:
            stat_ct = None

        ds = _wasp_wtg_data_points_to_dataset(
            table.iter("DataPoint"), wind_speed=wind_speed, stat_ct=stat_ct
        )
        ds = ds.assign_coords(mode=(("mode",), [mode]))
        ds["air_density"] = np.float64(table.attrib["AirDensity"])
        if stat_ct is not None:
            ds["stationary_thrust_coefficient"] = stat_ct

        ds["wind_speed_cutin"] = np.float64(
            table.find("StartStopStrategy").attrib["LowSpeedCutIn"]
        )
        ds["wind_speed_cutout"] = np.float64(
            table.find("StartStopStrategy").attrib["HighSpeedCutOut"]
        )
        ds["rated_power"] = ds["power_output"].max()
        datasets.append(ds)

    merged = xr.concat(datasets, dim="mode")
    merged["name"] = wtg_element.attrib["Description"]
    try:
        merged["manufacturer"] = wtg_element.attrib[
            "ManufacturerName"
        ]  # this is optional
    except Exception:
        pass
    merged["rotor_diameter"] = np.float64(wtg_element.attrib["RotorDiameter"])
    merged["hub_height"] = np.float64(
        wtg_element.find("SuggestedHeights").find("Height").text
    )

    root_attrs = wtg_element.attrib
    if root_attrs["FormatVersion"] >= "1.02":
        merged["regulation_type"] = RegulationType[
            root_attrs["ControlSystem"].upper()
        ].value
    else:
        merged["regulation_type"] = RegulationType.UNDEFINED.value

    return merged


def _read_wasp_wt_element(wt_element):  # pragma no cover Not used anywhere
    """Convert a wasp-formatted XML element to a WindKit wtg xr.Dataset.

    Parameters
    ----------
    wt_element : ET WT element
        Extracted from .xml object in the .wwh file.

    Returns
    -------
    xr.Dataset
        Wind Turbine Generator dataset as an xarray.Dataset

    """
    root = wt_element.find(".//WindTurbineGenerator")
    return _read_wasp_wtg_element(root)


def _read_wasp_wtg(wtg_file):
    """Read a wasp-formatted XML ".wtg" file.

    Parameters
    ----------
    wtg_file : string, pathlib.Path
        A string or pathlib.Path denoting the location of the .wtg file

    Returns
    -------
    xr.Dataset
        Wind Turbine Generator dataset as an xarray.Dataset

    """
    tree = ET.parse(wtg_file)
    root = tree.getroot()

    return _read_wasp_wtg_element(root)


def read_wtg(wtg_file, file_format="wasp", regulation_type="pitch"):
    """Read in Wind Turbine Generator (WTG) data from a file.

    A WTG dataset contains the following:

    coordinates(dim):
        wind_speed(wind_speed) : wind speed
        mode(mode)             : each mode reprents different ct/power curves

    variables(dims):
        name                                  : name of the WTG
        rotor_diameter                        : rotor diameter in meters
        hub_height                            : hub height a.g.l. in meters
        regulation_type                       : Regulation type (1: stall, 2: pitch)
        air_density(mode)                     : Air density power curve table
        wind_speed_cutin(mode)                : Wind speed cutin
        wind_speed_cutout(mode)               : Wind speed cutout
        rated_power(mode)                     : Rated power
        power_output(mode, wind_speed)        : Power output
        thrust_coefficient(mode, wind_speed)  : Thrust coefficient

    Parameters
    ----------
    wtg_file : str, pathlib.Path
        WTG file to read

    file_format : str
        XML file format to use. Only "wasp" formatting is
        supported currently.

    regulation_type : str or None
        One of "stall", "pitch" or None. If None, uses estimate_regulation_type to
        determine the regulation type. (Default: "pitch")

    Returns
    -------
    xr.Dataset
        WTG dataset
    """
    wtg_file = Path(wtg_file)
    ext = wtg_file.suffix
    if ext == ".nc":
        # read using xarray
        wtg_ds = xr.load_dataset(wtg_file)

    elif ext == ".wtg":
        if file_format == "wasp":
            wtg_ds = _read_wasp_wtg(wtg_file)
        # elif file_format == "windpro":
        #     wtg_ds = _read_windpro_wtg(wtg_file)
    else:
        raise ValueError(
            f"File extension: {ext} not recognized as wind turbine generator!"
        )

    # Update regulation type
    # If undefined from the file and argument is None then estimate, else use argument
    if ("regulation_type" not in wtg_ds.data_vars) or (
        RegulationType(wtg_ds.regulation_type) == RegulationType.UNDEFINED
    ):
        if regulation_type is None:
            wtg_ds["regulation_type"] = estimate_regulation_type(wtg_ds).value
        else:
            wtg_ds["regulation_type"] = RegulationType[regulation_type.upper()].value

    # Validate
    validate_wtg(wtg_ds)

    # Add metadata
    return _update_var_attrs(wtg_ds, _ALL_VARS_META)


def wtg_power(wtg, ws=None, *, interp_method="linear", air_density=None, use_cp=False):
    """Get power output when the inflow wind speed is ws. If the
    given wind speed does not have an associated power output,
    it is linearly interpolated between data points.

    Parameters
    ----------
    wtg : xr.Dataset
        WindKit Wind Turbine Generator (WTG) Dataset
    ws : array_like, floats
        Wind speeds to obtain WTG power for.
    interp_method : str
        Interpolation method to use between provided table values.
        Uses xr.DataArray.interp
    air_density : float, optional
        Air density, defaults to "air_density" from the WTG, or 1.225 kg/m^3 if it's missing.
    use_cp : bool
        If set to true, use the 'power_coefficient' values in the dataset to calculate the
        power output. Defaults to False.

    Returns
    -------
    xr.DataArray
        Power for the given wind speeds

    """

    if ws is None:
        ws = wtg.wind_speed.values

    if use_cp:  # Special case for using power coefficient to calculate power
        if air_density is None:
            if "air_density" in wtg.data_vars:
                air_density = wtg["air_density"]
            else:
                air_density = xr.DataArray(
                    [1.225] * wtg.mode.size,
                    dims=("mode",),
                    coords={"mode": wtg.mode},
                    name="air_density",
                )

        cp = wtg["power_coefficient"].interp(
            wind_speed=ws,
            method=interp_method,
            kwargs={"fill_value": 0.0, "bounds_error": False},
        )

        if not isinstance(ws, xr.DataArray):
            ws = xr.full_like(cp, 0.0) + ws

        rotor_diameter = wtg["rotor_diameter"]

        return cp * (0.5 * air_density * ws**3 * np.pi * (rotor_diameter / 2) ** 2)

    else:
        return wtg["power_output"].interp(
            wind_speed=ws,
            method=interp_method,
            kwargs={"fill_value": 0.0, "bounds_error": False},
        )


def wtg_cp(wtg, ws=None, *, air_density=None, interp_method="linear", use_power=False):
    """Get power coefficient when the inflow wind speed is ws. If the
    given wind speed does not have an associated power output,
    it is linearly interpolated between data points.

    Parameters
    ----------
    wtg : xr.Dataset
        WindKit Wind Turbine Generator (WTG) Dataset
    ws : array_like, floats
        Wind speeds to obtain WTG power for.
    air_density : float, optional
        Air density, defaults to "air_density" from the WTG, or 1.225 kg/m^3 if it's missing.
    interp_method : str
        Interpolation method to use between provided table values.
        Uses xr.DataArray.interp
    use_power : bool
        if set to True, use the 'power_output' values in the dataset to calculate cp. Defaults
        to False.

    Returns
    -------
    xr.DataArray
        Power Coefficient for the given wind speeds

    """

    if ws is None:
        ws = wtg.wind_speed.values

    if use_power:  # special case for using power to calculate power coefficient
        if air_density is None:
            if "air_density" in wtg.data_vars:
                air_density = wtg["air_density"]
            else:
                air_density = xr.DataArray(
                    [1.225] * wtg.mode.size,
                    dims=("mode",),
                    coords={"mode": wtg.mode},
                    name="air_density",
                )

        power = wtg_power(wtg, ws, interp_method=interp_method, air_density=air_density)

        if not isinstance(ws, xr.DataArray):
            ws = xr.full_like(power, 0.0) + ws

        rotor_diameter = wtg["rotor_diameter"]

        return power / (0.5 * air_density * ws**3 * np.pi * (rotor_diameter / 2) ** 2)

    else:
        return wtg["power_coefficient"].interp(
            wind_speed=ws,
            method=interp_method,
            kwargs={"fill_value": 0.0, "bounds_error": False},
        )


def wtg_ct(wtg, ws=None, *, interp_method="linear", ct_stat=None):
    """Get the thrust coefficient of a Wind Turbine Generator
    for given wind speed(s). If the given wind speed(s) do not
    have an associated thrust coefficient, it is interpolated
    between data points.

    Parameters
    ----------
    wtg : xr.Dataset
        WindKit Wind Turbine Generator (WTG) Dataset
    ws : array_like, floats
        Wind speeds to obtain WTG power for.
    interp_method : str
        Interpolation method to use between provided table values.
        Uses xr.DataArray.interp
    ct_stat: float
       Stationary thrust coefficient to be used when the dataset does
       not have it.
    Returns
    -------
    xr.DataArray
        Thrust coefficients for the given wind speeds

    """

    if ws is None:
        ws = wtg.wind_speed.values

    if ct_stat is None:
        if "stationary_thrust_coefficient" in wtg.data_vars:
            ct_stat = wtg["stationary_thrust_coefficient"]
        else:
            ct_stat = (
                wtg["thrust_coefficient"]
                .where(wtg["thrust_coefficient"] != 0)
                .min(dim="wind_speed")
            )

    # Interpolate ct, marking any extrapolated wind-speeds as NaN
    interp_ct = wtg["thrust_coefficient"].interp(
        wind_speed=ws,
        method=interp_method,
        kwargs={"bounds_error": False},
    )

    return interp_ct.fillna(ct_stat)


def _wtgs_to_unified_power_curve_arrays(*wtgs):
    """Convert multiple wtgs to arrays for power curve unification.
    The WTGs must only have one mode (select the mode before passing
    to this function).

    Parameters
    ----------
    *wtgs : xr.Dataset
        Multiple Wind Turbine Generator datasets.

    Returns
    -------
    unified_wind_speeds : np.ndarray
        1D array of unified wind speeds (m/s) for all WTGs.
    power_outputs: np.ndarray
        2D array of power outputs (W) for each WTG. The shape is (n_wind_speeds, n_wtgs).

    """
    wind_speeds_list = []
    power_outputs_list = []

    for wtg in wtgs:
        has_mode_dim = "mode" in wtg.dims
        if has_mode_dim and wtg.dims["mode"] != 1:
            raise ValueError(
                "Each WTG must only have one mode for power curve unification."
            )
        if has_mode_dim:
            wtg = wtg.isel(mode=0)

        wind_speeds_list.append(wtg["wind_speed"].values)
        power_outputs_list.append(wtg["power_output"].values)

    unified_wind_speeds, unified_power_outputs_list = _unify_power_curves(
        wind_speeds_list, power_outputs_list
    )

    return unified_wind_speeds, np.column_stack(unified_power_outputs_list)
