# (c) 2022 DTU Wind Energy
"""
Routines for working with the direction coordinate.
"""

__all__ = []

import numpy as np
import xarray as xr

from .metadata import _SECTOR_COORD_ATTRS

_DIRECTION_DIM = "sector"
_DIRECTION_COORD = "sector"


def _create_direction_coords(directions):
    """Create wind direction coordinate as a DataArray

    Wind direction coordinates use "sector" as their dimension, but represent a single
    wind direction rather than a sectoral region.

    Parameters
    ----------
    directions : int, array_like
        Wind direction values. Either a single integer number of directions,
        or an array of float direction values.

    Returns
    -------
    xarray.DataArray
        Data array with direction coordinates.

    """

    # Check if directions is an integer or a numpy.ndarray
    if isinstance(directions, (int, np.integer)):
        directions = np.linspace(0, 360, directions + 1)[:-1]

    directions = np.asarray(directions, dtype="float64")
    directions = np.atleast_1d(directions)

    # Check if directions are sorted
    if not np.all(np.diff(directions) > 0):
        raise ValueError("'directions' must be sorted in ascending order")

    # Create data arrays of sector values
    dir_da = xr.DataArray(directions, dims=_DIRECTION_DIM)
    dir_da = dir_da.assign_coords({_DIRECTION_COORD: dir_da})
    dir_da[_DIRECTION_COORD].attrs = {**_SECTOR_COORD_ATTRS["wind_direction"]}

    return dir_da
