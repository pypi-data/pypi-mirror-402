# (c) 2022 DTU Wind Energy
"""
Module that downloads elevation and roughness maps

Currently driven by the google earth engine, which is a cloud interface service to access
landcover and elevation data, among other things.

Installation & Setup
--------------------

The earth engine is an optional install, you can install with conda::

    conda install earthengine-api google-cloud-sdk

After installation you will have to do a one-time authentication
step from the command line: ``earthengine authenticate``

This will open a browser where you will have to allow google to use
you google account to retrieve data from the google servers. If you are on a machine
without the ability to use a browser (such as an HPC
cluster), you will have to use ``earthengine authenticate --quiet``, which requires you to
to manually copy the authentication code into the terminal.

In addition, you will have to `sign up
<https://signup.earthengine.google.com/#!/>`_ for the google earth engine and give
a reason why you want to use the program. Please pay particular attention to
their terms of service.

Automated Datasets
------------------

Currently, the databases that have been added are the Copernicus Global Land Cover
(CGLS-LC100), Copernicus CORINE land Cover (CORINE), MODIS Global Land Cover MCD12Q1
(MODIS), Globcover and WorldCover
(https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100) as landcover databases and
NASA SRTM Digital Elevation 30m(SRTM), ALOS DSM: Global 30 (ALOS) and NASADEM
(https://developers.google.com/earth-engine/datasets/catalog/NASA_NASADEM_HGT_001?hl=en) as elevation databases.

The landcover databases have standard conversion tables that are included in
``windkit/data/landcover_tables``.

Google Earth Engine provides lists of
`elevation
<https://developers.google.com/earth-engine/datasets/tags/elevation>`_ and
`land cover
<https://developers.google.com/earth-engine/datasets/tags/landcover>`_
data sources, which provide additional details about the various datasources used
in this library.
"""

import logging
import tempfile
import urllib.request
import warnings
from pathlib import Path

import rioxarray

from ..spatial import BBox, clip

CRS_GEOGRAPHIC = "EPSG:4326"


##### Initialize Google Earth Engine ######
try:
    import ee as earth_engine

    try:
        if (Path.home() / "earth_engine.json").exists():
            service_account = "windkit@windkit.iam.gserviceaccount.com"
            credentials = earth_engine.ServiceAccountCredentials(
                service_account, str(Path.home() / "earth_engine.json")
            )
            earth_engine.Initialize(credentials)
        else:
            earth_engine.Initialize()
    except Exception:
        warnings.warn(
            "Could not initialize Google Earth Engine. Run 'earth_engine.Authenticate()' and try again."
        )

except ImportError:
    earth_engine = None


logger = logging.getLogger(__name__)
LIST_DATA_SOURCES = [
    "CGLS-LC100",
    "CORINE",
    "MODIS",
    "Globcover",
    "SRTM",
    "NASADEM",
    "ALOS",
    "WorldCover",
]


def _bbox_to_ee_geometry(bbox):
    return earth_engine.Geometry(bbox.__geo_interface__, bbox.crs.to_string())


def _get_image(datasource):
    """Get URL from google earth engine to retrieve spatial data

    Parameters
    ----------
    datasource : str {'CGLS-LC100', 'CORINE', 'MODIS','Globcover', 'SRTM', 'ALOS'}
            Landcover or elevation datasource

    Returns
    -------
    image: ee.Image
            Google earth engine image
    """
    if earth_engine is None:
        raise ValueError(
            "ee (earthengine-api) is required to get maps from Google Earth Engine"
        )

    if datasource == "CGLS-LC100":
        url = "COPERNICUS/Landcover/100m/Proba-V/Global/2015"
        band = "discrete_classification"
    elif datasource == "CORINE":
        url = "COPERNICUS/CORINE/V20/100m/2018"
        band = "landcover"
    elif datasource == "MODIS":
        url = "MODIS/006/MCD12Q1/2018_01_01"
        band = "LC_Type1"
    elif datasource == "SRTM":
        url = "USGS/SRTMGL1_003"
        band = "elevation"
    elif datasource == "NASADEM":
        url = "NASA/NASADEM_HGT/001"
        band = "elevation"
    elif datasource == "ALOS":
        url = "JAXA/ALOS/AW3D30/V2_2"
        band = "AVE_DSM"
    elif datasource == "Globcover":
        url = "ESA/GLOBCOVER_L4_200901_200912_V2_3"
        band = "landcover"
    elif datasource == "WorldCover":
        url = "ESA/WorldCover/v100"
        band = "Map"
    else:
        str_valid = ", ".join(LIST_DATA_SOURCES)
        raise ValueError(f"Please specify a valid data source from {str_valid}")
    if datasource == "WorldCover":
        dataset = earth_engine.ImageCollection(url).first()
    else:
        dataset = earth_engine.Image(url)
    image = dataset.select(band)
    return image


def _get_ee_map(lat, lon, buffer_dist=20000, source="SRTM", vector=False):
    """Extract map from a given lat, lon

    Extract the smallest square which fits a cirle with radius buffer_dist
    around the coordinates lat,lon.

    Parameters
    ----------
    lat : float
        Center latitude from which we extract a map
    lon : float
        Center longitude from which we extract a map
    buffer_dist : int, optional
        Distance in meters from the given (lat,lon) where a map is extracted, by default 20000
    source : str {"CGLS-LC100", "CORINE", "MODIS", "Globcover", "WorldCover", "SRTM", "ALOS", "NASADEM"}, optional
        Landcover or elevation datasource, by default "SRTM"
    vector:
        If true, return the map in vector format else return a raster map
    """
    if vector:
        raise NotImplementedError("This feature is not yet available.")

    bbox = BBox.utm_bbox_from_geographic_coordinate(lon, lat, buffer_dist)
    ras = _get_raster_map_from_earth_engine(bbox, dataset=source)
    return ras


def _get_raster_map_from_earth_engine(bbox, dataset="NASADEM", band=None):
    """
    Get map from Google Earth Engine. Currently, all maps
    are downloaded in EPSG:4326 coordinates, even if the
    source map is in different coordinates.

    Parameters
    ----------
    bbox : windkit.spatial.BBox
        Bounding box of the map to download. Must be in "EPSG:4326" coordinates.

    dataset : str, optional
        Dataset to retrieve, by default "NASADEM"

    band : str, optional
        Band to retrieve, by default None

    Returns
    -------
    da : xarray.DataArray
        DataArray with the map

    """
    if earth_engine is None:
        raise ValueError(
            "ee (earthengine-api) is required to get maps from Google Earth Engine"
        )

    if not isinstance(bbox, BBox):
        raise ValueError("bbox must be a BBox object or a windkit.spatial.BBox object.")

    ee_image = _get_image(dataset)

    final_url = ee_image.getDownloadURL(
        {
            "region": _bbox_to_ee_geometry(bbox.reproject(CRS_GEOGRAPHIC)),
            "format": "GEO_TIFF",
            "crs": f"EPSG:{bbox.crs.to_epsg()}",
            "scale": ee_image.projection().nominalScale().getInfo(),
        }
    )

    try:
        tmpfile = tempfile.NamedTemporaryFile(delete=False)
        logger.debug(f"Downloading file {tmpfile.name}")
        urllib.request.urlretrieve(final_url, tmpfile.name)
        da = rioxarray.open_rasterio(tmpfile.name)
        da = da.rename({"spatial_ref": "crs", "x": "west_east", "y": "south_north"})
        da = da.drop_vars("band", errors="i")
        if dataset not in ["SRTM", "ALOS", "NASADEM"]:
            da.name = "landcover"
        else:
            da.name = "elevation"
        da = clip(da, bbox)
        da = da.sortby(["south_north", "west_east"])
        return da
    finally:
        tmpfile.close()
        Path(tmpfile.name).unlink()
