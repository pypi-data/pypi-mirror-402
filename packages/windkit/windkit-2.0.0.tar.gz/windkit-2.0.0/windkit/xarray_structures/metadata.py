# (c) 2022 DTU Wind Energy
"""
Variable Metadata for CF Conventions

This module contains a dictionary that lists all possible variables in the WindKit
system. These are then used to make metadata dictionaries for each object in their
respective modules.

In addition to the metadata, there are convience functions for updating object metadata.
"""

__all__ = []

import json
import linecache
import sys
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path

import xarray as xr

from .._version import version
from .data_structures import _DataStructures
from ..spatial._struct import get_spatial_struct

logger = Logger(__name__)

with open(Path(__file__).resolve().parents[1] / "data" / "all_vars.json") as f:
    _ALL_VARS_META = json.load(f)

_GLOBAL_CONVENTIONS = {
    "Conventions": "CF-1.8",
}


def _create_coords(data, dimname, meta):
    """Create simple coordinate DataArray with metadata.

    Parameters
    ----------
    data : list or numpy.ndarray
        Data to fill the datarray with.
    dimname : str
        Name of the dimension, also name of the key in metadata dict.
    meta : dict
        dictionary containing metadata for the coordinate.

    Returns
    -------
    xarray.DataArray
        DataArray containing the coordinate.
    """
    # Create data array
    da = xr.DataArray(data, dims=dimname)
    da = da.assign_coords({dimname: da})
    da[dimname].attrs = {**meta[dimname]}

    return da


# wind time series object
_TS_ATTRS = {
    "wind_speed": _ALL_VARS_META["wind_speed"],
    "wind_direction": _ALL_VARS_META["wind_direction"],
    "object_type": _DataStructures.TS.value,
}

# wind histogram (count) object
_HIS_ATTRS = {
    "wv_count": _ALL_VARS_META["wv_count"],
    "count_bins_exceeded": _ALL_VARS_META["count_bins_exceeded"],
    "object_type": _DataStructures.HIS.value,
}

# stability time series object
_TS_STAB_ATTRS = {
    "temp_scale": _ALL_VARS_META["temp_scale"],
}

# stability histogram object
_HIS_STAB_ATTRS = {
    "sum_temp_scale": _ALL_VARS_META["sum_temp_scale"],
    "sum_squared_temp_scale": _ALL_VARS_META["sum_squared_temp_scale"],
    "sum_pblh": _ALL_VARS_META["sum_pblh"],
    "count_bins_exceeded": _ALL_VARS_META["count_bins_exceeded"],
    "object_type": _DataStructures.HIS_STAB.value,
}

# mean stability histogram
_MEAN_STAB_ATTRS = {
    "mean_temp_scale_land": _ALL_VARS_META["mean_temp_scale_land"],
    "rms_temp_scale_land": _ALL_VARS_META["rms_temp_scale_land"],
    "mean_pblh_scale_land": _ALL_VARS_META["mean_pblh_scale_land"],
    "mean_temp_scale_sea": _ALL_VARS_META["mean_temp_scale_sea"],
    "rms_temp_scale_sea": _ALL_VARS_META["rms_temp_scale_sea"],
    "mean_pblh_scale_sea": _ALL_VARS_META["mean_pblh_scale_sea"],
}

# mean stability histogram
_MEAN_BARO_ATTRS = {
    "mean_dgdz": _ALL_VARS_META["mean_dgdz"],
    "mean_dgdz_dir": _ALL_VARS_META["mean_dgdz_dir"],
}

# baroclinicity histogram object
_HIS_BARO_ATTRS = {
    "wv_count": _ALL_VARS_META["wv_count"],
    "sum_dugdz": _ALL_VARS_META["sum_dugdz"],
    "sum_dvgdz": _ALL_VARS_META["sum_dvgdz"],
    "count_bins_exceeded": _ALL_VARS_META["count_bins_exceeded"],
}


_BWC_ATTRS = {
    "wdfreq": _ALL_VARS_META["wdfreq"],
    "wsfreq": _ALL_VARS_META["wsfreq"],
    "meridian_convergence": _ALL_VARS_META["meridian_convergence"],
    "object_type": _DataStructures.BWC.value,
}


_GEOWC_ATTRS = {
    "geo_wv_freq": _ALL_VARS_META["geo_wv_freq"],
    "geo_turn": _ALL_VARS_META["geo_turn"],
    "object_type": _DataStructures.GEOWC.value,
}


_ELEV_ROSE_ATTRS = {
    "site_elev": _ALL_VARS_META["elevation"],
    "rix": _ALL_VARS_META["rix"],
    "dirrix": _ALL_VARS_META["dirrix"],
    "flow_sep_height": _ALL_VARS_META["flow_sep_height"],
    "nray": _ALL_VARS_META["bz_nray"],
    "grid": _ALL_VARS_META["bz_grid"],
    "c": _ALL_VARS_META["bz_c"],
    "s": _ALL_VARS_META["bz_s"],
    "w": _ALL_VARS_META["bz_w"],
    "hr1": _ALL_VARS_META["bz_hr1"],
    "hi1": _ALL_VARS_META["bz_hi1"],
    "hi2": _ALL_VARS_META["bz_hi2"],
    "r": _ALL_VARS_META["bz_r"],
    "object_type": _DataStructures.ELEV_ROSE.value,
}

_ELEV_ROSE_COORDS = {
    "radial_dist": _ALL_VARS_META["radial_dist"],
    "radials_x_radial_dist": _ALL_VARS_META["radials_x_radial_dist"],
    "radials": _ALL_VARS_META["radials"],
}

_ROU_ROSE_ATTRS = {
    "z0": _ALL_VARS_META["rou_rose_roughness"],
    "slf": _ALL_VARS_META["rou_rose_slf"],
    "dist": _ALL_VARS_META["rou_rose_dist"],
    "displ": _ALL_VARS_META["displacement_height"],
    "nrch": _ALL_VARS_META["rou_rose_nrch"],
    "object_type": _DataStructures.ROU_ROSE.value,
}

_ROU_ROSE_COORDS = {
    "max_rou_changes1": _ALL_VARS_META["max_rou_changes1"],
    "max_rou_changes": _ALL_VARS_META["max_rou_changes"],
}

_GEWC_ATTRS = {
    "year": _ALL_VARS_META["year"],
    "max_wspd": _ALL_VARS_META["max_wspd"],
    "max_wdir": _ALL_VARS_META["max_wdir"],
    "max_time": _ALL_VARS_META["max_time"],
    "object_type": _DataStructures.GEWC.value,
}

_LINCOM_V50_ATTRS = {
    "max_wspd": _ALL_VARS_META["max_wspd"],
    "max_wdir": _ALL_VARS_META["max_wdir"],
    "ierror": _ALL_VARS_META["lincom_lut_err"],
    "object_type": _DataStructures.LINCOM_V50.value,
}

_LINCOM_V50_LUT_ATTRS = {
    "WS": _ALL_VARS_META["wind_speed"],
    "WD": _ALL_VARS_META["wind_direction"],
    "object_type": _DataStructures.LINCOM_V50_LUT.value,
}

_LINCOM_WIND_LEVEL_ATTRS = {
    "WS": _ALL_VARS_META["wind_speed"],
    "U": _ALL_VARS_META["U"],
    "V": _ALL_VARS_META["V"],
    "W": _ALL_VARS_META["W"],
    "flow_inclination": _ALL_VARS_META["flow_inclination"],
    "Z0": _ALL_VARS_META["dyn_roughness"],
    "terrain_inclination": _ALL_VARS_META["terrain_inclination"],
    "DU_DX": _ALL_VARS_META["DU_DX"],
    "DV_DX": _ALL_VARS_META["DV_DX"],
    "DW_DX": _ALL_VARS_META["DW_DX"],
    "DU_DY": _ALL_VARS_META["DU_DY"],
    "DV_DY": _ALL_VARS_META["DV_DY"],
    "DW_DY": _ALL_VARS_META["DW_DY"],
    "DU_DZ": _ALL_VARS_META["DU_DZ"],
    "DV_DZ": _ALL_VARS_META["DV_DZ"],
    "DW_DZ": _ALL_VARS_META["DW_DZ"],
    "object_type": _DataStructures.LINCOM_WIND_LEVEL.value,
}

_LINCOM_WIND_POINT_ATTRS = {
    "elevation": _ALL_VARS_META["elevation"],
    "height": _ALL_VARS_META["height"],
    "WS": _ALL_VARS_META["wind_speed"],
    "WD": _ALL_VARS_META["wind_direction"],
    "flow_inclination": _ALL_VARS_META["flow_inclination"],
    "USTAR": _ALL_VARS_META["USTAR"],
    "DU_DX": _ALL_VARS_META["DU_DX"],
    "DV_DX": _ALL_VARS_META["DV_DX"],
    "DU_DY": _ALL_VARS_META["DU_DY"],
    "DV_DY": _ALL_VARS_META["DV_DY"],
    "DU_DZ": _ALL_VARS_META["DU_DZ"],
    "DV_DZ": _ALL_VARS_META["DV_DZ"],
    "DTilt_DX": _ALL_VARS_META["DTilt_DX"],
    "DTilt_DY": _ALL_VARS_META["DTilt_DY"],
    "DTilt_DZ": _ALL_VARS_META["DTilt_DZ"],
    "ALPHA": _ALL_VARS_META["shear_exp"],
    "object_type": _DataStructures.LINCOM_WIND_POINT.value,
}

_V50_GUMBEL_ATTRS = {
    "gumbel_alpha": _ALL_VARS_META["gumbel_alpha"],
    "gumbel_beta": _ALL_VARS_META["gumbel_beta"],
    "extreme_wspd": _ALL_VARS_META["extreme_wspd"],
    "extreme_uncert": _ALL_VARS_META["extreme_uncert"],
    "ierror": _ALL_VARS_META["gumbel_fit_err"],
    "object_type": _DataStructures.V50_GUMBEL.value,
}

# This is used by rastermap and holds all potential maptypes
_MAP_TYPE_ATTRS = {
    "elevation": _ALL_VARS_META["elevation"],
    "roughness": _ALL_VARS_META["roughness"],
    "landcover": _ALL_VARS_META["landcover"],
    "speedup": _ALL_VARS_META["cfd_speedups"],
    "turning": _ALL_VARS_META["cfd_turnings"],
    "flow_inclination": _ALL_VARS_META["cfd_flow_inclination"],
    "turbulence_intensity": _ALL_VARS_META["cfd_turbulence_intensity"],
    "displacement_height": _ALL_VARS_META["displacement_height"],
    "landmask": _ALL_VARS_META["landmask"],
    "fetch": _ALL_VARS_META["fetch"],
    "object_type": _DataStructures.MAP_TYPE.value,
}

# this is the data structure after adding extra information to
# a basic weibull wind climate
_MET_ATTRS = {
    "A_combined": _ALL_VARS_META["weib_A_combined"],
    "k_combined": _ALL_VARS_META["weib_k_combined"],
    "wspd_sector": _ALL_VARS_META["wind_speed_sector"],
    "wspd": _ALL_VARS_META["wind_speed"],
    "wspd_combined": _ALL_VARS_META["wind_speed_combined"],
    "air_density": _ALL_VARS_META["air_density"],
    "power_density_sector": _ALL_VARS_META["power_density_sector"],
    "power_density": _ALL_VARS_META["power_density"],
    "power_density_combined": _ALL_VARS_META["power_density_combined"],
    "object_type": _DataStructures.MET.value,
}

_SECTOR_COORD_ATTRS = {
    "sector": _ALL_VARS_META["sector"],
    "sector_ceil": _ALL_VARS_META["sector_ceil"],
    "sector_floor": _ALL_VARS_META["sector_floor"],
    "wind_direction": _ALL_VARS_META["wind_direction"],
}

_WSBIN_COORD_ATTRS = {
    "wsbin": _ALL_VARS_META["wsbin"],
    "wsceil": _ALL_VARS_META["wsceil"],
    "wsfloor": _ALL_VARS_META["wsfloor"],
    "wind_speed": _ALL_VARS_META["wind_speed"],
}

_SPECTRUM_ATTRS = {
    "spectrum_freq": _ALL_VARS_META["spectrum_freq"],
    "spectrum_power": _ALL_VARS_META["spectrum_power"],
    "spec_corr_fac": _ALL_VARS_META["spec_corr_fac"],
    "object_type": _DataStructures.SPECTRUM.value,
}

_TOPO_EFFECTS_ATTRS = {
    "z0meso": _ALL_VARS_META["z0meso"],
    "slfmeso": _ALL_VARS_META["slfmeso"],
    "displ": _ALL_VARS_META["displacement_height"],
    "flow_sep_height": _ALL_VARS_META["flow_sep_height"],
    "user_def_speedups": _ALL_VARS_META["user_def_speedups"],
    "orographic_speedups": _ALL_VARS_META["orographic_speedups"],
    "obstacle_speedups": _ALL_VARS_META["obstacle_speedups"],
    "roughness_speedups": _ALL_VARS_META["roughness_speedups"],
    "user_def_turnings": _ALL_VARS_META["user_def_turnings"],
    "orographic_turnings": _ALL_VARS_META["orographic_turnings"],
    "obstacle_turnings": _ALL_VARS_META["obstacle_turnings"],
    "roughness_turnings": _ALL_VARS_META["roughness_turnings"],
    "dirrix": _ALL_VARS_META["dirrix"],
    "site_elev": _ALL_VARS_META["elevation"],
    "rix": _ALL_VARS_META["rix"],
    "object_type": _DataStructures.TOPO_EFFECTS.value,
}


_TOPO_CFD_EFFECTS_ATTRS = {
    "z0meso": _ALL_VARS_META["z0meso"],
    "cfd_speedups": _ALL_VARS_META["cfd_speedups"],
    "cfd_turnings": _ALL_VARS_META["cfd_turnings"],
    "cfd_turbulence_intensity": _ALL_VARS_META["cfd_turbulence_intensity"],
    "cfd_flow_inclination": _ALL_VARS_META["cfd_flow_inclination"],
    "site_elev": _ALL_VARS_META["elevation"],
    "object_type": _DataStructures.TOPO_CFD_EFFECTS.value,
}

# this is the basic data structure returned by
# a WAsP downscaling, in WAsP GUI often referred
# to as the pwc (predicted wind climate)
_WEIB_ATTRS = {
    "A": _ALL_VARS_META["weib_A"],
    "k": _ALL_VARS_META["weib_k"],
    "wdfreq": _ALL_VARS_META["wdfreq"],
    "object_type": _DataStructures.WWC.value,
}

_WTG_ATTRS = {
    "wind_speed": _ALL_VARS_META["wind_speed"],
    "mode": _ALL_VARS_META["wtg_mode"],
    "power_output": _ALL_VARS_META["power_output"],
    "thrust_coefficient": _ALL_VARS_META["thrust_coefficient"],
    "air_density": _ALL_VARS_META["air_density"],
    "stationary_thrust_coefficient": _ALL_VARS_META["stationary_thrust_coefficient"],
    "wind_speed_cutin": _ALL_VARS_META["wind_speed_cutin"],
    "wind_speed_cutout": _ALL_VARS_META["wind_speed_cutout"],
    "rated_power": _ALL_VARS_META["rated_power"],
    "name": _ALL_VARS_META["wtg_model"],
    "manufacturer": _ALL_VARS_META["wtg_manufacturer_name"],
    "rotor_diameter": _ALL_VARS_META["rotor_diameter"],
    "hub_height": _ALL_VARS_META["hub_height"],
    "object_type": _DataStructures.WTG.value,
}

# Data structure returned by aep calculations
_AEP_ATTRS = {
    "gross_aep": _ALL_VARS_META["gross_aep"],
    "gross_aep_sector": _ALL_VARS_META["gross_aep_sector"],
    "potential_aep": _ALL_VARS_META["potential_aep"],
    "potential_aep_sector": _ALL_VARS_META["potential_aep_sector"],
    "net_aep": _ALL_VARS_META["net_aep"],
    "net_aep_sector": _ALL_VARS_META["net_aep_sector"],
    "P_x_aep": _ALL_VARS_META["P_x_aep"],
    "P_x_aep_sector": _ALL_VARS_META["P_x_aep_sector"],
    "object_type": _DataStructures.AEP.value,
}
# Data structure for a wind farm flow map
_WF_FLOW_MAP_ATTRS = {
    "potential_aep_sector": _ALL_VARS_META["potential_aep_sector"],
    "gross_aep_sector": _ALL_VARS_META["gross_aep_sector"],
    "potential_aep_deficit_sector": _ALL_VARS_META["potential_aep_deficit_sector"],
    "wspd_sector": _ALL_VARS_META["wind_speed"],  # Is this right?
    "wspd_eff_sector": _ALL_VARS_META["wind_speed_effective"],  # Is this right?
    "wspd_deficit_sector": _ALL_VARS_META["wind_speed_deficit"],  # Is this right?
    "turbulence_intensity_eff_sector": _ALL_VARS_META[
        "turbulence_intensity_effective_sector"
    ],  # there is a similar
    "wdfreq": _ALL_VARS_META["wdfreq"],
    "potential_aep": _ALL_VARS_META["potential_aep"],
    "gross_aep": _ALL_VARS_META["potential_aep"],
    "potential_aep_deficit": _ALL_VARS_META["potential_aep_deficit"],
    "wspd": _ALL_VARS_META["wind_speed"],  # Is this right?
    "wspd_eff": _ALL_VARS_META["wind_speed_effective"],  # Is this right?
    "wspd_deficit": _ALL_VARS_META["wind_speed_deficit"],  # Is this right?
    "turbulence_intensity_eff": _ALL_VARS_META[
        "turbulence_intensity_effective"
    ],  # there is a siilar
    "object_type": _DataStructures.WF_FLOW_MAP.value,
}


def _update_local_attrs(da, var_dict):
    """Updates data varaible attributes

    Parameters
    ----------
    da: xarray.DataArray
        WindKit DataArray to be updated
    vars_dict : dict
        Dictionary of attributes for the data variable

    Returns
    -------
    xarray.DataArray
        The same DataArray with updated attributes
    """
    # Update attributes if they are in the list otherwise inform the user
    try:
        da.attrs = {**da.attrs, **var_dict[da.name]}
    except KeyError as e:
        logger.info(f"KeyError{e}")

    if get_spatial_struct(da) is not None:
        da.attrs["grid_mapping"] = "crs"

    return da


def _update_var_attrs(obj, var_dict):
    """Update all data variable attributes.

    Parameters
    ----------
    obj : xarray.Dataset or xarray.DataArray
        WindKit Dataset of DataArray to be updated.
    vars_dict : dict
        Dictionary maping variable names to the attributes that should be used.

    Returns
    -------
    xarray.Dataset or xarray.DataArray
        The same Dataset or DataArray with updated attributes.

    """
    var_dict_copy = var_dict.copy()
    object_type = var_dict_copy.pop("object_type", None)
    if isinstance(obj, xr.Dataset):
        # Update attrs in place - no reassignment needed (avoids xarray __setitem__ overhead)
        for var in obj.data_vars:
            _update_local_attrs(obj[var], var_dict)
        for coord in obj.coords:
            _update_local_attrs(obj.coords[coord], var_dict)
        obj.attrs["Conventions"] = "CF-1.8"
        obj.attrs["Package name"] = __name__.split(".")[0]
        obj.attrs["Package version"] = version
        obj.attrs["Creation date"] = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        )
        if object_type is not None:
            obj.attrs["Object type"] = object_type

        from ..config import CONFIG

        obj.attrs["author"] = CONFIG.name
        obj.attrs["author_email"] = CONFIG.email
        obj.attrs["institution"] = CONFIG.institution

    elif isinstance(obj, xr.DataArray):
        obj = _update_local_attrs(obj, var_dict)
    else:
        raise ValueError(
            "Can only add attributes to xarray.Dataset or xarray.DataArray objects."
        )

    return obj


def _update_history(ds):
    """Update history global attribute.

    Updates the global history attribute for a xarray Dataset.

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset to be updated.

    Returns
    -------
    xarray.Dataset
        The same Dataset with updated attribute.

    """
    current_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    package = __name__.split(".")[0]

    # Get the function call that was used before calling _update_history.
    # NOTE: If call is from the python interpreter, we can't determine the context, so
    #       include a generic message.
    # Using sys._getframe + linecache instead of inspect.stack for ~430x speedup.
    frame = sys._getframe(2)
    function_context = linecache.getline(frame.f_code.co_filename, frame.f_lineno)
    if not function_context:
        function_call = "Unknown python interpreter command."
    else:
        function_call = function_context.rstrip("\n")

    if "=" in function_call:
        function_call = function_call[function_call.index("=") + 1 :]
        if " " in function_call:
            function_call = function_call[function_call.index(" ") + 1 :]
    history_to_add = (
        current_utc + ":" + "\t" + package + "==" + version + "\t" + function_call
    )

    if "history" in ds.attrs.keys():
        ds.attrs["history"] = ds.attrs["history"] + "\n" + history_to_add
    else:
        ds.attrs["history"] = history_to_add
    return ds


def _update_coord_attrs(ds, attr_dict):
    """Update coordinates attributes.

    Parameters
    ----------

    ds: xarray.Dataset
        Winkdit Dataset to be updated
    attr_dict: dict
        dictionary where the key is a coordinate name and the value is a dictionary
        with the attributes (also key-value pairs) associated to the coordinate.

    Returns
    -------

    xarray.Dataset
        the same dataset with updated attributes.
    """
    ds_output = ds.copy()
    for c in ds.coords:
        ds_output.coords[c].attrs = attr_dict[c]

    return ds_output
