# (c) 2022 DTU Wind Energy
"""
Module that downloads elevation and roughness maps

Currently supports Google's Earth Engine and Microsoft's Planetary Computer.

"""

__all__ = [
    "get_raster_map",
    "get_vector_map",
]

import logging
import warnings

from ..integrations._gwa_map_api import (
    _get_raster_map_from_dtu,
    _get_vector_map_from_dtu,
)
from ..xarray_structures.metadata import (
    _MAP_TYPE_ATTRS,
    _update_history,
    _update_var_attrs,
)

logger = logging.getLogger(__name__)

CRS_GEOGRAPHIC = "EPSG:4326"


def get_raster_map(
    bbox, dataset="NASADEM", band=None, source="planetary_computer", **kwargs
):
    """
    Download a raster map from DTU, the planetary computer or google earth engine.

    Read about Microsofts planetary computer here: https://planetarycomputer.microsoft.com/docs/overview/about

    Use of Microsofts Planetary Computer is subject to Planetary Computer terms of service: https://planetarycomputer.microsoft.com/terms

    Read about google earth engine here: https://earthengine.google.com/

    Use of google earth engine is subject to the Google Earth Engine terms of service: https://earthengine.google.com/terms/


    For both Microsofts Planetary Computer and Earth Engine, each available dataset has an
    additional license from the dataset provider. Please check the license of the dataset
    you are downloading before using it.

    Parameters
    ----------
    bbox : windkit.spatial.BBox
        Bounding box of the map to download. Must be in "EPSG:4326" coordinates.
    dataset : str, optional
        Dataset to download.

        For dtu the following datasets are available:
            "Viewfinder"
            "ESA_CCI"

        For planetary computer the following datasets are available:
            "ALOS"
            "CDEM_GLO30"
            "CDEM_GLO90"
            "NASADEM"
            "ESRI_10M9CLC"
            "ESRI_10M10CLC"
            "ESA_CCI"
            "WorldCover"

        For google earth engine the following datasets are available:
            "CGLS-LC100":
            "CORINE":
            "MODIS":
            "SRTM":
            "NASADEM":
            "ALOS":
            "Globcover":
            "WorldCover":
    band : str, optional
        Band to download. If None, the primary band is downloaded.
    source : str, optional
        Source to download from. Can be "dtu", "planetary_computer" or "earth_engine".
        Default is "planetary_computer".

    Returns
    -------
    xr.DataArray
        The map as a DataArray.

    Raises
    ------
    ValueError
        If the source is not supported

    Notes
    -----
    Some datasets are available from different sources. For these datasets,
    some work has been done to ensure that the maps are consistent.
    Howewer, this cannot be guaranteed.

    """
    if source == "planetary_computer":
        from ..integrations._planetary_computer import (
            _get_raster_map_from_planetary_computer,
        )

        da = _get_raster_map_from_planetary_computer(
            bbox, dataset=dataset, band=band, **kwargs
        )
    elif source == "earth_engine":
        from ..integrations._earth_engine import _get_raster_map_from_earth_engine

        da = _get_raster_map_from_earth_engine(
            bbox, dataset=dataset, band=band, **kwargs
        )
    elif source == "dtu":
        da = _get_raster_map_from_dtu(bbox, dataset=dataset, **kwargs)
    else:
        raise ValueError(
            f"Unknown source {source}. Valid sources are 'dtu', 'planetary_computer' and 'earth_engine'"
        )

    da = _update_var_attrs(da, _MAP_TYPE_ATTRS)
    return _update_history(da)


def get_vector_map(bbox, dataset="CORINE", source="dtu", **kwargs):
    """
    Download a map from the GWA map API.

    Parameters
    ----------
    bbox : windkit.spatial.BBox
        Bounding box of the map to download. Must be in "EPSG:4326" coordinates.
    dataset : str, optional
        Dataset to download. Currently only CORINE vector data.
    source : str, optional
        Source to download from. Can be "dtu" only.
    kwargs: Extra arguments to forward to the dataset readers, e.g. polygon=True [...]

    Returns
    -------
    gpd.GeoDataFrame
        Geopandas GeoDataFrame with vector features

    Raises
    ------
    ValueError
        If the source is not supported
    """
    if source == "dtu":
        lc = _get_vector_map_from_dtu(bbox, dataset=dataset, **kwargs)
    else:
        raise ValueError(f"Unknown source {source}. Only source 'dtu' is supported")

    return lc


def get_map(bbox, dataset="NASADEM", band=None, source="planetary_computer", **kwargs):
    """
    Download a map from the planetary computer or google earth engine.

    Read about Microsofts planetary computer here: https://planetarycomputer.microsoft.com/docs/overview/about

    Use of Microsofts Planetary Computer is subject to Planetary Computer terms of service: https://planetarycomputer.microsoft.com/terms

    Read about google earth engine here: https://earthengine.google.com/

    Use of google earth engine is subject to the Google Earth Engine terms of service: https://earthengine.google.com/terms/

    For both Microsofts Planetary Computer and Earth Engine, each available dataset has an
    additional license from the dataset provider. Please check the license of the dataset
    you are downloading before using it.

    Parameters
    ----------
    bbox : windkit.spatial.BBox
        Bounding box of the map to download. Must be in "EPSG:4326" coordinates.
    dataset : str, optional
        Dataset to download.

        For dtu the following datasets are available:

          - "Viewfinder"
          - "ESA_CCI"

        For planetary computer the following datasets are available:

         - "ALOS"
         - "CDEM_GLO30"
         - "CDEM_GLO90"
         - "NASADEM"
         - "ESRI_10M9CLC"
         - "ESRI_10M10CLC"
         -  "ESA_CCI"
         -  "WorldCover"

        For google earth engine the following datasets are available:

         - "CGLS-LC100":
         - "CORINE":
         - "MODIS":
         -  "SRTM":
         -  "NASADEM":
         -  "ALOS":
         -  "Globcover":
         -  "WorldCover":

    band : str, optional
        Band to download. If None, the primary band is downloaded.
    source : str, optional
        Source to download from. Can be "dtu", "planetary_computer" or "earth_engine".
        Default is "planetary_computer".

    Returns
    -------
    xr.DataArray
        The map as a DataArray.

    Raises
    ------
    ValueError
        If the source is not supported

    Notes
    -----
    Some datasets are available from both sources. For these datasets,
    some work has been done to ensure that the maps are consistent.
    Howewer, this cannot be guaranteed.

    """
    warnings.warn(
        "The function `get_map` is deprecated and is called `get_raster_map` now.",
        FutureWarning,
    )

    return get_raster_map(
        bbox=bbox, dataset=dataset, band=band, source=source, **kwargs
    )


def _get_ee_map(lat, lon, buffer_dist=20000, source="SRTM", vector=False):
    """Extract map from a given lat, lon

    Extract the smallest square which fits a cirle with radius buffer_dist
    around the coordinates lat,lon.

    Read about google earth engine here: https://earthengine.google.com/

    Use of google earth engine is subject to the Google Earth Engine terms of service: https://earthengine.google.com/terms/

    Parameters
    ----------
    lat : float
        Center latitude from which we extract a map
    lon : float
        Center longitude from which we extract a map
    buffer_dist : int, optional
        Distance in meters from the given (lat, lon) where a map is extracted, by default 20000
    source : str {"CGLS-LC100", "CORINE", "MODIS", "Globcover", "WorldCover", "SRTM", "ALOS", "NASADEM"}, optional
        Landcover or elevation datasource, by default "SRTM"
    vector:
        If true, return the map in vector format else return a raster map

    Returns
    -------
    xr.DataArray
        The map as a DataArray.

    """
    warnings.warn(
        "The function `get_ee_map` is deprecated. Use `get_raster_map` with the argument source='earth_engine' instead.",
        FutureWarning,
    )

    from ..integrations._earth_engine import (  # to avoid earth_engine.Initialize being called on import
        _get_ee_map as __get_ee_map,
    )

    return __get_ee_map(lat, lon, buffer_dist=buffer_dist, source=source, vector=vector)
