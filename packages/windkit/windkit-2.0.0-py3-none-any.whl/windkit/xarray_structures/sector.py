# (c) 2022 DTU Wind Energy
"""
Routines for working with the sector coordinate.
"""

__all__ = [
    "create_sector_coords",
]

import numpy as np
import xarray as xr

from .metadata import _SECTOR_COORD_ATTRS


_SECTOR_DIM = "sector"
_SECTOR_CENTER_COORD = "sector"
_SECTOR_CEIL_COORD = "sector_ceil"
_SECTOR_FLOOR_COORD = "sector_floor"


def create_sector_coords(bins=12, start="infer"):
    """Create wind sector coordinate as a data array.

    The data array contains the sector, the sector ceiling and the
    sector floor. The sector width is 360 / bins if bins is an integer.

    Parameters
    ----------
    bins : int, array_like
        Number of bins or an array of bin edges. If bins is an integer,
        the width and start parameters are used to create the bin edges.
        If bins is an array, it must be sorted in ascending order and span the
        negative and positive directions to give the proper center, ceiling,
        and floor values for the sector. All values are made positive
        by taking the modulo 360 after calculating the center, ceiling, and floor.
    start : float, optional
        Starting value of the bins, by default "infer", which, if bins is an integer,
        sets the start to -360/bins/2.0. If bins is an array, start is ignored.

    Returns
    -------
    xarray.DataArray
        Data array with sector coordinates, ceiling and floor.
    """
    # Check if bins is an integer or a numpy.ndarray
    if isinstance(bins, (int, np.integer)):
        if bins <= 0:
            raise ValueError("'bins' must be a positive integer")

        if start == "infer":
            start = -360 / bins / 2.0
        start = float(start)

        bins = np.linspace(start, start + 360, bins + 1)

    bins = np.asarray(bins, dtype="float64")

    if bins.ndim != 1:
        raise ValueError(
            "'bins' must be an integer or a 1D numpy.ndarray. Got: %sD array."
            % bins.ndim
        )

    # Check if bins are sorted
    if not np.all(np.diff(bins) > 0):
        raise ValueError("'bins' must be sorted in ascending order")

    center = 0.5 * (bins[:-1] + bins[1:])
    ceils = bins[1:]
    floors = bins[:-1]

    # modulo to 360
    center = np.mod(center, 360)
    ceils = np.mod(ceils, 360)
    floors = np.mod(floors, 360)

    da = xr.DataArray(
        center,
        dims=_SECTOR_DIM,
        coords={
            _SECTOR_CENTER_COORD: ((_SECTOR_DIM,), center),
            _SECTOR_CEIL_COORD: ((_SECTOR_DIM,), ceils),
            _SECTOR_FLOOR_COORD: ((_SECTOR_DIM,), floors),
        },
        attrs={
            **_SECTOR_COORD_ATTRS[_SECTOR_DIM],
        },
    )
    da[_SECTOR_CEIL_COORD].attrs = {**_SECTOR_COORD_ATTRS[_SECTOR_CEIL_COORD]}
    da[_SECTOR_FLOOR_COORD].attrs = {**_SECTOR_COORD_ATTRS[_SECTOR_FLOOR_COORD]}
    da[_SECTOR_CENTER_COORD].attrs = {**_SECTOR_COORD_ATTRS[_SECTOR_CENTER_COORD]}
    return da
