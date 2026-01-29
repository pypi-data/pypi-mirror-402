# (c) 2022 DTU Wind Energy
"""
Vector related functions.
"""

import geopandas as gpd
import pyproj
import shapely

from ._bbox import BBox


def _clip_vector(obj, mask, **kwargs):  # pragma: no cover covered_in_public_method
    """Clip geopandas.GeoDataFrame or geopandas.GeoSeries to the bounds
    of a bounding box or geometry.

    Parameters
    ----------
    obj : gpd.GeoDataFrame or gpd.GeoSeries
        Geometry to clip with mask.
    mask : tuple, BBox, geopandas.GeoDataFrame, geopandas.GeoSeries, Polygon
        Geometric features or bounding box to clip out of object.

    Returns
    -------
    geopandas.GeoDataFrame or geopandas.GeoSeries:
        Object clipped by geometric features.

    """

    crs_obj = pyproj.CRS.from_user_input(obj.crs)

    # windkit.spatial.bbox.BBox objects are converted to gpd.GeoSeries
    # with the LinearRing converted to Polygon
    if isinstance(mask, BBox):
        poly = shapely.geometry.Polygon(mask.ring.coords)
        mask = gpd.GeoSeries(poly, crs=mask.crs)

    # Basic Polygons are converted to GeoSeries - assuming CRS is gdf.crs
    if isinstance(mask, shapely.geometry.Polygon):
        mask = gpd.GeoSeries(mask, crs=crs_obj)
    elif isinstance(mask, shapely.geometry.LinearRing):
        mask = shapely.geometry.Polygon(mask)
        mask = gpd.GeoSeries(mask, crs=crs_obj)

    # If mask is tuple or list we assume bounds (minx, miny, maxx, maxy)
    # With same CRS as gdf
    if isinstance(mask, (tuple, list)):
        if len(mask) != 4:
            raise ValueError(
                "Got tuple/list of size {len(mask)}. "
                + "Bounds (minx, miny, maxx, maxy)"
                + " should be size 4!"
            )
        minx, miny, maxx, maxy = mask
        poly = shapely.geometry.Polygon(
            ((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy))
        )
        mask = gpd.GeoSeries(poly, crs=crs_obj)

    # Ensure mask is gpd.GeoSeries or gpd.GeoDataFrame
    if not isinstance(mask, (gpd.GeoDataFrame, gpd.GeoSeries)):
        raise ValueError(
            f"mask type {type(mask)} not supported!"
            + " must be tuple of bounds (minx, miny, maxx, maxy), "
            + " windkit.BBox, geopandas.GeoDataFrame, "
            + " geopandas.GeoSeries or shapely.geometry.Polygon"
        )

    crs_mask = pyproj.CRS.from_user_input(mask.crs)
    if not crs_obj.equals(crs_mask):
        raise ValueError(
            "Vector CRS and mask CRS are not identical!" + " please reproject first!"
        )

    # For some reason the keep_geom_type argument is not working on clip. Therefore,
    # we need to explode any multilinestring objects
    return gpd.clip(obj, mask).explode(index_parts=True).reset_index(drop=True)
