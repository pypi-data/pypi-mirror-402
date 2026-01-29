# (c) 2022 DTU Wind Energy
"""
Module for downloading wind time series and wind climates from models and observations.

Currently supports datasets from microsofts planetary computer.

Read about Microsofts planetary computer here: https://planetarycomputer.microsoft.com/docs/overview/about

Use of Microsofts Planetary Computer is subject to Planetary Computer terms of service: https://planetarycomputer.microsoft.com/terms

"""

__all__ = ["get_era5"]


def get_era5(
    datetime, bbox=None, source="planetary_computer", translate_to_windkit=True
):
    """
    Download ERA5 data from the planetary computer.

    Read about Microsofts planetary computer here: https://planetarycomputer.microsoft.com/docs/overview/about

    Use of Microsofts Planetary Computer is subject to Planetary Computer terms of service: https://planetarycomputer.microsoft.com/terms

    This function requires the optional dependencies:
        "zarr", "pystac-client", "planetary-computer", "fsspec", and "adlfs"

    Parameters
    ----------
    datetime : datetime.datetime, str, tuple
        Either a single datetime or datetime range used to filter results.
        If a tuple, it must be a (start, end) tuple of datetime.datetime or timestamps
        as described below.
        You may express a single datetime using a datetime.datetime instance,
        a RFC 3339-compliant timestamp, or a simple date string (see below).
        Instances of datetime.datetime are assumed to be in UTC timezone
        If using a simple date string, the datetime can be specified in YYYY-mm-dd format,
        optionally truncating to YYYY-mm or just YYYY. Simple date strings will be
        expanded to include the entire time period,
        If used in a range, the end of the range expands to the end of that day/month/year.


    bbox : windkit.spatial.BBox, tuple, list, np.ndarray, optional
        Bounding box of the ERA5 data to download. Must be in "EPSG:4326" coordinates.
        If a list, tuple, or np.ndarray is provided, it must be a
        a 1D iterable of [min_lon, min_lat, max_lon, max_lat]. By default None, which
        downloads the entire ERA5 grid.

    source : str, optional
        Source from which we download the ERA5 data, by default "planetary_computer"
        Currently only "planetary_computer" is supported

    translate_to_windkit : bool, optional
        If True, translate the ERA5 data to the format used in windkit, by default True

    Returns
    -------
    xr.Dataset
        ERA5 data

    Raises
    ------
    ValueError
        If the source is not supported

    Notes
    -----
    The ERA5 data is downloaded from the planetary computer. Read about Microsofts planetary computer here: https://planetarycomputer.microsoft.com/docs/overview/about

    Use of Microsofts Planetary Computer is subject to Planetary Computer terms of service: https://planetarycomputer.microsoft.com/terms

    """

    if source == "planetary_computer":
        from .integrations._planetary_computer import _get_era5_from_planetary_computer

        return _get_era5_from_planetary_computer(
            datetime, bbox=bbox, translate_to_windkit=translate_to_windkit
        )
    else:
        raise ValueError(
            f"Unknown source {source}. Valid sources are 'planetary_computer'"
        )
