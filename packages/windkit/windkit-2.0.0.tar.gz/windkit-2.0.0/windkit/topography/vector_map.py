# (c) 2022 DTU Wind Energy
"""
Readers and writers for vectormap objects.

VectorMaps are defined as collections of linestrings and metadata that represent either
elevations, or the land-cover information. When working with land-cover lines, an
additional LandCoverTable is required to map the land-cover ids to relevant parameters.

Here VectorMaps are represented as geopandas.GeoDataFrame objects. They can be read
from and written to several different formats to support interoperability with different
tools. We recommend using the Geopackage (.gpkg) format if you do not need to use one of
the other formats. For interoperability with WAsP, you should use the .map format for
elevation maps, and .gml for land-cover maps.
"""

__all__ = ["create_vector_map", "add_landcover_table"]

import argparse
import logging
import re
import warnings
from collections import defaultdict
from importlib.metadata import version
from inspect import cleandoc
from pathlib import Path
from typing import Union

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Polygon

from windkit.import_manager import _import_optional_dependency
from windkit.topography.landcover import LandCoverTable
from windkit.topography.map_conversions import lines_to_polygons, polygons_to_lines
from windkit.spatial import crs_are_equal
from windkit.utils import _infer_file_format

from .._errors import UnsupportedFileTypeError
from ._vectormap_gml import _read_vector_map_gml, _write_vectormap_gml
from ._vectormap_helpers import (
    _MAP_TYPE_CODES,
    VECTORMAP_ALT_ELEV_COL,
    VECTORMAP_ELEV_COL,
    VECTORMAP_ID_COLS,
    VECTORMAP_LMASKL_COL,
    VECTORMAP_LMASKR_COL,
    VECTORMAP_META_COLS,
    VECTORMAP_ROU_COLS,
    VECTORMAP_ROUL_COL,
    VECTORMAP_ROUR_COL,
    _check_map_errors,
    _explode_gdf,
    _has_inline_lctable,
    _is_elev,
    _is_lc,
    _is_lines,
    _is_polygons,
    _is_z0,
    _landcover_to_roughness,
    _read_map_file_header_to_epsg_table,
    _roughness_to_landcover,
)

try:
    _import_optional_dependency("pyogrio")
    HAS_PYOGRIO = True
except ImportError:
    HAS_PYOGRIO = False

try:
    _import_optional_dependency("fiona")
    HAS_FIONA = True
except ImportError:
    HAS_FIONA = False

logger = logging.getLogger("__name__")

SUPPORTED_VECTOR_FILE_FORMATS_READ = ["gpkg", "gml", "map", "tmp", "zip", "ZipExtFile"]
SUPPORTED_VECTOR_FILE_FORMATS_WRITE = ["gpkg", "gml", "map"]


def _read_vector_map_combo(filename, crs, map_type):
    """
    Read a .map vector_map file, assuming that both elevation and
    roughness change values are present.

    Parameters
    ----------
    filename : str or pathlib.Path
        File path
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
    map_type: str {elevation, roughness, landmask}
        Which lines to read from the .map

    Returns
    -------
    tuple : (geopandas.GeoDataFrame, (geopandas.GeoDataFrame, LandCoverTable))
        Vectormap as a geodataframe with elevation data
        Vectormap as a geodataframe with landcover data
        LandCoverTable with lookup table for landcover data

    """

    metadata = ""
    n_lines = 0
    n_empty_lines = 0
    got_header_line = False
    current_point_count = 0
    ltype = -999
    n_pts_geom = None

    data = defaultdict(list)

    ###############
    # Setup maptype
    ###############
    # TODO: See about autodetecting map_type
    if map_type is None:
        raise ValueError(
            cleandoc(
                """'map_type' must be provided when reading .map file.
        You can use the read_roughness_map and read_elevation_map convience functions, or
        add a map_type argument."""
            )
        )
    map_type_code = _MAP_TYPE_CODES[map_type]
    if map_type == "landmask":
        map_type_code = _MAP_TYPE_CODES["roughness"]

    #############
    # Handle CRS
    #############
    if crs is None:
        crs = _crs_from_map_file(filename)
        if crs is None:
            raise ValueError("""'crs' cannot be detected from file""")

    with open(filename, "r", newline="\r\n") as fobj:
        # Read 4 header lines into a single string
        for _ in range(4):
            metadata += fobj.readline()

        # Process remaining data
        for line in fobj:
            elements = [float(i) for i in line.strip().split()]

            # Read line header
            if got_header_line is False:
                z0_left, z0_right, elev = np.nan, np.nan, np.nan

                # Check for empty lines
                if (
                    len(elements) == 0
                ):  # pragma: no cover (not sure what this should be)
                    n_pts_geom = 0
                    ltype = -999
                    n_empty_lines += 1

                # Check for list of points with no attributes
                if len(elements) == 1:
                    (n_pts_geom,) = elements
                    ltype = -999
                    n_empty_lines += 1

                # Elevation header row
                if len(elements) == 2:
                    elev, n_pts_geom = elements
                    ltype = 0

                # Roughness header line
                if len(elements) == 3:  # leave out the roughness line
                    z0_left, z0_right, n_pts_geom = elements
                    ltype = 1

                # Combination line
                if len(elements) == 4:
                    z0_left, z0_right, elev, n_pts_geom = elements
                    ltype = 2

                # Combination line with displacement height
                if len(elements) == 5:
                    raise RuntimeError(
                        ".map files with displacement heights are not supported."
                    )

                # Only save data if it is supposed to be output
                if ltype in [map_type_code, 2]:  # ltype=2 is combo line
                    if ltype == 0:
                        data[VECTORMAP_ELEV_COL].append(elev)
                    elif ltype == 1:
                        data[VECTORMAP_ROU_COLS[0]].append(z0_left)
                        data[VECTORMAP_ROU_COLS[1]].append(z0_right)
                    elif ltype == 2:
                        if map_type_code == 1:
                            data[VECTORMAP_ROU_COLS[0]].append(z0_left)
                            data[VECTORMAP_ROU_COLS[1]].append(z0_right)
                        else:
                            data[VECTORMAP_ELEV_COL].append(elev)

                    n_lines += 1

                x_pts = []
                y_pts = []

                got_header_line = True

            # if we have the header and the line is what we want
            # then get all the points.
            else:
                if ltype in [map_type_code, 2]:
                    x_pts += elements[0::2]
                    y_pts += elements[1::2]

                current_point_count += len(elements) / 2

                # After reading all the points for the line,
                # Set the header back to false and reset the point counter
                if current_point_count == n_pts_geom:
                    if ltype in [map_type_code, 2]:
                        geometry = LineString(zip(x_pts, y_pts))
                        data["geometry"].append(geometry)

                    got_header_line = False
                    current_point_count = 0

    if len(data) == 0:
        with open(filename, "r", newline="\r\n") as fobj:
            if len(fobj.readlines()) == 1:
                raise ValueError(
                    "Only a single line detected, make sure your mapfile has 'CRLF' line endings"
                )
        raise ValueError(f"""No '{map_type}' lines found.""")

    gdf = gpd.GeoDataFrame(
        {key: val for key, val in data.items() if len(val) > 0},
        geometry="geometry",
        crs=crs,
    ).dropna(axis=1, how="all")

    if map_type == "landmask":
        gdf = gdf.rename(
            columns={
                VECTORMAP_ROUL_COL: VECTORMAP_LMASKL_COL,
                VECTORMAP_ROUR_COL: VECTORMAP_LMASKR_COL,
            }
        )

    return gdf


def _read_vector_map(
    filename,
    crs=None,
    map_type=None,
    file_format="infer",
    external_roughness=None,
    return_lctable=False,
    convert_to_landcover=False,
    polygons=True,
    check_errors=True,
):
    """
    Read a vector_map from a file.

    Parameters
    ----------
    filename : str or pathlib.Path
        File path
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS` Default reads from file.
    map_type : str
        One of "elevation" or "roughness" to specify the type of map to create.
        Defaults to None.
    file_format: str
        Format of the file. Defaults to "infer", which will try to infer the format from the file extension.
    external_roughness: float, optional.
        This option is used for polygon based landcover files. It sets the roughness
        for all areas not covered by polygons.
    return_lctable: bool
        If True, attempt to read and return a LandCoverTable from the file. Defaults to False.
    convert_to_landcover: bool
        If True when reading a roughness map, convert it to a landcover map and return both the map and the
        lctable. Defaults to False.
    polygons: bool
        Whether to convert the opened file to polygons, default True.
    check_errors: bool
        Whether to check for errors in the map, default True.

    Returns
    -------
    gdf: geopandas.GeoDataFrame
        Vectormap as a geodataframe.
    lc : LandCoverTable, optional
        LandCoverTable optional.
    """
    lctable = None
    if file_format == "infer":
        file_format = _infer_file_format(filename)

    unsupported_file_format_err = f"Unsupported file format: {file_format}. Supported formats are: {SUPPORTED_VECTOR_FILE_FORMATS_READ}"
    if file_format not in SUPPORTED_VECTOR_FILE_FORMATS_READ:
        raise UnsupportedFileTypeError(unsupported_file_format_err)

    if file_format not in ["ZipExtFile"]:
        if not Path(filename).exists():
            raise FileNotFoundError(filename)

    if file_format in ["map", "tmp"]:
        if not polygons and not convert_to_landcover and map_type == "landcover":
            raise ValueError(
                ".map files do not support landcover maps."
                + " If you want to read a roughness map and convert it to a landcover map,"
                + " use the 'convert_to_landcover' argument with 'read_roughness_map'."
            )
        elif map_type == "landcover":
            map_type = "roughness"
        gdf = _read_vector_map_combo(filename, crs=crs, map_type=map_type)
    elif file_format in ["gml"]:
        gdf, lctable = _read_vector_map_gml(filename)
    elif file_format in ["gpkg", "zip", "ZipExtFile"]:
        if HAS_PYOGRIO:
            gdf = gpd.read_file(filename, engine="pyogrio")
        elif HAS_FIONA:
            gdf = gpd.read_file(filename, engine="fiona", driver="GPKG")
        else:
            raise ValueError("No suitable reader found for gpkg vector map.")

    if crs is not None and gdf.crs is not None:
        if not crs_are_equal(gdf.crs, crs):
            raise ValueError(f"Dataset crs {gdf.crs} doesn't match crs argument {crs}.")
        else:
            gdf.crs = crs

    if _is_polygons(gdf):
        if check_errors:
            _check_map_errors(gdf, external_roughness, lctable)
        return gdf

    if _is_elev(gdf):
        gdf = gdf.rename(
            columns={v: VECTORMAP_ELEV_COL for v in VECTORMAP_ALT_ELEV_COL}
        )
        gdf[VECTORMAP_ELEV_COL] = gdf[VECTORMAP_ELEV_COL].astype(float)

    if _is_z0(gdf):
        gdf[list(VECTORMAP_ROU_COLS)] = gdf[list(VECTORMAP_ROU_COLS)].astype(float)
        if not polygons and convert_to_landcover:
            return _roughness_to_landcover(gdf)
        elif polygons:
            gdf, lctable = _roughness_to_landcover(gdf)

    if _is_lc(gdf):
        if (
            lctable is None
        ):  # Requires separate landcover table, either from gpkg or json
            gdf[list(VECTORMAP_ID_COLS)] = gdf[list(VECTORMAP_ID_COLS)].astype(int)

            if not polygons and not return_lctable:
                return gdf

            ###############################################
            # Get landcover table from file if it is there
            ###############################################

            if _has_inline_lctable(gdf):  # Landcover info is from each row of table
                lctable = LandCoverTable(
                    gdf[["id", "d", "z0", "desc"]]
                    .drop_duplicates()
                    .set_index("id")
                    .to_dict(orient="index")
                )
                if not polygons:
                    return gdf, lctable

            if HAS_PYOGRIO:
                layers = gpd.list_layers(filename)["name"].values.tolist()
                if "landcover_table" not in layers:
                    raise ValueError(
                        "Landcover table not found in GeoPackage, cannot return LandCoverTable."
                    )

            try:
                lcdf = gpd.read_file(filename, layer="landcover_table")
                if "index" in lcdf.columns:
                    lcdf = lcdf.rename(columns={"index": "id"})
                    warnings.warn(
                        "The use of the name 'index' to identify landcover ID's in the landcover table is deprecated, please use the name 'id' for this instead.",
                        FutureWarning,
                    )
                lcdf = lcdf.set_index("id")
                lctable = LandCoverTable(
                    lcdf.drop("geometry", axis=1, errors="ignore").transpose().to_dict()
                )
            except ValueError as e:
                raise e

        if not polygons and return_lctable:
            return (gdf, lctable)
        else:
            gdf = lines_to_polygons(gdf)
            gdf = add_landcover_table(gdf, lctable)

    return gdf


def _vector_map_to_mapfile(gdf, filename, description="WindKit", mode="w"):
    """
    Write vector_map in GeoDataFrame format to WAsP mapfile format.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Elevation or roughness change vector_map.
    filename : pathlib.Path or str
        Path to output file.
    description : str
        Description string added to the file (cannot be empty when reading with map editor).
        Defaults to "WindKit"
    mode : str("w" or "a")
        Write or append mode. Defaults to "w".
    """
    if all(c in gdf.columns for c in VECTORMAP_META_COLS):  # pragma: no cover
        raise ValueError(
            cleandoc(
                """Both elevation and roughness values found! combo files are not supported! Please write them separately!"""
            )
        )

    if _is_elev(gdf):
        map_type = "elevation"
    elif _is_z0(gdf):
        map_type = "roughness"
    else:
        raise ValueError(
            "Only elevation and roughness data can be written to mapfile (.map) format."
        )

    if description == "":
        raise ValueError("Description cannot be empty for a .map file.")

    # build mapfile header
    mapeditor_crs_str = _crs_to_map_editor_str(gdf.crs)
    # Parse windkit version
    wk_version = version("windkit")
    ver_regex = r"(\d+)\.(\d+)\.(\d+)|(\d+)\.(\d+)"
    try:
        ver_str = re.match(ver_regex, wk_version, re.IGNORECASE).group()
    except Exception:
        ver_str = ""
    header_str = f"+{description} | {mapeditor_crs_str} | windkit v{ver_str}"

    with open(filename, mode, newline="\r\n") as fobj:
        # File header
        if mode == "w":
            fobj.write(header_str + "\n")
            # Fixed point #1 in user and metric [m] coordinates:
            # X1_user, Y1_user, X1_metric, Y1_metric
            fobj.write("%3.1f %3.1f %3.1f %3.1f\n" % (0.0, 0.0, 0.0, 0.0))

            # Fixed point #2 in user and metric [m] coordinates:
            # X2_user, Y2_user, X2_metric, Y2_metric
            fobj.write("%3.1f %3.1f %3.1f %3.1f\n" % (1.0, 0.0, 1.0, 0.0))

            # Scaling factor and offset for height scale (z),
            # Zmetric = scaling factor X (zuser +offset)
            fobj.write("%3.1f %15.1f\n" % (1.0, 0.0))

        for _, row in gdf.iterrows():
            rg = row.geometry
            x_pts, y_pts = (
                rg.boundary.coords.xy if isinstance(rg, Polygon) else rg.coords.xy
            )
            n_pts = len(x_pts)

            if map_type == "elevation":
                fobj.write(f"{row.elev:10.4f} {n_pts:10d}\n")
            elif map_type == "roughness":
                fobj.write(f"{row.z0_left:10.4f} {row.z0_right:10.4f} {n_pts:10d}\n")
            xy_string = " ".join(f"{x:10.1f} {y:10.1f}" for x, y in zip(x_pts, y_pts))
            fobj.write(xy_string + "\n")


def _vector_map_to_gmlfile(
    gdf, filename, lctable=None, description="Windkit", **kwargs
):
    """
    Write vectormap in GeoDataFrame format to GML format.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Elevation or roughness change vector_map.
    filename : pathlib.Path or str
        Path to output file.
    lctable : LandCoverTable
        Landcover table to map landcover and roughness / displacements. Defaults to None.
    description : str
        Description added to the file (cannot be empty when reading with map editor).
        Defaults to "Windkit"
    kwargs : dict
        Extra arguments.

    """
    _write_vectormap_gml(filename, gdf, lctable, description)


def _vector_map_to_gpdfile(gdf, filename, lctable=None, **kwargs):
    """
    Write vectormap in GeoDataFrame format to GeoPackage format.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Elevation or roughness change vector_map.
    filename : pathlib.Path or str
        Path to output file.
    lctable : LandCoverTable
        Landcover table to map landcover and roughness / displacements. Defaults to None.
    kwargs : dict
        Extra arguments.

    """
    default_geopandas_kwargs = {"driver": "GPKG"}
    kwargs = {**default_geopandas_kwargs, **kwargs}
    if _is_lc(gdf):
        logger.debug("Adding landcover table to GeoPackage output")
        gdf.to_file(str(filename), layer="landcover_lines", **kwargs)
        lct_df = pd.DataFrame.from_dict(lctable, orient="index")
        lct_df["geometry"] = None
        lct_gdf = gpd.GeoDataFrame(lct_df, geometry="geometry")
        return lct_gdf.reset_index().to_file(
            str(filename),
            layer="landcover_table",
            **kwargs,
        )
    else:
        return gdf.to_file(str(filename), **kwargs)


def _force_to_lines(
    gdf, lctable, external_roughness=None, check_errors=True, snap=True
):
    """
    Prepare a roughness GeoDataFrame for processing.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        The GeoDataFrame to prepare.
    lctable : LandCoverTable
        The landcover table to use.
    **kwargs : dict
        Additional arguments.

    Returns
    -------
    tuple
        A tuple containing the prepared GeoDataFrame and the landcover table.
    """
    gdf = _explode_gdf(gdf)
    if _is_polygons(gdf):
        return polygons_to_lines(
            gdf,
            lctable=lctable,
            map_type="landcover",
            return_lctable=True,
            external_roughness=external_roughness,
            check_errors=check_errors,
            snap=snap,
        )
    elif _is_lines(gdf):
        return (gdf, lctable)
    else:
        geom_types = "&".join(gdf.geom_type.unique())
        raise ValueError(
            f"Don't know how to deal with a combination of geometry types {geom_types}"
        )


def _vector_map_to_file(
    gdf,
    filename: Union[Path, str],
    lctable: LandCoverTable = None,
    file_format: str = "infer",
    external_roughness: float = None,
    check_errors: bool = True,
    snap: bool = True,
    polygons: bool = True,
    **kwargs,
):
    """Write a GeoDataFrame vector map to a vectorfile.

    Filetypes are determined from the file extension.
    .map files passed to vector_to_mapfile()
    .gml files are passed to vector_to_gmlfile()
    all others use the geopandas .to_file() method

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        Vector map to write
    filename : pathlib.Path or str
        Path to file to write to.
    lctable : LandCoverTable
        Landcover table to map landcover and roughness / displacements. Defaults to None.
    driver : str
        Name of the Fiona Driver to pass to geopandas.to_file(). Defaults to "GPKG"
    kwargs : dict
        Keyword arguments to pass to writer.
    """
    if file_format == "infer":
        file_format = _infer_file_format(filename)
    else:
        if file_format not in SUPPORTED_VECTOR_FILE_FORMATS_WRITE:
            raise ValueError(f"Unsupported file format: {file_format}")

    if _is_polygons(gdf) and polygons:
        if lctable is not None:
            raise ValueError(
                "Cannot write polygons with a landcover table. Add the landcover table using `windkit.add_landcover_table` first."
            )
        if file_format == "gpkg":
            return _vector_map_to_gpdfile(gdf, filename, **kwargs)

    gdf, lctable = _force_to_lines(
        gdf,
        lctable,
        external_roughness=external_roughness,
        check_errors=check_errors,
        snap=snap,
    )

    if not (_is_elev(gdf) or _is_lc(gdf) or _is_z0(gdf)):
        raise ValueError(
            "Only elevation, landcover, and roughness maps can be written to file."
        )

    if _is_lc(gdf):
        if lctable is None:
            raise ValueError("'lctable' not specified for landcover map")
        if file_format == "map":
            gdf = _landcover_to_roughness(gdf, lctable=lctable)
            if any([v["d"] > 0 for _, v in lctable.items()]):
                raise ValueError(
                    "Cannot write displacement heights to .map file. Use the .gpkg or .gml extension instead!"
                )

    if file_format == "map":
        return _vector_map_to_mapfile(gdf, filename, **kwargs)
    elif file_format == "gml":
        return _vector_map_to_gmlfile(gdf, filename, lctable=lctable, **kwargs)
    elif file_format == "gpkg":
        return _vector_map_to_gpdfile(gdf, filename, lctable=lctable, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def create_vector_map(
    bbox, map_type="elevation", elevation=0.0, roughness_change=(0.0, 0.0)
):
    """
    Create a square elevation or roughness map within the specified bounding box.

    Parameters
    ----------
    bbox : wk.spatial.BBox
        Bounding box to use for setting the boundary.
    map_type : str
        One of "elevation" or "roughness" to specify the type of map to create. Defaults
        to "elevation".
    elevation : float
        Elevation to set the line to if it is an elevation map. Defaults to 0.0.
    roughness_change : tuple of 2 floats
        Roughness values for the line describing what is inside (first element) and outside the line (second element). Defaults to (0.0,0.0).

    Returns
    -------
    vector_map: geopandas.GeoDataFrame
        Flat vector_map
    """
    minx, miny, maxx, maxy = bbox.bounds()

    z0_left, z0_right = roughness_change

    data = defaultdict(list)

    if map_type == "elevation":
        data[VECTORMAP_ELEV_COL].append(elevation)
    elif map_type in ["roughness", "landcover"]:
        data[VECTORMAP_ROUL_COL].append(z0_left)
        data[VECTORMAP_ROUR_COL].append(z0_right)

    geometry = LineString(
        [
            (minx, miny),
            (maxx, miny),
            (maxx, maxy),
            (minx, maxy),
            (minx, miny),
        ]
    )

    data["geometry"].append(geometry)
    gdf = gpd.GeoDataFrame(data, geometry="geometry", crs=bbox.crs)

    if map_type in ["elevation", "roughness"]:
        return gdf
    elif map_type in ["landcover"]:
        return _roughness_to_landcover(gdf)
    else:
        raise ValueError(f"Unsupported map type: {map_type}")


def _split_combo_parser():
    """
    Parser for the split_combo command line tool
    """
    p = argparse.ArgumentParser(
        description="Split a combo mapfile into elevation and roughness GML files."
    )
    p.add_argument("inputfile", help="File to split")
    p.add_argument(
        "crs", help="Projection of the map, can be an epsg code, proj4 string, or wkt"
    )

    return p


def _split_combo():
    """
    Split a combo mapfile into elevation and roughness files.

    The roughness and elevation files have the same name as the
    input file, but with _elev or _rou added at the end.
    """
    p = _split_combo_parser()
    args = p.parse_args()

    inputfile = args.inputfile
    try:
        crs = int(args.crs)
    except ValueError:
        crs = args.crs

    # Roughness
    lc_map, lc_table = _read_vector_map(
        inputfile, crs, map_type="roughness", convert_to_landcover=True, polygons=False
    )
    _vector_map_to_file(lc_map, inputfile[:-4] + "_landcover.gpkg", lc_table)

    # Elevation
    elev = _read_vector_map(inputfile, crs, map_type="elevation")
    _vector_map_to_file(elev, inputfile[:-4] + "_elevation.gpkg")


def _crs_from_map_file(filename):
    """
    Gets crs/epsg from .map file

    Parameters
    ----------
    filename : pathlib.Path or str
        Path to .map file

    Returns
    -------
    crs: int
        Integer representing EPSG zone
    """
    if Path(filename).suffix == ".gml":
        gdf = gpd.read_file(filename, driver="GML", layer="ChangeLine")
        crs = gdf.crs.to_epsg()
    else:
        f = open(filename, "r", newline="\r\n")
        header = f.readline()
        f.close()

        epsg_lookup_table = _read_map_file_header_to_epsg_table(mode="r")

        crs = None
        for string, epsg in epsg_lookup_table.items():
            if string in header:
                crs = epsg
                break

    return crs


def _crs_to_map_editor_str(crs):
    """
    Returns a CRS string with the map editor format
    to write in a .map file header

    Parameters
    ----------
    crs: pyproj.CRS.crs
        crs object to transform
    Returns
    -------
    crs_str : str
        String with the .map header format
    """
    epsg_lookup_table = _read_map_file_header_to_epsg_table(mode="w")

    crs_str_lookup_table = {v: k for k, v in epsg_lookup_table.items()}
    for k, v in crs_str_lookup_table.items():
        if crs_are_equal(k, crs):
            return v
    return ""


def add_landcover_table(gdf, lctable):
    """
    Add a landcover table to a GeoDataFrame.

    This function adds a landcover table to a GeoDataFrame containing polygon geometries.
    It ensures that all IDs in the GeoDataFrame are present in the landcover table.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame to which the landcover table will be added. Must contain polygon geometries.
    lctable : dict
        A dictionary representing the landcover table. The keys should be IDs corresponding to the IDs in the GeoDataFrame.

    Returns
    -------
    GeoDataFrame
        The original GeoDataFrame with the landcover table joined on the 'id' column.

    Raises
    ------
    ValueError
        If the GeoDataFrame contains non-polygon geometries or if any IDs in the GeoDataFrame are not present in the landcover table.
    """
    if not _is_polygons(gdf):
        raise ValueError("Can only add a landcover table to a polygon map")

    df_lct = gpd.GeoDataFrame.from_dict(lctable).T.astype(
        {"z0": float, "d": float, "desc": str}
    )

    id_is_present = [i in df_lct.index for i in gdf["id"].unique()]
    if not all(id_is_present):
        ids_not_present = ",".join(
            gdf["id"].unique()[np.invert(id_is_present)].astype(str)
        )
        raise ValueError(f"id '{ids_not_present}' not present in the landcover table")

    return gdf.set_index("id").join(df_lct).reset_index(names="id")
