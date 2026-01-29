"""
Module for working with predicted wind climates
"""

__all__ = [
    "create_pwc",
]

import xarray as xr

from windkit.xarray_structures.empty import _define_std_arrays, _empty_unstack
from windkit.xarray_structures.metadata import _update_history
from windkit.spatial import _spatial_stack
from windkit.topography.topography import create_wasp_site_effects
from windkit.wind_climate.weibull_wind_climate import create_wwc
from windkit.wind_climate.wind_climate import create_met_fields


def create_pwc(
    output_locs,
    n_sectors=12,
    not_empty=True,
    seed=9876538,
    met_fields=["A_combined", "k_combined", "power_density"],
    site_effects=["site_elev"],
    include_name=True,
    **kwargs,
):
    """Empty predicted wind climate with optional variables.

    Parameters
    ----------
    out_grid : xarray.Dataset
        Output geospatial information
    n_sectors : int
        Number of sectors, defaults to 12.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data. Defaults to True.
    seed : int
        Seed for the random data, defaults to 9876538.
    met_fields : list of str, string
        List of met fields variables to include in the output. If None, nothing
        is included. Defaults to A_combined, k_combined, power_density
    include_site_effects : list of str, str
        List of site factors variables to include in the output. If None, nothing
        is included. Defaults to site_elev.
    include_name : bool
        If true, include a "name" coordinate, which is a string, associated to the dimension
        point, as it is commonly seen in rsf and wrg files. Defaults to True.
    kwargs : dict
        Additional arguments.

    Returns
    -------
    ds : xarray.Dataset
        empty predicted wind climate dataset.
    """

    _, _, is_scalar = _define_std_arrays(output_locs, n_sectors)
    output_locs = _spatial_stack(output_locs)  # needed to handle scalar case
    if include_name:
        output_locs = output_locs.assign_coords(
            name=("point", ["GridPoint"] * output_locs.sizes["point"])
        )
    ds_list = [create_wwc(output_locs, n_sectors)]
    # increment seed +1
    seed += 1
    if site_effects:
        # ds_list.append(empty_wasp_site_effects(output_locs, n_sectors)[include_site_effects])
        ds_list.append(
            create_wasp_site_effects(
                output_locs,
                n_sectors,
                site_effects=site_effects,
                seed=seed,
                not_empty=not_empty,
            )
        )
    # increment seed +1
    seed += 1
    if met_fields is not None:
        ds_list.append(
            create_met_fields(
                output_locs,
                n_sectors,
                not_empty=not_empty,
                met_fields=met_fields,
                seed=seed,
            )
        )

    pwc = xr.merge(ds_list, combine_attrs="override")
    ustack_ds = _empty_unstack(pwc, is_scalar)

    # return _update_history(pwc)
    return _update_history(ustack_ds)
