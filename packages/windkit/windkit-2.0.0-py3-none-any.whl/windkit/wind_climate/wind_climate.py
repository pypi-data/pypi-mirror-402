# (c) 2022 DTU Wind Energy
"""
Wind climate functions.
"""

__all__ = [
    "create_met_fields",
    "mean_ws_moment",
    "ws_cdf",
    "ws_freq_gt_mean",
    "mean_wind_speed",
    "mean_power_density",
    "get_cross_predictions",
    "extrapolate_to_height",
]

import random
from itertools import product

import numpy as np
import xarray as xr

from windkit.xarray_structures.data_structures import _DataStructures
from windkit.xarray_structures.empty import (
    _copy_chunks,
    _define_std_arrays,
    _empty_unstack,
)
from windkit.xarray_structures.metadata import (
    _MEAN_BARO_ATTRS,
    _MEAN_STAB_ATTRS,
    _MET_ATTRS,
    _update_history,
    _update_var_attrs,
)
from windkit.spatial import create_dataset, get_crs, is_cuboid, to_point
from windkit.wind_climate import binned_wind_climate as wk_bwc
from windkit.wind_climate import generalized_wind_climate as wk_gwc
from windkit.wind_climate import geostrophic_wind_climate as wk_geowc
from windkit.wind_climate import time_series_wind_climate as wk_tswc
from windkit.wind_climate import weibull_wind_climate as wk_wwc

_metvars_3d_nosec = [
    "wspd",  # same as A
    "power_density",  # 100 - 600
    "air_density",  # 1.225, 0.2 stddev
    "wspd_emergent",  # same as A
    "power_density_emergent",  # same as power density
    "A_combined",  # same as A
    "k_combined",  # same as k
]
_metvars_4d = ["wspd_sector", "power_density_sector"]  # same as wspd, power_density


def create_met_fields(
    output_locs,
    n_sectors=12,
    not_empty=True,
    seed=9876538,
    met_fields=["wspd", "power_density"],
    **kwargs,
):
    """Create empty dataset filled with met_fields

    Parameters
    ----------
    output_locs : xarray.Dataset
        Output geospatial information
    n_sectors : int
        Number of sectors, defaults to 12
    met_fields : list of strings, or string
        List of variables to include in the output, or a string "all" with
        all the variables. Defaults to ["wspd", "power_dens"]
    kwargs : dict
        Additional arguments.
    Returns
    -------
    ds : xarray.Dataset
        empty met fields dataset
    """
    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)
    random_param_dict = {
        "wspd": (5, 10),
        "power_density": (100, 600),
        "air_density": ("gaussian", 1.225, 0.2),
        "wspd_emergent": (5, 10),
        "power_density_emergent": (100, 600),
        "A_combined": (5, 10),
        "k_combined": (5, 10),
        "wspd_sector": (5, 10),
        "power_density_sector": (100, 600),
    }
    if met_fields == "all":
        met_fields = _metvars_4d + _metvars_3d_nosec

    out_vars = {}
    for var in met_fields:
        if var in _metvars_4d:
            out_vars[var] = da_dict["da_4d"]
        elif var in _metvars_3d_nosec:
            out_vars[var] = da_dict["da_3d_nosec"]
        else:
            raise ValueError(f"Unknown met_field {var}, cannot add to result")

    ds = xr.Dataset(
        out_vars,
        attrs=unstack_attrs,
    )

    if not_empty:
        rng = np.random.default_rng(seed)
        for val in met_fields:
            rand_param = random_param_dict[val]
            if len(rand_param) == 2:
                ds[val].values = rng.uniform(*rand_param, ds[val].shape)
            else:
                ds[val].values = rng.normal(*rand_param[1:], ds[val].shape)
    ustack_ds = _empty_unstack(ds, is_scalar)

    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _MET_ATTRS)
    return _update_history(ds)


def _create_baro(output_locs, n_sectors=12, not_empty=True, seed=9876538, **kwargs):
    """Create empty baro.

    If not_empty=True,the data variables are filled with meaninful random numbers

    Parameters
    ----------
    output_locs : xarray.Dataset
        Output geospatial information, it should be a cuboid with 1 height
    n_sectors : int
        Number of sectors, defaults to 12.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data. Defaults to True.
    seed : int
        Seed for the random data, defaults to 9876538.
    kwargs : dict
        Additional arguments.

    Returns
    -------
    ds : xarray.Dataset
        baro dataset either empty or filled with random numbers.
    """
    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)

    ds = xr.Dataset(
        {"mean_dgdz_dir": da_dict["da_4d"], "mean_dgdz": da_dict["da_4d"]},
        attrs=unstack_attrs,
    )
    n_pt = len(ds["point"])
    if not_empty:
        rng = np.random.default_rng(seed)
        mean_dgdz_dir = rng.uniform(-180.0, 180.0, [n_sectors, n_pt])
        mean_dgdz = rng.uniform(0.0, 0.015, [n_sectors, n_pt])
        ds["mean_dgdz_dir"] = xr.DataArray(
            mean_dgdz_dir, ds["mean_dgdz_dir"].coords, ds["mean_dgdz_dir"].dims
        )
        ds["mean_dgdz"] = xr.DataArray(
            mean_dgdz, ds["mean_dgdz"].coords, ds["mean_dgdz"].dims
        )

    ustack_ds = _empty_unstack(ds, is_scalar)
    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _MEAN_BARO_ATTRS)

    return _update_history(ds)


def _create_stab(output_locs, n_sectors=12, not_empty=True, seed=9876538, **kwargs):
    """Create empty stab.

    If not_empty=True,the data variables are filled with meaninful random numbers

    Parameters
    ----------
    output_locs : xarray.Dataset
        Output geospatial information, it should be a cuboid with 1 height
    n_sectors : int
        Number of sectors, defaults to 12.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data. Defaults to True.
    seed : int
        Seed for the random data, defaults to 9876538.
    kwargs : dict
        Additional arguments.

    Returns
    -------
    ds : xarray.Dataset
        stab dataset either empty or filled with random numbers.
    """
    if not is_cuboid(output_locs):
        raise ValueError("output_locs must be a cuboid")

    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)
    ds = xr.Dataset(
        {
            "mean_temp_scale_land": da_dict["da_3d_nohgt"],
            "rms_temp_scale_land": da_dict["da_3d_nohgt"],
            "mean_pblh_scale_land": da_dict["da_3d_nohgt"],
            "mean_temp_scale_sea": da_dict["da_3d_nohgt"],
            "rms_temp_scale_sea": da_dict["da_3d_nohgt"],
            "mean_pblh_scale_sea": da_dict["da_3d_nohgt"],
        },
        attrs=unstack_attrs,
    )
    n_pt = len(ds["point"])
    if not_empty:
        rng = np.random.default_rng(seed)
        mean_temp_scale_land = rng.uniform(-0.9, 0.22, [n_sectors, n_pt])
        rms_temp_scale_land = rng.uniform(0.0, 0.45, [n_sectors, n_pt])
        mean_pblh_scale_land = rng.uniform(15.0, 9707.0, [n_sectors, n_pt])
        mean_temp_scale_sea = rng.uniform(-0.19, 0.19, [n_sectors, n_pt])
        rms_temp_scale_sea = rng.uniform(0.0, 0.12, [n_sectors, n_pt])
        mean_pblh_scale_sea = rng.uniform(67, 1000, [n_sectors, n_pt])

        ds["mean_temp_scale_land"] = xr.DataArray(
            mean_temp_scale_land,
            ds["mean_temp_scale_land"].coords,
            ds["mean_temp_scale_land"].dims,
        )
        ds["rms_temp_scale_land"] = xr.DataArray(
            rms_temp_scale_land,
            ds["rms_temp_scale_land"].coords,
            ds["rms_temp_scale_land"].dims,
        )
        ds["mean_pblh_scale_land"] = xr.DataArray(
            mean_pblh_scale_land,
            ds["mean_pblh_scale_land"].coords,
            ds["mean_pblh_scale_land"].dims,
        )
        ds["mean_temp_scale_sea"] = xr.DataArray(
            mean_temp_scale_sea,
            ds["mean_temp_scale_sea"].coords,
            ds["mean_temp_scale_sea"].dims,
        )
        ds["rms_temp_scale_sea"] = xr.DataArray(
            rms_temp_scale_sea,
            ds["rms_temp_scale_sea"].coords,
            ds["rms_temp_scale_sea"].dims,
        )
        ds["mean_pblh_scale_sea"] = xr.DataArray(
            mean_pblh_scale_sea,
            ds["mean_pblh_scale_sea"].coords,
            ds["mean_pblh_scale_sea"].dims,
        )

    ustack_ds = _empty_unstack(ds, is_scalar)
    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _MEAN_STAB_ATTRS).isel(
        height=0
    )

    return _update_history(ds)


def _get_wc_struct(obj, raise_error=True):
    """Get the type of a WindKit wind climate object.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object to determine the wind climate structure from.

    Returns
    -------
    string :
        Spatial structure name. Can be on of:
            - 'ts'
            - 'bwc'
            - 'wwc'
            - 'genwc'
            - 'geowc'
        If no spatial structure is found None is returned.
    """

    if wk_bwc.is_bwc(obj):
        return _DataStructures.BWC
    elif wk_wwc.is_wwc(obj):
        return _DataStructures.WWC
    elif wk_geowc.is_geowc(obj):
        return _DataStructures.GEOWC
    elif wk_gwc.is_gwc(obj):
        return _DataStructures.GWC
    elif wk_tswc.is_tswc(obj):
        return _DataStructures.TS
    else:
        if raise_error:
            raise ValueError("Unknown wind climate structure")
        else:
            return None


def mean_ws_moment(wc_obj, moment=1, *, bysector=False):
    """Calculate the mean wind speed moment from a wind climate.

    Parameters
    ----------
    wc_obj: xarray.Dataset
        Wind climate object
    moment: int
        Moment to calculate, defaults to 1
    bysector: bool
        Calculate the moment by sector, defaults to True
        Only used for BWC and WWC.

    Returns
    -------
    xarray.DataArray
        DataArray with the wind speed moment.
    """

    wc_struct = _get_wc_struct(wc_obj, raise_error=True)

    if wc_struct == _DataStructures.BWC:
        return wk_bwc._mean_ws_moment(wc_obj, moment, bysector=bysector)
    elif wc_struct == _DataStructures.WWC:
        return wk_wwc._mean_ws_moment(wc_obj, moment, bysector=bysector)
    elif wc_struct == _DataStructures.GEOWC:
        return wk_geowc._mean_ws_moment(wc_obj, moment)
    elif wc_struct == _DataStructures.GWC:
        return wk_gwc._mean_ws_moment(wc_obj, moment)
    elif wc_struct == _DataStructures.TS:
        return wk_tswc._mean_ws_moment(wc_obj, moment)
    else:
        raise ValueError(f"Unknown wind climate structure {wc_struct}")


def ws_cdf(wc_obj, *, bysector=False):
    """Calculate the wind speed cumulative distribution function from a wind climate.

    Parameters
    ----------
    wc_obj: xarray.Dataset
        Wind climate object
    bysector: bool
        Calculate the CDF by sector, defaults to True
        Only used for BWC.

    Returns
    -------
    xarray.DataArray
        DataArray with the wind speed cumulative distribution function.
    """

    wc_struct = _get_wc_struct(wc_obj, raise_error=True)

    if wc_struct == _DataStructures.BWC:
        return wk_bwc._ws_cdf(wc_obj, bysector=bysector)
    elif wc_struct == _DataStructures.WWC:
        return wk_wwc._ws_cdf(wc_obj)
    elif wc_struct == _DataStructures.GEOWC:
        return wk_geowc._ws_cdf(wc_obj, bysector=bysector)
    elif wc_struct == _DataStructures.GWC:
        return wk_gwc._ws_cdf(wc_obj)
    elif wc_struct == _DataStructures.TS:
        return wk_tswc._ws_cdf(wc_obj)
    else:
        raise ValueError(f"Unknown wind climate structure {wc_struct}")


def ws_freq_gt_mean(wc_obj, *, bysector=False):
    """Calculate the wind speed frequency greater than the mean from a wind climate.

    Parameters
    ----------
    wc_obj: xarray.Dataset
        Wind climate object
    bysector: bool
        Calculate the frequency by sector, defaults to True
        Only used for BWC.

    Returns
    -------
    xarray.DataArray
        DataArray with the wind speed frequency greater than the mean.
    """

    wc_struct = _get_wc_struct(wc_obj, raise_error=True)

    if wc_struct == _DataStructures.BWC:
        return wk_bwc._ws_freq_gt_mean(wc_obj, bysector=bysector)
    elif wc_struct == _DataStructures.WWC:
        return wk_wwc._ws_freq_gt_mean(wc_obj)
    elif wc_struct == _DataStructures.GEOWC:
        return wk_geowc._ws_freq_gt_mean(wc_obj, bysector=bysector)
    elif wc_struct == _DataStructures.GWC:
        return wk_gwc._ws_freq_gt_mean(wc_obj)
    elif wc_struct == _DataStructures.TS:
        return wk_tswc._ws_freq_gt_mean(wc_obj)
    else:
        raise ValueError(f"Unknown wind climate structure {wc_struct}")


def mean_wind_speed(wc_obj, *, bysector=False):
    """Calculate the mean wind speed from a wind climate.

    Parameters
    ----------
    wc_obj: xarray.Dataset
        Wind climate object
    bysector: bool
        Calculate the mean by sector, defaults to True
        Only used for BWC and WWC.

    Returns
    -------
    xarray.DataArray
        DataArray with the wind speed.
    """

    wc_struct = _get_wc_struct(wc_obj, raise_error=True)

    if wc_struct == _DataStructures.BWC:
        return wk_bwc._mean_wind_speed(wc_obj, bysector=bysector)
    elif wc_struct == _DataStructures.WWC:
        return wk_wwc._mean_wind_speed(wc_obj, bysector=bysector)
    elif wc_struct == _DataStructures.GEOWC:
        return wk_geowc._mean_wind_speed(wc_obj, bysector=bysector)
    elif wc_struct == _DataStructures.GWC:
        return wk_gwc._mean_wind_speed(wc_obj)
    elif wc_struct == _DataStructures.TS:
        return wk_tswc._mean_wind_speed(wc_obj)
    else:
        raise ValueError(f"Unknown wind climate structure {wc_struct}")


def mean_power_density(wc_obj, *, bysector=False, air_density=1.225):
    """Calculate the power density of wind climate object

    Parameters
    ----------
    wco: xarray.Dataset
        Weibull Wind Climate or Binned Wind Climate Object.
    bysector: bool
        Calculate the power density by sector, defaults to True
        Only used for BWC and WWC.
    air_density: float
        Air density, defaults to 1.225

    Returns
    -------
    xarray.DataArray
        DataArray with the power density.
    """

    wc_struct = _get_wc_struct(wc_obj, raise_error=True)

    if wc_struct == _DataStructures.BWC:
        return wk_bwc._mean_power_density(
            wc_obj, bysector=bysector, air_density=air_density
        )
    elif wc_struct == _DataStructures.WWC:
        return wk_wwc._mean_power_density(
            wc_obj, bysector=bysector, air_density=air_density
        )
    elif wc_struct == _DataStructures.GEOWC:
        return wk_geowc._mean_power_density(
            wc_obj, bysector=bysector, air_density=air_density
        )
    elif wc_struct == _DataStructures.GWC:
        return wk_gwc._mean_power_density(wc_obj)
    elif wc_struct == _DataStructures.TS:
        return wk_tswc._mean_power_density(wc_obj)
    else:
        raise ValueError(f"Unknown wind climate structure {wc_struct}")


def extrapolate_to_height(
    wc_obj,
    height,
    **kwargs,
):
    """Extrapolate wind climate to a given height

    Parameters
    ----------
    wc_obj: xarray.Dataset
        Wind climate object
    height: float
        Height to extrapolate to
    method_wind_speed: str
        Method to use for wind speed extrapolation, defaults to "shear_extrapolation"
    kwargs_wind_speed: dict
        Additional arguments for the wind speed extrapolation method, defaults to None
    method_wind_direction: str
        Method to use for wind direction extrapolation, defaults to "nearest"
    kwargs_wind_direction: dict
        Additional arguments for the wind direction extrapolation method, defaults to None

    Returns
    -------
    xarray.Dataset
        Wind climate object extrapolated to the given height
    """
    wc_struct = _get_wc_struct(wc_obj, raise_error=True)

    if wc_struct == _DataStructures.TS:
        return wk_tswc._extrapolate_to_height(
            wc_obj,
            height,
            **kwargs,
        )
    else:
        raise ValueError(
            f"Extrapolation to height not implemented for wind climate structure {wc_struct}"
        )


def _not_equal(points):
    """Return if not a self-prediction"""
    for x, y in points:
        if x != y:
            yield (x, y)


def _higher(points):
    """Return if the target observation higher or equal than the source"""
    for x, y in points:
        if y[2] >= x[2]:
            yield (x, y)


def _in_range(points, filter_range):
    """Return if the observation is within the chosen range"""
    for x, y in points:
        bottom, top = filter_range
        if x[2] >= bottom and x[2] < top and y[2] >= bottom and y[2] < top:
            yield (x, y)


def get_cross_predictions(
    wcs,
    wcs_src=None,
    include_self_predictions=True,
    only_upward_extrapolations=True,
    filter_range=None,
    sample_size=None,
    seed=4,
):
    """Get cross predictions from a dataset

    Given the filtering options, return a dataset with the points
    where we want to predict from and where we want to predict to.

    Parameters
    ----------
    wcs: :py:class:`xarray.Dataset`
        wind climate `xarray.Dataset` for which we want to do cross predictions
    wcs_src: :py:class:`xarray.Dataset`
        wind climate :py:class:`xarray.Dataset` used as source for the cross predictions.
        If None, 'wcs' is used as source and as target. Defaults to None.
    include_self_predictions: bool
        A self prediction is a pair of points where the input point is
        the exact same as the output point. Keep self predictions in the dataset?
    only_upward_extrapolations: bool
        Keep only the cross predictions where
        the height of point_in >= the height of point_out?
    filter_range: list
        height range that we want to retain from the input dataset
    sample_size: int
        Number of samples to take from the input dataset
    seed: int
        Seed number for the random sampling, if applied

    Returns
    -------
    from_locs: :py:class:`xr.Dataset`
        xarray dataset with input locations
    to_locs: :py:class:`xr.Dataset`
        xarray dataset with target locations
    """

    def point_to_multiindex(ds):
        """Convert to windkit 'point' structure

        Parameters
        ----------
        ds: :any:`xr.Dataset`
            xarray dataset with windkit 'point' structure

        Returns
        -------
        points: :any:`xr.Dataset`
            xarray dataset with multiindex point coordinate
        """
        pp = to_point(ds)
        return pp.set_index(point=["west_east", "south_north", "height"])

    def reindex_points(ds, locs):
        """Reindex ds by using point indices from locs

        Returns the dataset 'ds' but on the points in 'locs'.

        Parameters
        ----------
        ds: :any:`xr.Dataset`
            xarray dataset with windkit 'point' structure
        locs: :any:`xr.Dataset`
            xarray dataset with the desired windkit 'point' structure

        Returns
        -------
        points: :any:`xr.Dataset`
            xarray dataset with the variables from 'ds' but at points from 'locs'
        """
        points = ds.sel(
            point=locs.set_index(point=["west_east", "south_north", "height"])["point"]
        )
        return points.reset_index("point")

    point_bwc = point_to_multiindex(wcs)
    index = point_bwc.point.values
    points = ((i[0], i[1]) for i in product(index, index))

    if not include_self_predictions:
        points = _not_equal(points)

    if only_upward_extrapolations:
        points = _higher(points)

    if filter_range is not None:
        points = _in_range(points, filter_range)

    # if lp is an empty list we have filtered out all measurements
    # so we return None
    lp = list(points)
    if lp:
        if sample_size is not None:
            # take sample_size from the points, if the number of samples exceeds
            # the length of the list, take all points
            random.seed(seed)
            point_from, point_to = zip(*random.sample(lp, min(sample_size, len(lp))))
        else:
            point_from, point_to = zip(*lp)

        dataset_from = create_dataset(
            np.array(point_from).T[0],
            np.array(point_from).T[1],
            np.array(point_from).T[2],
            crs=get_crs(point_bwc),
        )
        dataset_to = create_dataset(
            np.array(point_to).T[0],
            np.array(point_to).T[1],
            np.array(point_to).T[2],
            crs=get_crs(point_bwc),
        )

        to_locs = reindex_points(point_bwc, dataset_to)

        if wcs_src is None:
            from_locs = reindex_points(point_bwc, dataset_from)
        else:
            point_wcs_src = point_to_multiindex(wcs_src)
            from_locs = reindex_points(point_wcs_src, dataset_from)

        return (from_locs, to_locs)
    else:
        return (None, None)
