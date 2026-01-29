# (c) 2022 DTU Wind Energy
"""
Routines for working with the wsbin coordinate.
"""

__all__ = [
    "create_wsbin_coords",
]

import numpy as np
import xarray as xr

from .metadata import _WSBIN_COORD_ATTRS

_WSBIN_DIM = "wsbin"
_WSBIN_CENTER_COORD = "wsbin"
_WSBIN_CEIL_COORD = "wsceil"
_WSBIN_FLOOR_COORD = "wsfloor"


def create_wsbin_coords(bins=40, width=1.0, start=0.0):
    """Create wind speed bins coordinates.

    Create a data array with the wind speed bins, ceiling and floor.

    Parameters
    ----------
    bins : int, array_like
        Wind speed bins. Either a single integer number of bins,
        or an array of float bin edges.
    width : float, optional
        Width of the bins, by default 1.0. Only used if bins is an integer.
    start : float, optional
        Starting value of the bins, by default 0.0. Only used if bins is an integer.

    Returns
    -------
    xarray.DataArray
        Data array with wind speed bins and center, ceiling, and floor coordinates.
    """

    # Check if bins is an integer or a numpy.ndarray
    if isinstance(bins, (int, np.integer)):
        if bins <= 0:
            raise ValueError("'bins' must be a positive integer")

        if width <= 0.0:
            raise ValueError("'width' must be a positive float")

        if start < 0.0:
            raise ValueError("'start' must be zero or a positive float")

        bins = np.linspace(start, start + bins * width, bins + 1)

    bins = np.asarray(bins, dtype="float64")

    if bins.ndim != 1:
        raise ValueError(
            "'bins' must be an integer or a 1D numpy.ndarray. Got: %sD array."
            % bins.ndim
        )

    # Check if bins are sorted
    if not np.all(np.diff(bins) > 0):
        raise ValueError("'bins' must be sorted in ascending order")

    # Check if bins are positive
    if not np.all(bins >= 0):
        raise ValueError("'bins' must be positive")

    # Check if bins are finite
    if not np.all(np.isfinite(bins)):
        raise ValueError("'bins' must be finite")

    center = 0.5 * (bins[:-1] + bins[1:])
    ceils = bins[1:]
    floors = bins[:-1]

    da = xr.DataArray(
        center,
        dims=_WSBIN_DIM,
        coords={
            _WSBIN_CENTER_COORD: ((_WSBIN_DIM,), center),
            _WSBIN_CEIL_COORD: ((_WSBIN_DIM,), ceils),
            _WSBIN_FLOOR_COORD: ((_WSBIN_DIM,), floors),
        },
        attrs={
            **_WSBIN_COORD_ATTRS[_WSBIN_DIM],
        },
    )
    da[_WSBIN_CEIL_COORD].attrs = {**_WSBIN_COORD_ATTRS[_WSBIN_CEIL_COORD]}
    da[_WSBIN_FLOOR_COORD].attrs = {**_WSBIN_COORD_ATTRS[_WSBIN_FLOOR_COORD]}
    da[_WSBIN_CENTER_COORD].attrs = {**_WSBIN_COORD_ATTRS[_WSBIN_CENTER_COORD]}

    return da
