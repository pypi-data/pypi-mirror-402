# (c) 2022 DTU Wind Energy
"""
Helper functions for plotting
"""

import math
from typing import Tuple

from .._errors import Missing_arguments, MultiPointError, PlottingAttrsError


def check_multipoint(ds):
    """Raise error if a dataset contains multiple points

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset to be used for plotting

    Raises
    ------
    MultiPointError
        Only single point objects should be plotted
    """
    # Don't care about spatial structure as we are checking the coordinate values
    if "height" in ds.coords:
        if max(ds.west_east.size, ds.south_north.size, ds.height.size) != 1:
            raise MultiPointError()
    else:
        if max(ds.west_east.size, ds.south_north.size) != 1:
            raise MultiPointError()


def check_plotting_attrs(da):
    """Raise error if the "long_name" and "units" attributes are not defined
    in attrs

    Parameters
    ----------

    da : xarray.DataArray
        DataArray representing a data variable, coordinate or dimension

    Raises
    ------
    ValueError
        Both attributes needed for defining the tittle axes of the plot

    Returns
    -------
    title, str
        Title of the axis
    """
    attrs = da.attrs
    name = da.name
    errors = []
    if "long_name" not in attrs:
        errors.append(f"{len(errors) + 1}. Missing attribute value: 'long_name'")
    if "units" not in attrs:
        errors.append(f"{len(errors) + 1}. Missing attribute value: 'units'")
    if errors:
        raise PlottingAttrsError(errors, name)
    if not errors:
        if attrs["units"] == "":
            title = attrs["long_name"]
        else:
            title = attrs["long_name"] + " " + "[" + attrs["units"] + "]"
    return title


def _get_num_rows_cols(num_plots: int) -> Tuple[int, int]:
    sqr_num_plots = math.sqrt(num_plots)
    if (sqr_num_plots % 1) > 0.5:
        num_cols = math.ceil(sqr_num_plots) + 1
        num_rows = math.floor(sqr_num_plots)
    else:
        num_cols = math.ceil(sqr_num_plots)
        num_rows = math.floor(sqr_num_plots)
    return num_rows, num_cols


def missing_arguments(func_name, arg_names):
    """Raise error if the "long_name" and "units" attributes are not defined
    in attrs

    Parameters
    ----------

    func_name : str
        Represents the name of the function with missing args

    arg_names : list of str
        List containing the names of the missing args

    Raises
    ------
    ValueError
        Arsg that need to be inputted in the function
    """
    errors = []
    for i in arg_names:
        errors.append(f"{len(errors) + 1}. Missing argument value: {i}")
    raise Missing_arguments(func_name, errors)


def _get_map_units(gdf):
    """
    Get the map units of a GeoDataFrame.

    This function determines the units of the coordinate reference system (CRS) of a GeoDataFrame.
    If the CRS is geographic, the units are degrees. Otherwise, the units are meters.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame for which to determine the map units.

    Returns
    -------
    str
        The units of the CRS. "deg." for geographic CRS, "m" for other CRS.

    Notes
    -----
    If the GeoDataFrame does not have a CRS, the function will return None.
    """
    if gdf.crs is not None:
        if gdf.crs.is_geographic:
            units = "deg."
        else:
            units = "m"
    return units
