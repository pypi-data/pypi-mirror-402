# (c) 2023 DTU Wind Energy
"""
Module for downloading topography maps from microsofts planetary computer.

Read about Microsofts planetary computer here: https://planetarycomputer.microsoft.com/docs/overview/about

Each dataset downloaded from the planetary computer is licensed by the dataset provider.



"""

from dataclasses import dataclass

import numpy as np
import rioxarray
import xarray as xr

from .. import wind_speed_and_direction
from ._gwa_map_api import _add_safety_buffer
from ..import_manager import _import_optional_dependency
from ..spatial import BBox, clip, get_crs, set_crs, warp

try:
    import pystac_client
except ImportError:
    pystac_client = None

try:
    import planetary_computer
except ImportError:
    planetary_computer = None

try:
    import zarr
except ImportError:
    zarr = None

try:
    import fsspec
except ImportError:
    fsspec = None

try:
    import adlfs
except ImportError:
    adlfs = None


PLANETARY_COMPUTER_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
CRS_GEOGRAPHIC = "EPSG:4326"


@dataclass
class PlanetaryComputerCollection:
    """Class for keeping track of available collection in the planetary computer."""

    name: str
    primary_band: str
    primary_band_variable: str
    dim_time: str
    dim_west_east: str
    dim_south_north: str
    default_datetime: str


ALOS_DEM = PlanetaryComputerCollection(
    name="alos-dem",
    primary_band="data",
    primary_band_variable="elevation",
    default_datetime="2016-12-07",
    dim_time="time",
    dim_west_east="x",
    dim_south_north="y",
)


COPERNICUS_DEM_GLO_30 = PlanetaryComputerCollection(
    name="cop-dem-glo-30",
    primary_band="data",
    primary_band_variable="elevation",
    default_datetime="2021-04-22",
    dim_time="time",
    dim_west_east="x",
    dim_south_north="y",
)

COPERNICUS_DEM_GLO_90 = PlanetaryComputerCollection(
    name="cop-dem-glo-90",
    primary_band="data",
    primary_band_variable="elevation",
    default_datetime="2021-04-22",
    dim_time="time",
    dim_west_east="x",
    dim_south_north="y",
)


NASA_DEM = PlanetaryComputerCollection(
    name="nasadem",
    primary_band="elevation",
    primary_band_variable="elevation",
    default_datetime="2000-02-20",
    dim_time="time",
    dim_west_east="x",
    dim_south_north="y",
)

# ESRI_10M9CLC = PlanetaryComputerCollection(
#     name="io-lulc-9-class",
#     primary_band="data",
#     primary_band_variable="landcover",
#     default_datetime="2018-01-01",
#     dim_time="time",
#     dim_west_east="x",
#     dim_south_north="y",
# )

# ESRI_10M10CLC = PlanetaryComputerCollection(
#     name="io-lulc",
#     primary_band="data",
#     primary_band_variable="landcover",
#     default_datetime="2018-01-01",
#     dim_time="time",
#     dim_west_east="x",
#     dim_south_north="y",
# )


ESA_CCI = PlanetaryComputerCollection(
    name="esa-cci-lc",
    primary_band="lccs_class",
    primary_band_variable="landcover",
    default_datetime="2018-01-01",
    dim_time="time",
    dim_west_east="x",
    dim_south_north="y",
)

ESA_WORLDCOVER = PlanetaryComputerCollection(
    name="esa-worldcover",
    primary_band="map",
    primary_band_variable="landcover",
    default_datetime="2021-01-01",
    dim_time="time",
    dim_west_east="x",
    dim_south_north="y",
)

COLLECTIONS = {
    "ALOS": ALOS_DEM,
    "CDEM_GLO30": COPERNICUS_DEM_GLO_30,
    "CDEM_GLO90": COPERNICUS_DEM_GLO_90,
    "NASADEM": NASA_DEM,
    # "ESRI_10M9CLC": ESRI_10M9CLC,
    # "ESRI_10M10CLC": ESRI_10M10CLC,
    "ESA_CCI": ESA_CCI,
    "WorldCover": ESA_WORLDCOVER,
}


def _get_raster_map_from_planetary_computer(
    bbox, dataset="NASADEM", band=None, datetime=None, safety_buffer=None
):
    """
    Load a map from the planetary computer.

    The following DEMs are available:
        "ALOS"
        "CDEM_GLO30"
        "CDEM_GLO90"
        "NASADEM"

    The following landcover maps are available:
        "ESA_CCI"
        "WorldCover"

    This function requires the optional dependencies: "pystac-client" and "planetary-computer"

    Parameters
    ----------
    bbox : windkit.spatial.BBox, tuple, list, np.ndarray
        Bounding box of the map to download.
        If a list, tuple, or np.ndarray is provided, it must be a
        a 1D iterable of [min_lon, min_lat, max_lon, max_lat].

    dataset : str
        The dataset to load. See above for available datasets. By default "NASADEM".

    band : str, optional
        The band to load. If None, the primary band is loaded.
        By default None, which means the primary band is loaded.


    datetime : datetime.datetime. str, optional
        You may express a single datetime using a datetime.datetime instance,
        a RFC 3339-compliant timestamp, or a simple date string (see below).
        Instances of datetime.datetime are assumed to be in UTC timezone
        If using a simple date string, the datetime can be specified in YYYY-mm-dd format,
        optionally truncating to YYYY-mm or just YYYY. Simple date strings will be
        expanded to include the entire time period.
        If the datetime does not match any available datetimes, the closest datetime is used.
        None by default, which means the default datetime is loaded.

    Returns
    -------
    da : xarray.DataArray
        The map as a DataArray.

    Raises
    ------
    ImportError
        If pystac_client or planetary_computer is not installed.

    ValueError
        If the requested dataset is not supported.


    Notes
    -----
    Read about Microsofts planetary computer here: https://planetarycomputer.microsoft.com/docs/overview/about

    Each dataset downloaded from the planetary computer is licensed by the dataset provider.

    """
    pystac_client = _import_optional_dependency("pystac_client")
    planetary_computer = _import_optional_dependency("planetary_computer")

    if pystac_client is None or planetary_computer is None:
        raise ImportError(
            "To use the planetary computer source, you must install the 'planetary-computer' and 'pystac-client' packages."
        )

    if not isinstance(bbox, BBox):
        bbox = np.asarray(bbox)
        if bbox.shape != (4,):
            raise ValueError(
                "bbox must be a BBox object or a 1D array with 4 elements or a windkit.spatial.BBox object."
            )
        bbox = BBox.from_cornerpts(*bbox, crs=CRS_GEOGRAPHIC)

    if dataset not in COLLECTIONS:
        raise ValueError(
            f"Unknown dataset {dataset}. Valid datasets are {list(COLLECTIONS.keys())}"
        )

    collection = COLLECTIONS[dataset]

    if band is None:
        band = collection.primary_band

    if datetime is None:
        datetime = collection.default_datetime

    catalog = pystac_client.Client.open(
        PLANETARY_COMPUTER_STAC_URL,
        modifier=planetary_computer.sign_inplace,
    )

    bbox_safe = _add_safety_buffer(bbox, safety_buffer)
    bbox_latlon = bbox_safe.reproject_to_geographic()

    search = catalog.search(
        collections=[collection.name],
        datetime=datetime,
        intersects=bbox_latlon.polygon.__geo_interface__,
    )

    items = search.item_collection()

    data_arrays = []
    for item in items:
        da = rioxarray.open_rasterio(item.assets[band].href)
        if collection.dim_time in da.dims:
            da = da.sel(time=collection.default_datetime, method="nearest").squeeze(
                drop=True
            )
            da = da.drop_vars(collection.dim_time)

        da = da.rename(
            {
                collection.dim_west_east: "west_east",
                collection.dim_south_north: "south_north",
            }
        )

        da = set_crs(da, CRS_GEOGRAPHIC)

        if "spatial_ref" in da.coords:
            da = da.drop_vars("spatial_ref")

        da = da.sortby(["south_north", "west_east"])
        da = clip(da, bbox_latlon)

        data_arrays += list(da)

    if len(data_arrays) > 1:
        da = xr.combine_by_coords(data_arrays, combine_attrs="override").squeeze(
            drop=True
        )
    elif len(data_arrays) == 1:
        da = data_arrays[0]
    else:
        raise ValueError("No data found.")

    if band == collection.primary_band:
        da = da.rename(collection.primary_band_variable)

    da = da.drop_duplicates(dim=["south_north", "west_east"], keep="first")

    da_bbox = warp(da, get_crs(bbox))

    # clip latlon bbox to match exactly the input bbox
    da_bbox = clip(da_bbox, bbox)

    if "band" in da.coords:
        if da_bbox.band.size == 1:
            da_bbox = da_bbox.drop_vars("band")

    return da_bbox


def _get_era5_from_planetary_computer(datetime, bbox=None, translate_to_windkit=True):
    """
    Load the ERA5 dataset from the planetary computer.

    The following variables are included:
        "air_pressure_at_mean_sea_level"
        "air_temperature_at_2_metres"
        "dew_point_temperature_at_2_metres"
        "eastward_wind_at_100_metres"
        "eastward_wind_at_10_metres"
        "northward_wind_at_100_metres"
        "northward_wind_at_10_metres"
        "sea_surface_temperature"
        "surface_air_pressure"

    The dataset is loaded as a chunked remote zarr dataset.

    Requires: zarr, pystac_client, planetary_computer

    Parameters
    ----------
    datetime : datetime.datetime, str, tuple
        Either a single datetime or datetime range used to filter results.
        You may express a single datetime using a datetime.datetime instance,
        a RFC 3339-compliant timestamp, or a simple date string (see below).
        Instances of datetime.datetime are assumed to be in UTC timezone
        If using a simple date string, the datetime can be specified in YYYY-mm-dd format,
        optionally truncating to YYYY-mm or just YYYY. Simple date strings will be
        expanded to include the entire time period,
        If used in a range, the end of the range expands to the end of that day/month/year.
        If a tuple, it must be a (start, end) tuple of datetime.datetime or timestamps
        as described above.

    bbox : windkit.spatial.BBox, tuple, list, np.ndarray, optional
        Bounding box of the map to download.
        If a list, tuple, or np.ndarray is provided, it must be a
        a 1D iterable of [min_lon, min_lat, max_lon, max_lat]. By default None, which
        downloads the entire ERA5 grid.

    translate_to_windkit : bool, optional
        If True, translate the ERA5 data to the format used in windkit, by default True

    Returns
    -------
    ds : xarray.Dataset
        The ERA5 dataset.

    Raises
    ------
    ImportError
        If zarr, pystac_client, or planetary_computer is not installed.

    """
    pystac_client = _import_optional_dependency("pystac_client")
    planetary_computer = _import_optional_dependency("planetary_computer")
    _import_optional_dependency("fsspec")
    _import_optional_dependency("adlfs")
    _import_optional_dependency("zarr")

    catalog = pystac_client.Client.open(
        PLANETARY_COMPUTER_STAC_URL,
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=["era5-pds"],
        datetime=datetime,
        query={"era5:kind": {"eq": "an"}},
    )

    items = search.item_collection()

    datasets = []
    for item in items:
        datasets += list(
            xr.open_dataset(asset.href, **asset.extra_fields["xarray:open_kwargs"])
            for asset in item.assets.values()
        )

    ds = xr.combine_by_coords(datasets, join="exact")

    if isinstance(datetime, tuple):
        ds = ds.sel(time=slice(*datetime))
    else:
        ds = ds.sel(time=datetime)

    if bbox is not None:
        if isinstance(bbox, BBox):
            bbox = bbox.bounds()
        xmin, ymin, xmax, ymax = bbox
        ds = ds.sel(lon=slice(xmin, xmax), lat=slice(ymax, ymin))

    if translate_to_windkit:
        ds = ds.rename(
            {
                "lon": "west_east",
                "lat": "south_north",
            }
        )
        ds = set_crs(ds, CRS_GEOGRAPHIC)

        ws10, wd10 = wind_speed_and_direction(
            ds["eastward_wind_at_10_metres"], ds["northward_wind_at_10_metres"]
        )

        ws100, wd100 = wind_speed_and_direction(
            ds["eastward_wind_at_100_metres"], ds["northward_wind_at_100_metres"]
        )

        ws10 = ws10.rename("wind_speed")
        wd10 = wd10.rename("wind_direction")
        ws100 = ws100.rename("wind_speed")
        wd100 = wd100.rename("wind_direction")

        ws10 = ws10.expand_dims(dim={"height": [10.0]})
        wd10 = wd10.expand_dims(dim={"height": [10.0]})
        ws100 = ws100.expand_dims(dim={"height": [100.0]})
        wd100 = wd100.expand_dims(dim={"height": [100.0]})

        ws = xr.concat([ws10, ws100], dim="height")
        wd = xr.concat([wd10, wd100], dim="height")

        ds_wind = xr.merge([ws, wd])
        ds_wind = ds_wind.transpose("time", "height", "south_north", "west_east")

        ds_no_wind = ds.drop_vars(
            [
                "eastward_wind_at_10_metres",
                "northward_wind_at_10_metres",
                "eastward_wind_at_100_metres",
                "northward_wind_at_100_metres",
            ]
        )

        ds = xr.merge([ds_no_wind, ds_wind])

    return ds
