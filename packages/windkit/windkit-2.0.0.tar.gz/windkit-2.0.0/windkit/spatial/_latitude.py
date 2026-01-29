"""Latitude functions"""

__all__ = []

import logging

from .spatial import get_crs, reproject

logger = logging.getLogger(__name__)


def _get_latitude(ds):
    """Returns data-array of latitude values in wgs84

    Notes
    -----
    Reprojects from projected values if necessary
    """
    # We need the latitude for coriolis calculation
    map_crs = get_crs(ds)
    if map_crs.is_geographic:
        logger.debug("Using raw latitude since output has geographic crs.")
        latitude = ds["south_north"].copy()
    else:
        logger.debug("Reprojecting from output crs to 4326 to get latitude.")
        routput_locs = reproject(ds, 4326, copy=True)  # pylint:disable=no-member
        latitude = routput_locs["south_north"].copy()

    return latitude
