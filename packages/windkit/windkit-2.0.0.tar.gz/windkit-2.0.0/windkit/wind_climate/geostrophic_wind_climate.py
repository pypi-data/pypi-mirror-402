# (c) 2022 DTU Wind Energy
"""Geostrophic wind climate module

A geostrophic wind climate is somehwat similar as a binned wind climate, but
contains 6 variables:
geo_wv_freq is the geostrophic wind speed frequency binned by wind speed
and wind direction, where the whole histogram sums to 1 (note
that in a binned wind climate the frequency in one sector sums to one).
The geostrophic turning is the turning of the wind in the boundary layer
for each bin given by the geostrophic drag law.

A valid geostrophic wind climate therefore has dimensions ``sector`` and ``wsbin``
and variables ``geo_wv_freq``, ``geo_turn``, ``z0meso``, ``slfmeso``, ``displ``,
 ``flow_sep_height``. Also it must have a valid spatial structure.
"""

__all__ = ["validate_geowc", "is_geowc", "create_geowc"]

import numpy as np
import xarray as xr
import scipy
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
    _GEOWC_ATTRS,
    _update_history,
    _update_var_attrs,
)
from windkit.xarray_structures.wsbin import (
    create_wsbin_coords,
)
from windkit.wind_climate.binned_wind_climate import (
    _mean_ws_moment as _bwc_mean_ws_moment,
    _mean_wind_speed as _bwc_mean_wind_speed,
    _mean_power_density as _bwc_mean_power_density,
    _ws_cdf as _bwc_ws_cdf,
    _ws_freq_gt_mean as _bwc_ws_freq_gt_mean,
)

DATA_VAR_DICT_GEOWC = {
    "geo_wv_freq": ["wsbin", "sector"],
    "geo_turn": ["wsbin", "sector"],
    "z0meso": ["sector"],
    "slfmeso": ["sector"],
    "displ": ["sector"],
    "flow_sep_height": ["sector"],
}

REQ_DIMS_GEOWC = ["wsbin", "sector"]

REQ_COORDS_GEOWC = [
    "sector",
    "wsbin",
]

validate_geowc = _create_validator(
    variables=DATA_VAR_DICT_GEOWC,
    dims=REQ_DIMS_GEOWC,
    coords=REQ_COORDS_GEOWC,
    extra_checks=[],
)

_validate_geowc_wrapper_factory = _create_validation_wrapper_factory(validate_geowc)

is_geowc = _create_is_obj_function(validate_geowc)


def create_geowc(output_locs, n_sectors=4, n_wsbins=10, not_empty=True, seed=9876538):
    """
    Create empty binned wind climate dataset.

    If not_empty=True, the data variables are filled with meaninful random numbers,
    e.g. the sum of wdfreq is 1.

    Parameters
    ----------
    output_loc : xarray.Dataset
        Output geospatial information.
    n_sectors : int
        Number of sectors, defaults to 12.
    n_wsbins: int
        Number of histogram bins, defaults to 30.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data.
    seed : int
        Seed for the random data, defaults to 9876538.

    Returns
    -------
    ds : xarray.Dataset
        Binned wind climate dataset either empty or filled with
        random numbers.
    """

    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)
    ds = xr.Dataset(
        {
            "wdfreq": da_dict["da_4d"],
            "geo_wv_freq": da_dict["da_4d"],
            "z0meso": da_dict["da_3d_nohgt"],
            "slfmeso": da_dict["da_3d_nohgt"],
            "displ": da_dict["da_3d_nohgt"],
            "flow_sep_height": da_dict["da_3d_nohgt"],
        },
        attrs=unstack_attrs,
    )
    wsbin_coords = create_wsbin_coords(n_wsbins, width=1.0)

    ds["geo_wv_freq"] = ds["geo_wv_freq"].expand_dims({"wsbin": wsbin_coords.values})
    ds = ds.assign_coords({**wsbin_coords.coords})
    n_pt = len(ds["point"])

    if not_empty:
        wsbin_n = np.linspace(1, n_wsbins, n_wsbins)
        rng = np.random.default_rng(seed)
        wsbin_full = wsbin_n.repeat(n_sectors * n_pt).reshape(
            (n_wsbins, n_sectors, n_pt)
        )
        k = rng.uniform(1.5, 2.5, [n_sectors, n_pt])
        A = rng.uniform(5, 10, [n_sectors, n_pt])
        wsbin_freq_not1 = scipy.stats.weibull_min.pdf(wsbin_full, k, scale=A)
        wsbin_freq = wsbin_freq_not1 / wsbin_freq_not1.sum(0)

        ds["geo_wv_freq"] = xr.DataArray(
            wsbin_freq, ds["geo_wv_freq"].coords, ds["geo_wv_freq"].sizes
        )
        ds["wdfreq"] = xr.DataArray(
            rng.dirichlet(np.ones(n_sectors), n_pt).T,
            ds["wdfreq"].coords,
            ds["wdfreq"].sizes,
        )
        ds["geo_wv_freq"] = ds["geo_wv_freq"] * ds["wdfreq"]
        ds["geo_turn"] = xr.full_like(ds["geo_wv_freq"], 22.0)
        ds["z0meso"] = xr.full_like(ds["z0meso"], 0.1)
        ds["slfmeso"] = xr.full_like(ds["slfmeso"], 1.0)
        ds["displ"] = xr.full_like(ds["displ"], 0.0)
        ds["flow_sep_height"] = xr.full_like(ds["flow_sep_height"], 0.0)

    ds = ds.drop_vars("wdfreq")
    ustack_ds = _empty_unstack(ds, is_scalar)
    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _GEOWC_ATTRS)

    return _update_history(ds)


def _mean_ws_moment(geowc, **kwargs):
    """Calculates mean wind speed moment from geostrophic wind climate dataset."""
    return _bwc_mean_ws_moment(geowc.rename({"geo_wv_freq": "wv_count"}), **kwargs)


def _ws_cdf(geowc, **kwargs):
    """Calculates wind speed cumulative distribution function from geostrophic wind climate dataset."""
    return _bwc_ws_cdf(geowc.rename({"geo_wv_freq": "wv_count"}), **kwargs)


def _ws_freq_gt_mean(geowc, **kwargs):
    """Calculates wind speed frequency greater than mean from geostrophic wind climate dataset."""
    return _bwc_ws_freq_gt_mean(geowc.rename({"geo_wv_freq": "wv_count"}), **kwargs)


def _mean_wind_speed(geowc, **kwargs):
    """Calculates mean wind speed from geostrophic wind climate dataset."""
    return _bwc_mean_wind_speed(geowc.rename({"geo_wv_freq": "wv_count"}), **kwargs)


def _mean_power_density(geowc, **kwargs):
    """Calculates mean power density from geostrophic wind climate dataset."""
    return _bwc_mean_power_density(geowc.rename({"geo_wv_freq": "wv_count"}), **kwargs)
