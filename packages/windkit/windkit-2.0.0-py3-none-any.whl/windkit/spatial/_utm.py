# (c) 2022 DTU Wind Energy
"""
UTM related functions.
"""

__all__ = []

import pyproj


def _utmzone2epsg(utm, band):
    """Converts utm zone to EPSG code on the WGS84 geodetic datum

    Parameters
    ----------
    utm: int
        UTM zone number (1--60 starting from zero meridian)
    band: str
        UTC band letter (X at North Pole to C at south pole)

    Returns
    -------
    epsg: int
        EPSG integer id
    """
    # Get hemisphere and EPSG
    if band < "N":  # Southern Hemisphere before "N"
        epsg = 32700 + utm
    else:
        epsg = 32600 + utm
    return epsg


def _getsitecorners(lat, lon, extent):
    """Converts utm zone to EPSG

    Parameters
    ----------
    lat: float
        Latitude of the site
    lon: float
        Longitude of the site
    extent: float
        Size of the bounding box extending from the site in meters.
        An extent of 10000 m means a box with a width of 20000 m.

    Returns
    -------
    res: tuple
        Tuple with x,y-position of site in UTM zones and the lower left
        and upper right corner of the bounding box with size 'extent'
    """
    utm_epsg = _utmzone2epsg(*_mgrs_from_latlon(lat, lon))
    utm_crs = pyproj.CRS.from_epsg(utm_epsg)
    ll_crs = pyproj.CRS.from_epsg(4326)
    epsgstr = "epsg:4326"
    trans = pyproj.Transformer.from_crs(ll_crs, utm_crs, always_xy=True)
    x, y = trans.transform(lon, lat)
    xll = x - extent  # x position of lower left corner
    yll = y - extent  # y position of lower left corner
    xur = x + extent  # x position of upper right corner
    yur = y + extent  # x position of upper right corner

    return (x, y, xll, yll, xur, yur, epsgstr)


def _mgrs_from_latlon(lat, lon):
    """Get the MGRS zone (UTM and letters) from a provided latitude and longitude

    Parameters
    ----------
    lat: float
        Latitude of the site
    lon: float
        Longitude of the site

    Returns
    -------
    utm: int
        UTM zone number (1--60 starting from zero meridian)
    mgrs_letter : char
        Military Grid Reference System grid-zone designation letter
    """
    mgrs_letter = _get_mgrs_letter_from_lat(lat)
    utm = _get_utm_from_latlon(lat, lon)

    return utm, mgrs_letter


def _get_utm_from_latlon(lat, lon):
    """Get UTM zone from lat and lon coordinates

    Parameters
    ----------
    lat: float
        Latitude of the site
    lon: float
        Longitude of the site

    Returns
    -------
    int
        UTM zone number (1--60 starting from zero meridian)

    Notes
    -----
    Get the Longitude bounds for the box, standard grids are 6-degrees
    wide, however latitude bands V and X have special values
    """
    # V band is special for Norway
    if 56 <= lat < 64 and 3 <= lon < 12:
        return 32

    # X is special as it has 9-degree bands
    if 72 <= lat <= 84 and lon >= 0:
        if lon < 9:
            return 31
        elif lon < 21:
            return 33
        elif lon < 33:
            return 35
        elif lon < 42:
            return 37

    # Zones start at 1
    return int((lon + 180) / 6) + 1


def _get_mgrs_letter_from_lat(lat):
    """Gets Military Grid Reference System grid-zone designation letter

    Parameters
    ----------
    lat: float
        Latitude of the site

    Returns
    -------
    char
        Letter indicating mgrs grid-zone

    Raises
    ------
    ValueError
        If lat is outside MGRS bounds

    Notes
    -----
    Latitude bands are a constant 8 degrees except for zone x which is
    12 degrees. The Latitude bands cover the range of 80S to 84N.
    """
    alpha = [
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "J",
        "K",
        "L",
        "M",
        "N",
        "P",
        "Q",
        "R",
        "S",
        "T",
        "U",
        "V",
        "W",
        "X",
    ]
    if lat > 84 or lat < -80:
        raise ValueError("Latitude outside of MGRS bounds.")

    if lat > 72:
        return "X"
    else:
        return alpha[int((lat + 80) / 8)]
