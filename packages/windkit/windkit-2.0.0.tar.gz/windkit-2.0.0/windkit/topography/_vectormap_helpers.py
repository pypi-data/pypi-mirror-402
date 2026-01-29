# (c) 2022 DTU Wind Energy
"""Common tools used in vectormap.py and _vectormap_gml.py"""

import json
import math
import warnings
from enum import IntEnum
from inspect import cleandoc
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, box

import windkit as wk

# from .landcover import LandCoverTable

VECTORMAP_FILE_EXTENSIONS = [".map", ".gml", ".shp", ".gpkg"]
VECTORMAP_GEOM_COL = "geometry"
VECTORMAP_ELEV_COL = "elev"
VECTORMAP_ALT_ELEV_COL = {"ELEV", "elevation", "ELEVATION"}
VECTORMAP_ROUL_COL = "z0_left"
VECTORMAP_ROUR_COL = "z0_right"
VECTORMAP_ROU_COLS = (VECTORMAP_ROUL_COL, VECTORMAP_ROUR_COL)
VECTORMAP_IDL_COL = "id_left"
VECTORMAP_IDR_COL = "id_right"
VECTORMAP_ID_COLS = (VECTORMAP_IDL_COL, VECTORMAP_IDR_COL)
VECTORMAP_LMASKL_COL = "landmask_left"
VECTORMAP_LMASKR_COL = "landmask_right"
VECTORMAP_LMASK_COLS = (VECTORMAP_LMASKL_COL, VECTORMAP_LMASKR_COL)
VECTORMAP_META_COLS = [VECTORMAP_ELEV_COL] + list(VECTORMAP_ROU_COLS)
VECTORMAP_INLINE_LCTABLE_COLS = ("id", "d", "z0", "desc")
_MAP_TYPE_CODES = {
    "elevation": 0,
    "roughness": 1,
    "speedup": 2,
    "turning": 3,
    "flow_inclination": 4,
    "turbulence_intensity": 5,
    "landcover": 6,
    "displacement_height": 7,
    "landmask": 15,
    "fetch": 16,
}


class MapTypes(IntEnum):
    elevation = 0
    roughness = 1
    speedup = 2
    turning = 3
    flow_inclination = 4
    turbulence_intensity = 5
    landcover = 6
    displacement_height = 7
    landmask = 15
    fetch = 16


_LR_COLS = {
    "roughness": VECTORMAP_ROU_COLS,
    "landcover": VECTORMAP_ID_COLS,
    "landmask": VECTORMAP_LMASK_COLS,
}


def _read_map_file_header_to_epsg_table(mode="w"):
    """
    Opens the map_file_header_to_epsg.json file and returns it as a dict.

    Parameters
    ----------
    mode : {"r","w"}
        Whether to open projection strings for reading or writing .map files. We support
        more version for reading, but only write to something the latest WAsP GUI version
        can read.

    Returns
    -------
    dict
        Dictionary containing the EPSG table.
    """
    file_suffix = "" if mode == "w" else "_read"
    with open(
        Path(__file__).parents[1]
        / "data"
        / f"map_file_header_to_epsg{file_suffix}.json",
        "r",
    ) as f:
        return json.load(f)


def _roughness_to_landcover(gdf):
    """Converts a roughness to landcover GeoDataFrame.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Geopandas dataframe with the columns 'z0_left' and 'z0_right'

    Returns
    -------
    tuple: (geopandas.GeoDataFrame, LandCoverTable):
        GeoDataFrame with ID's that are present in the lookup table
        and the LandCoverTable itself
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError(
            cleandoc(
                """This is not a GeoDataFrame. Perhaps you are passing in a combination of a GeoDataFrame and a landcover table?"""
            )
        )

    if not _is_z0(gdf):
        raise TypeError("Can only convert roughness map to landcover map")

    # fastest way to get unique values in pandas is in fortran order, hence K
    all_z0 = pd.unique(gdf[list(VECTORMAP_ROU_COLS)].values.ravel("K"))

    z0_to_id = {z0: lid for lid, z0 in enumerate(all_z0)}
    lct = {lid: {"z0": z0, "d": 0.0, "desc": ""} for z0, lid in z0_to_id.items()}

    def _convert_z0(cell):
        return z0_to_id[cell]

    gdf = gdf[["geometry"]].assign(
        id_left=list(map(_convert_z0, gdf.z0_left)),
        id_right=list(map(_convert_z0, gdf.z0_right)),
    )

    return (gdf, wk.LandCoverTable(lct))


def _landcover_to_roughness(gdf, lctable):
    """Converts a landcover to roughness GeoDataFrame.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Geopandas dataframe with the columns 'id_left' and 'id_right'
    lctable: LandCoverTable
        LandCoverTable class with id's, roughnesses, displacements and a description

    Returns
    -------
    gdf: geopandas.GeoDataFrame:
        GeoDataFrame with columns 'z0_left' and 'z0_right'
    """
    if not isinstance(gdf, gpd.GeoDataFrame):
        raise TypeError("This is not a vectormap so can't convert!")

    if not _is_lc(gdf):
        raise TypeError("Can only convert landcover map to a roughness map!")

    # make sure we create a new gdf and don't assign to original
    gdf = gdf[["geometry"]].assign(
        z0_left=[lctable[id]["z0"] for id in gdf.id_left],
        z0_right=[lctable[id]["z0"] for id in gdf.id_right],
    )

    return gdf


def _is_lc(gdf):
    """
    Check if the GeoDataFrame is a landcover map.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame is a landcover map, False otherwise.
    """
    if all([i in gdf.columns for i in VECTORMAP_ID_COLS]):
        return True
    return False


def _is_lmask(gdf):  # pragma: no cover
    """
    Check if the GeoDataFrame is a landmask map.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame is a landmask map, False otherwise.
    """
    if all([i in gdf.columns for i in VECTORMAP_LMASK_COLS]):
        return True
    return False


def _is_z0(gdf):
    """
    Check if the GeoDataFrame is a roughness map.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame is a roughness map, False otherwise.
    """
    if all([i in gdf.columns for i in VECTORMAP_ROU_COLS]):
        return True
    return False


def _is_elev(gdf):
    """
    Check if the GeoDataFrame is an elevation map.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame is an elevation map, False otherwise.
    """
    if VECTORMAP_ELEV_COL in gdf.columns:
        return True
    return False


def _has_inline_lctable(gdf):
    """
    Check if the GeoDataFrame has an inline landcover table.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame has an inline landcover table, False otherwise.
    """
    if all([i in gdf.columns for i in VECTORMAP_INLINE_LCTABLE_COLS]):
        return True
    return False


def _get_map_type(gdf):  # pragma: no cover
    """
    Identify the map type from the GeoDataFrame column names.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    str
        The map type as a string.

    Raises
    ------
    ValueError
        If the map type cannot be identified from the column names.
    """
    if _is_lc(gdf):
        return "landcover"
    elif _is_z0(gdf):
        return "roughness"
    elif _is_elev(gdf):
        return "elevation"
    elif _is_lmask(gdf):
        return "landmask"
    raise ValueError("Unable to identify map_type from column names.")


def _explode_gdf(gdf):
    """
    Explode a GeoDataFrame into single part geometries.

    The explode is needed for converting multipart geometries: wasp only supports
    single part geometries. The reset index is needed so that each single geometry
    has a unique ID.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to be exploded.

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame with single part geometries and reset index.
    """
    if _is_multipart(gdf):
        return gdf.explode(index_parts=True).reset_index(drop=True)
    else:
        return gdf


def _covers_full_bounding_box(gdf):
    """
    Check if the polygons cover the full bounding box enclosing them.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the polygons cover the full bounding box, False otherwise.
    """
    # check that the polygons cover the full bounding box enclosing them
    area1 = box(*gdf.total_bounds).area
    area2 = gdf.geometry.area.sum().item()
    return math.isclose(area1, area2)


def _has_holes(gdf):
    """
    Check if the GeoDataFrame has holes.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame has holes, False otherwise.
    """
    area1 = Polygon(gdf.dissolve().exterior.item()).area
    area2 = gdf.geometry.area.sum().item()
    return not math.isclose(area1, area2)


def _has_overlaps(gdf):
    """
    Check if the GeoDataFrame has overlapping polygons.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame has overlapping polygons, False otherwise.
    """
    # check for overlaps
    area1 = gdf.dissolve().area.item()
    area2 = gdf.area.sum().item()
    return abs(1 - area1 / area2) > 1e-7


def _check_map_columns(gdf):
    """
    Check for required columns in the GeoDataFrame.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame to be checked. Must contain the required columns.

    Raises
    ------
    KeyError
        If the required column 'z0' is missing from the GeoDataFrame.
    """
    # check for required columns
    if "z0" not in gdf.columns:
        raise KeyError(
            "Column 'z0' is missing. You have to specify the `lctable` argument with a wk.LandCoverTable with a mapping from an integer 'id' to 'z0' and optionally 'd'."
        )


def _check_map_errors(gdf, external_roughness=None, lctable=None):
    """
    Check for errors in the map represented by a GeoDataFrame.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame containing the map data. Must have geometry column.
    external_roughness : float or None
        The roughness length to be used for external areas. If None, the function will check for holes in the map.
    lctable : wk.LandCoverTable or None
        The land cover table to be used for the map. If None, the function will check for missing columns.

    Raises
    ------
    ValueError
        If there is no column "z0" and lctable is None
        If there are overlapping polygons in the map.
        If there are holes in the map and `external_roughness` is None.

    Warns
    -----
    UserWarning
        If there are holes in the map and `external_roughness` is provided.

    Notes
    -----
    This function checks for three types of errors in the map:
    1. Overlapping polygons: The area of the dissolved map should be close to the sum of the areas of individual polygons.
    2. Holes in the map: The area of the total extent of the map should be close to the sum of the areas of the polygons.
       If `external_roughness` is provided, holes will get the roughness length specified by `external_roughness`.
    3. Missing columns: The map should have the required column "z0"
    """
    if lctable is None:
        _check_map_columns(gdf)  # check for required columns

    if _has_overlaps(gdf):
        raise ValueError(
            "There is overlapping polygons in your map. The area of the dissolved map is not the same as the sum of the areas of the individual polygons. Please fix these issues using a program like QGIS"
        )

    if _has_holes(gdf):
        if external_roughness is None:
            raise ValueError(
                "There is holes in your map. The area specified by the outer boundary of your polygons (the convex hull) is not the same as the sum of the areas of the polygons. You can fix this by specifying a external roughness length with the `external_roughness` argument, but all the holes in your map will be filled with this roughness value."
            )
        else:
            warnings.warn(
                "There is holes in your map. The area specified by the outer boundary of your polygons (the convex hull) is not the same as the sum of the areas of the polygons. These areas will get the roughness length specified by external_roughness, even though they are not at the edge of the map."
            )


def _is_polygons(gdf):
    """
    Check if the GeoDataFrame contains only Polygons or MultiPolygons.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame contains only Polygons or MultiPolygons, False otherwise.
    """
    return all(["Polygon" in t for t in gdf.geom_type.unique()])


def _is_single_polygons(gdf):
    """
    Check if the GeoDataFrame contains only polygons.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame contains only polygons, False otherwise.
    """
    return all(gdf.geom_type == "Polygon")


def _is_lines(gdf):
    """
    Check if the GeoDataFrame contains only LineString or MultiLineString.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame contains only LineString or MultiLineString, False otherwise.
    """
    return all(["LineString" in t for t in gdf.geom_type.unique()])


def _is_single_lines(gdf):
    """
    Check if the GeoDataFrame contains only LineStrings.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame contains only LineStrings, False otherwise.
    """
    return all(gdf.geom_type == "LineString")


def _is_multipart(gdf):
    """
    Check if the GeoDataFrame has any multipart geometries.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to check.

    Returns
    -------
    bool
        True if the GeoDataFrame has any multipart geometries, False otherwise.
    """
    return any(["Multi" in t for t in gdf.geom_type.unique()])


def _get_vector_map_geometry(gdf):
    """
    Get the geometry of a GeoDataFrame.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to get the geometry from.

    Returns
    -------
    shapely.geometry
        The geometry of the GeoDataFrame.
    """
    if _is_polygons(gdf):
        geom_type = "Polygon"
    if _is_lines(gdf):
        geom_type = "LineString"
    else:
        raise ValueError(
            "The GeoDataFrame contains a mix of geometry types. It is only allowed the have only (Multi)LineStrings or only (Multi)Polygons."
        )

    return geom_type
