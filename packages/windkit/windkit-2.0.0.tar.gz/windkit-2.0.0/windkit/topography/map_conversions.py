__all__ = [
    "lines_to_polygons",
    "polygons_to_lines",
    "snap_to_layer",
    "check_dead_ends",
    "check_lines_cross",
]

import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import get_point
from shapely.geometry import LineString, Point, box

from ._vectormap_helpers import (
    _LR_COLS,
    _check_map_columns,
    _check_map_errors,
    _explode_gdf,
    _get_map_type,
    _landcover_to_roughness,
)


def _detect_z0_external(polygons, line_segments, output_name, col_names):
    """
    Detects the z0 external from polygon and the line segments derived from it

    Parameters
    ----------
    polygons : geopandas.GeoDataFrame
        A GeoDataFrame containing line geometries.
    line_segments : geopandas.GeoDataFrame
        A GeoDataFrame containing line geometries
    output_name: str
        Name of output column
    col_names: tuple
        colnames denoting the change-line properties of the line (e.g z0_left,
        z0_right or id_left, id_right)

    Returns
    -------
    z0_ext: float
        Float of the external polygon surrounding all polygons
    """
    # get feature which contains the nan
    na_feature = polygons[polygons[output_name].isna()]

    # select the first interior ring from this feature
    first_interior = (
        gpd.GeoDataFrame(
            geometry=[[na for na in na_feature.interiors if na][-1][0]],
            crs=polygons.crs,
        )
        .sjoin(line_segments)
        .dropna()
    )
    # find the z0 external from the line segment
    z0_ext = (
        first_interior[col_names[1]]
        .where(line_segments["lines_same_dir"], line_segments[col_names[0]])
        .iloc[0]
    )

    return z0_ext


def check_lines_cross(lines_out, errors="raise", add_errors=False):
    """
    Detects and handles crossing line geometries in a GeoDataFrame.

    This function identifies line geometries that cross each other in the input GeoDataFrame.
    It can raise an error, issue a warning, or add a boolean column indicating crossing lines.

    Parameters
    ----------
    lines_out : geopandas.GeoDataFrame
        A GeoDataFrame containing line geometries to check for crossings.
    errors : {"raise", "warn", "ignore"}, optional
        Specifies how to handle detected crossings:
        - "raise": Raises a 'ValueError' if crossings are found.
        - "warn": Issues a warning if crossings are found.
        - "ignore": Does nothing.
        Default is "raise".
    add_errors : bool, optional
        If True, adds a boolean column named "crosses" to the input GeoDataFrame,
        indicating whether each line crosses another line. Default is True.

    Returns
    -------
    geopandas.GeoDataFrame
        The input GeoDataFrame with an optional "crosses" column added if 'add_errors' is True.

    Raises
    ------
    ValueError
        If 'errors' is set to "raise" and crossing lines are detected.

    Warns
    -----
    UserWarning
        If 'errors' is set to "warn" and crossing lines are detected.

    Notes
    -----
    - The function first uses a spatial join to detect crossings. If crossings are found,
      it performs a more precise check by splitting the lines into segments and rechecking
      for overlaps.
    - This secondary check is slower and is only performed if crossings are initially detected.

    Examples
    --------
    >>> import geopandas as gpd
    >>> from shapely.geometry import LineString
    >>> lines = gpd.GeoDataFrame({
    ...     "geometry": [LineString([(0, 0), (1, 1)]), LineString([(0, 1), (1, 0)])]
    ... })
    >>> check_lines_cross(lines, errors="warn")
    GeoDataFrame with a "crosses" column indicating crossing lines.
    """
    # remove any existing columns so we don't get duplicate column names when doing sjoin
    lines_out = lines_out.drop(columns=["crosses"], errors="ignore")

    crosses = lines_out[["geometry"]].sjoin(lines_out, predicate="crosses")
    crosses = crosses.drop_duplicates(subset=["geometry"])
    crosses["crosses"] = 1
    if crosses.shape[0] > 0:
        # this part is because two linestring that share one point
        # somehow can be labelled as crossing, perhaps due precision issues
        # here we split them up in seperate segments and check the overlaps
        # between those, which detects the true overlaps.
        # this is much slower then the sjoin statement above, so we only do
        # this in case there is any reported crossings.
        crosses_double_check = (
            crosses[["geometry"]]
            .overlay(crosses, keep_geom_type=True)
            .explode()
            .drop(columns="index_right")
        )
        true_cross = crosses_double_check[["geometry"]].sjoin(
            crosses_double_check, predicate="crosses"
        )
        crosses_double_check["crosses"] = 0
        crosses_double_check.loc[true_cross.index.unique(), "crosses"] = 1
        crosses_double_check = crosses_double_check[
            ~crosses_double_check.index.duplicated(keep="first")
        ]
        crosses["crosses"] = crosses_double_check["crosses"].values

    cross_series = crosses["crosses"].reindex(lines_out.index).fillna(0).astype(bool)

    cross_lines = ",".join(crosses["crosses"].index.astype(str))
    contains_errors = cross_series.any()
    if errors == "raise" and contains_errors:
        raise ValueError(
            f"Lines with index {cross_lines} are crossing each other in your map. Please fix these in a program like QGIS."
        )
    elif errors == "warn" and contains_errors:
        warnings.warn(
            f"Lines with index {cross_lines} are crossing each other in your map."
        )

    if add_errors:
        lines_out["crosses"] = cross_series

    return lines_out


def check_dead_ends(lines_out, errors="raise", add_errors=False):
    """
    Detects dead ends in a given set of lines.

    This function checks for dead ends in the provided GeoDataFrame of lines.
    A dead end is defined as a point where only one line segment ends or starts.

    Parameters
    ----------
    lines_out : GeoDataFrame
        A GeoDataFrame containing the line geometries to be checked for dead ends.
    errors : {"raise", "warn", "ignore"}, optional
        Specifies how to handle detected crossings:
        - "raise": Raises a `ValueError` if crossings are found.
        - "warn": Issues a warning if crossings are found.
        - "ignore": Does nothing.
        Default is "raise".
    add_errors : bool, optional
        If True, adds a boolean column named "crosses" to the input GeoDataFrame,
        indicating whether each line crosses another line. Default is True.

    Returns
    -------
    geopandas.GeoDataFrame
        The input GeoDataFrame with an optional "crosses" column added if 'add_errors' is True.

    Raises
    ------
    ValueError
        If 'errors' is set to "raise" and crossing lines are detected.

    Warns
    -----
    UserWarning
        If 'errors' is set to "warn" and crossing lines are detected.
    """
    # remove any existing columns so we don't get duplicate columnname when doing sjoin
    lines_out = lines_out.drop(columns=["nr_overlaps", "dead_end"], errors="ignore")
    end_points = gpd.GeoDataFrame(
        geometry=get_point(lines_out.geometry, -1),
        crs=lines_out.crs,
    )
    start_points = gpd.GeoDataFrame(
        geometry=get_point(lines_out.geometry, 0),
        crs=lines_out.crs,
    )
    points = pd.concat([start_points, end_points], ignore_index=True)
    points["nr_overlaps"] = np.bincount(
        points.sjoin(points, predicate="contains").index_right
    )
    points["dead_end"] = points["nr_overlaps"] == 1

    nr_dead_ends = points["dead_end"].astype(int).sum()
    contains_errors = points["dead_end"].any()
    if errors == "raise" and contains_errors:
        raise ValueError(
            f"Your map contains {nr_dead_ends} dead ends, please fix these in a program like QGIS. You can set the arguments errors to 'ignore' to ignore this error and get a column 'dead_end' which denotes where the problems occur."
        )
    elif errors == "warn" and contains_errors:
        warnings.warn(
            f"Your map contains {nr_dead_ends} dead ends, please fix these in a program like QGIS. You can set the arguments 'add_errors' to get a boolean column 'dead_end' which denotes which lines contains dead ends."
        )

    if add_errors:
        res = lines_out.sjoin(points)
        lines_out["dead_end"] = False
        lines_out.loc[res[res["dead_end"]].index, "dead_end"] = True

    return lines_out


def lines_to_polygons(lines, check_errors=False):
    """
    Converts a GeoDataFrame of lines into polygons.

    This function takes a GeoDataFrame containing line geometries and converts
    them into polygons. The resulting polygons are
    associated with attributes from the input lines.

    Parameters
    ----------
    lines : geopandas.GeoDataFrame
        A GeoDataFrame containing line geometries. The GeoDataFrame must have
        columns corresponding to the change lines type (e.g., z0_left, z0_right for
        roughness, id_left, id_right for landcover).
    check_errors: bool
        Check the input line map for errors, Default False

    Returns
    -------
    geopandas.GeoDataFrame
        A GeoDataFrame containing polygon geometries with associated attributes
        from the input lines.

    Raises
    ------
    ValueError
        If landcover could not be found for all created polygons due to issues
        in the input geometries.

    Warnings
    --------
    UserWarning
        If landcover could not be found for all created polygons, indicating
        potential issues in the input geometries such as dangles or unexpected
        geometries.

    Notes
    -----
    - The function creates outer boundary polygons to ensure complete coverage.
    - It uses spatial joins to associate attributes from the input lines with
      the resulting polygons.
    - The function assumes that the input lines are valid and do not contain
      invalid geometries.
    """
    if check_errors:
        _ = check_dead_ends(lines, errors="raise")
        _ = check_lines_cross(lines, errors="raise")

    map_type = _get_map_type(lines)  # get map type
    col_names = list(_LR_COLS[map_type])  # get column names of such a map type
    output_name = col_names[0].split("_")[
        0
    ]  # get name without the left and right identifiers

    # create outer boundary of all lines to also create outer polygons
    lines_ext = gpd.GeoDataFrame(
        {col_names[0]: np.nan, col_names[1]: np.nan},  # these are not used
        geometry=[box(*lines.total_bounds).boundary],
        index=[0],
        crs=lines.crs,
    )
    # paste together normal lines and outer boundary line
    lines_out = pd.concat([lines, lines_ext], ignore_index=True)

    # make sure that all lines are split when they meet another line
    planar_graph = gpd.GeoDataFrame(
        geometry=[lines_out.geometry.union_all()], crs=lines.crs
    ).explode()
    lines_out = (
        lines_out.sjoin(planar_graph, how="right", predicate="contains")
        .reset_index()
        .drop(columns=["index_left", "index"], errors="ignore")
    )
    lines_out = lines_out.drop_duplicates("geometry")

    # convert all lines into polygons and drop invalid ones
    polygons = gpd.GeoDataFrame(geometry=lines_out.polygonize(node=False))

    # select only first two points of each lines that form the output polygon
    segments_lines = gpd.GeoDataFrame(
        geometry=[
            LineString([p1, p2])
            for p1, p2 in zip(
                get_point(polygons.exterior.geometry, 0),
                get_point(polygons.exterior.geometry, 1),
            )
        ],
        crs=lines.crs,
    )

    # spatial join on the original lines that contain the segments
    fpsi = (
        lines_out.sjoin(segments_lines, predicate="contains")
        .set_index("index_right")
        .sort_index()
    )
    fpsi["geometry"] = [
        LineString([p1, p2])
        for p1, p2 in zip(get_point(fpsi.geometry, 0), get_point(fpsi.geometry, 1))
    ]

    # find out if the line segment are oriented in the same direction or not
    fpsi["lines_same_dir"] = segments_lines.frechet_distance(fpsi) > 0
    # the correct ID of the polygon is on the left if the segments have
    # the same direction otherwise on the right
    fpsi[output_name] = fpsi[col_names[0]].where(
        fpsi["lines_same_dir"], fpsi[col_names[1]]
    )
    # join polygons with results from matching segments
    polygons = polygons.join(fpsi[[output_name]])[["geometry", output_name]]

    # if there is any nan's left it must mean they come from the outer boundary
    # so we fill them by selecting a interior ring, finding a line segment that
    # is on that interior ring and finding the z0 from the external side of
    # that polygon
    if polygons[output_name].isna().any():
        nr_nans = polygons[output_name].isna().sum()
        warnings.warn(
            f"""Landcover could not be found for {nr_nans} polygons! These
            will be filled with the external roughness of a random interior
            ring. Check your map in a program like QGIS and make sure that
            there is no dangles, overlapping lines and other unexpected
            geometries"""
        )
        z0_ext = _detect_z0_external(polygons, fpsi, output_name, col_names)
        polygons[output_name] = polygons[output_name].fillna(z0_ext)

    return polygons


def _is_clockwise(points):
    """
    Determine if a ring of points is oriented clockwise.

    This function calculates the signed area enclosed by a ring of points
    using a linear time algorithm. A negative value indicates a clockwise
    orientation, while a value >= 0 indicates a counter-clockwise orientation.

    Parameters
    ----------
    points : list of tuple
        A list of (x, y) coordinate tuples representing the ring of points.

    Returns
    -------
    bool
        True if the ring is oriented clockwise, False otherwise.

    Notes
    -----
    The algorithm is based on the formula for the signed area of a polygon:
    http://www.cgafaq.info/wiki/Polygon_Area
    """
    xs, ys = map(list, zip(*points))
    xs.append(xs[1])
    ys.append(ys[1])
    return sum(xs[i] * (ys[i + 1] - ys[i - 1]) for i in range(1, len(points))) / 2.0 < 0


def _process_segments(segments, line, j, index, external_roughness):
    """
    Process line segments and update segment information.

    Parameters
    ----------
    segments : dict
        A dictionary where keys are segment tuples and values are dictionaries containing segment information.
    line : list of tuples
        A list of coordinate tuples representing the line to be processed.
    j : int
        An integer representing the current segment index.
    index : int
        The index to be assigned to the left side of the segment.
    external_roughness : int
        The background roughness length identifier.

    Returns
    -------
    tuple
        A tuple containing the updated segments dictionary and the updated segment index.

    Notes
    -----
    This function processes each segment of the line, updating the segment information in the 'segments' dictionary.
    It checks for existing segments and updates their left or right identifiers based on the 'external_roughness'.
    If a segment does not exist, it adds a new entry to the 'segments' dictionary.
    """
    for i in range(len(line) - 1):
        lsegment = (
            (line[i][0], line[i][1]),
            (line[i + 1][0], line[i + 1][1]),
        )
        rsegment = (
            (line[i + 1][0], line[i + 1][1]),
            (line[i][0], line[i][1]),
        )
        z0id = index
        if lsegment in segments:
            if segments[lsegment]["id_left"] == external_roughness:
                segments[lsegment]["id_left"] = z0id
            elif segments[lsegment]["id_right"] == external_roughness:
                segments[lsegment]["id_right"] = z0id
        elif rsegment in segments:
            if segments[rsegment]["id_left"] == external_roughness:
                segments[rsegment]["id_left"] = z0id
            elif segments[rsegment]["id_right"] == external_roughness:
                segments[rsegment]["id_right"] = z0id
        else:
            segments[lsegment] = {
                "id_left": z0id,
                "id_right": external_roughness,
                "fid": j,
            }
        j += 1
    return (segments, j)


def _create_lctable_from_gdf(gdf, lctable=None):
    """
    Create a land cover table from a GeoDataFrame.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame containing land cover data. Must have at least a "z0" column.
    lctable : windkit.LandCoverTable or None
        Landcover table specifying the landcover classes and their mappings to
        roughness and displacement height. Required for 'landcover' maps that
        only have an 'id' column. The default is None, which means that there
        is a 'z0' column in the dataframe that specifies the roughness length.
        The returned lctable is in that case made up of the unique ("z0","d")
        pairs in the gdf.

    Returns
    -------
    lctable : windkit.LandCoverTable
        A dictionary representing the new land cover table.

    Notes
    -----
    If 'lctable' is provided, it will be copied to ensure the original is not modified.
    If 'lctable' is None, the function will check for required columns in 'gdf' and create
    a new land cover table from unique pairs of "z0" and "d" values.
    """
    if lctable is not None:
        # make sure that we don't modify the original landcover table by copying
        # this also ensure that the landcovertable has the required columns z0,d,desc
        lctable_new = lctable.copy()
        # this is what it should be but couldn't import due to a circular import
        # I have made an issue about this here:
        # https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/-/issues/639
        # lctnew = LandCoverTable(lctable.copy())
    else:
        _check_map_columns(gdf)  # check the the gdf has at least a "z0" column

        if "d" not in gdf.columns:
            gdf["d"] = 0.0

        if "desc" not in gdf.columns:
            gdf["desc"] = ""

        # create landcover table from unique pairs of z0/d
        id_cols = ["z0", "d", "id"] if "id" in gdf.columns else ["z0", "d"]
        unique_z0d = gdf.set_index(id_cols)
        unique_z0d = unique_z0d[~unique_z0d.index.duplicated(keep="first")]
        unique_z0d = unique_z0d.drop(columns="geometry", errors="i")
        if "id" not in unique_z0d.columns and "id" not in unique_z0d.index.names:
            unique_z0d["id"] = range(unique_z0d.index.drop_duplicates().size)
        unique_z0d = unique_z0d.reset_index().set_index("id")
        lctable_new = unique_z0d.T.to_dict()

    return lctable_new


def _preprocess_polygon_gdf(gdf, lctable, external_roughness, check_errors):
    """
    Preprocess a GeoDataFrame of polygons for conversion to line segments.

    This function prepares a GeoDataFrame containing polygon geometries for
    conversion into line segments. It ensures that the input data is valid,
    creates a landcover table if not provided, and checks for errors in the
    geometries.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing polygon geometries. Must have at least a 'z0'
        column. If a landcover table is not provided, the GeoDataFrame can also
        contain a 'd' column for displacement height and a 'desc' column for
        descriptions of the landcover.
    lctable : windkit.LandCoverTable or None
        A landcover table specifying the mapping of landcover classes to
        roughness and displacement height. If None, a new landcover table is
        created from the unique ('z0', 'd') pairs in the GeoDataFrame.
    external_roughness : float or None
        The roughness value to assign to areas outside the polygons. If None,
        segments bordering unspecified areas are removed.
    check_errors : bool
        Whether to check for errors in the map. If True, the following checks
        are performed:
        1) No polygons are allowed to overlap.
        2) If 'external_roughness' is None, the bounding box of the polygons
           must not contain holes.
        3) If 'external_roughness' is a float, a warning is issued if there are
           holes in the polygons.

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame with LineString geometries and columns 'id_left' and
        'id_right'.
    lctable : windkit.LandCoverTable
        A landcover table containing the mapping of 'id_left' and 'id_right' to
        roughness length ('z0'), displacement height ('d'), and a description
        ('desc').
    unique_z0d : pandas.DataFrame
        A DataFrame containing unique ('z0', 'd') pairs and their corresponding
        IDs.
    newidx : int
        The ID assigned to the external roughness class, if applicable.

    Raises
    ------
    KeyError
        If there are duplicate ('z0', 'd') pairs with different IDs in the
        landcover table.
    ValueError
        If the GeoDataFrame contains invalid geometries or fails the error
        checks.

    Notes
    -----
    - This function ensures that only polygons (not multipolygons) are
      processed by exploding the GeoDataFrame.
    - If 'external_roughness' is specified, an additional landcover class is
      added to the landcover table for areas outside the polygons.
    """
    # only work with polygons not multipolygons
    gdf = _explode_gdf(gdf)

    # create landcover table if not specified
    lctable = _create_lctable_from_gdf(gdf, lctable)

    # check for errors in the geometries
    if check_errors:
        _check_map_errors(gdf, external_roughness=external_roughness, lctable=lctable)

    df = gpd.GeoDataFrame.from_dict(lctable).T
    df.index.name = "id"

    # find maximum possible land cover id we can use and extra landcover
    # class in case in case external_roughness has been specified
    newidx = int(df.index.max()) + 1  # new ID for external roughness
    lctable[newidx] = {
        "z0": 0.03 if external_roughness is None else external_roughness,
        "d": 0.0,
        "desc": "Roughness length beyond last line",
    }

    unique_z0d = df.reset_index().set_index(["z0", "d"])
    nonunique = unique_z0d.groupby(["id"]).count() > 1
    if any(nonunique.values.ravel()):
        wrong_id = nonunique[nonunique].index.values
        raise KeyError(
            f"Key {','.join(wrong_id.astype(str))} has more than one z0/d pair connected to it. Each combination of (z0,d) must have an unique id!"
        )

    if "id" not in gdf.columns:
        if "d" not in gdf.columns:
            gdf["d"] = 0.0
        gdf = gdf.drop(columns="desc", errors="ignore")
        gdf = gdf.set_index(["z0", "d"]).join(unique_z0d)
        gdf = gdf.reset_index()

    return gdf, lctable, unique_z0d, newidx


def polygons_to_lines(
    gdf,
    lctable=None,
    map_type="roughness",
    return_lctable=False,
    external_roughness=None,
    check_errors=True,
    snap=True,
):
    """
    Convert a GeoDataFrame of polygons into line segments.

    This function processes a GeoDataFrame containing polygon geometries and
    converts them into line segments. It ensures that the input data is valid,
    optionally snaps geometries to align vertices, and creates a landcover
    table if not provided.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame containing polygon geometries. Must have at least a 'z0'
        column. If a landcover table is not provided, the GeoDataFrame can also
        contain a 'd' column for displacement height and a 'desc' column for
        descriptions of the landcover.
    lctable : windkit.LandCoverTable or None, optional
        A landcover table specifying the mapping of landcover classes to
        roughness and displacement height. If None, a new landcover table is
        created from the unique ('z0', 'd') pairs in the GeoDataFrame.
    map_type : {"roughness","landcover"}
        Whether the output is a geopandas dataframe with roughness (z0) or id change lines, default "roughness".
    return_lctable: bool
        Whether to return the landcover table, default False
    external_roughness : float or None, optional
        The roughness value to assign to areas outside the polygons. If None,
        segments bordering unspecified areas are removed.
    check_errors : bool, optional
        Whether to check for errors in the map. If True, the following checks
        are performed:
        1) No polygons are allowed to overlap.
        2) If 'external_roughness' is None, the bounding box of the polygons must not contain holes.
        3) If 'external_roughness' is a float, a warning is issued if there are holes in the polygons.
    snap : bool, optional
        If True, inserts extra vertices to align polygons that touch but do not
        share vertices. Default is True.

    Returns
    -------
    gdf : geopandas.GeoDataFrame
        A GeoDataFrame with LineString geometries and columns 'id_left' and
        'id_right'.
    lctable : windkit.LandCoverTable
        A landcover table containing the mapping of 'id_left' and 'id_right' to
        roughness length ('z0'), displacement height ('d'), and a description
        ('desc').

    Raises
    ------
    ValueError
        If no line segments remain after processing or if the GeoDataFrame
        contains invalid geometries.
    KeyError
        If there are duplicate ('z0', 'd') pairs with different IDs in the
        landcover table.

    Notes
    -----
    - This function is heavily inspired by the code available in the QGIS
      plugin where a similar conversion is performed.
    - If 'external_roughness' is specified, an additional landcover class is
      added to the landcover table for areas outside the polygons.
    - Identical functionality written in Fortran is available in the WAsP core
      at Rvea0287/poly2lines.f90, which is faster than this implementation.
    """

    # if we have a single polygon, we can just write a single line with
    # roughness length outside the same as inside, so we are still able to
    # retain a single feature in our map without any errors
    if gdf.geometry.size == 1:
        external_roughness = gdf["z0"].item()

    doclipping = True if external_roughness is None else False
    gdf, lctable, unique_z0d, newidx = _preprocess_polygon_gdf(
        gdf,
        lctable=lctable,
        external_roughness=external_roughness,
        check_errors=check_errors,
    )

    if snap:
        gdf = snap_to_layer(gdf)

    # note: identical code that is written in fortran is available in the
    # WAsP core at Rvea0287/poly2lines.f90. This is much faster then below.
    if gdf.geometry.size != 1:
        external_roughness = -999

    segments = {}  # initialize dictionairy with segment
    j = 0
    for i, feat in gdf.iterrows():
        poly = feat["geometry"]
        # use id if it is there, otherwise lookup the id in the table with unique z0/d in the index
        index = (
            feat["id"]
            if "id" in feat.keys()
            else unique_z0d.loc[(feat["z0"], feat["d"])]["id"]
        )

        # check if the line is clockwise or counterclockwise
        is_cw = _is_clockwise(poly.exterior.coords)
        if not is_cw:
            xy_ext = poly.exterior.coords
        else:
            xy_ext = poly.exterior.coords[::-1]
        # break the polygons into segments to find out was on the left or right side of the line
        segments, j = _process_segments(segments, xy_ext, j, index, external_roughness)
        for sline in poly.interiors:
            is_cw = _is_clockwise(sline.coords)
            if not is_cw:
                tros = sline.coords[::-1]
            else:
                tros = sline.coords
            segments, j = _process_segments(
                segments, tros, j, index, external_roughness
            )

    # create features
    feats = {}
    for i, segment in enumerate(segments):
        if (
            segments[segment]["id_left"] == external_roughness
            or segments[segment]["id_right"] == external_roughness
        ):
            # if we want roughness change after lines that are on the edge of
            # our domain we overwrite the -999 values.
            if doclipping:
                if (
                    segments[segment]["id_left"] == external_roughness
                    or segments[segment]["id_right"] == external_roughness
                ):
                    continue
            else:
                if segments[segment]["id_left"] == external_roughness:
                    segments[segment]["id_left"] = newidx
                if segments[segment]["id_right"] == external_roughness:
                    segments[segment]["id_right"] = newidx

        vertices = [
            Point(segment[0][0], segment[0][1]),
            Point(segment[1][0], segment[1][1]),
        ]
        fid = segments[segment]["fid"]
        idl = segments[segment]["id_left"]
        idr = segments[segment]["id_right"]

        feats[fid] = {
            "x1": segment[0][0],
            "y1": segment[0][1],
            "x2": segment[1][0],
            "y2": segment[1][1],
            "id_left": idl,
            "id_right": idr,
            "geometry": LineString(vertices),
        }

    if len(feats) == 0:
        raise ValueError(
            f"No roughness changes lines left after processing {len(gdf)} features, because the roughness on both sides of the lines was equal"
        )

    gdf_out = gpd.GeoDataFrame.from_dict(feats, orient="index")
    gdf_out = gdf_out.set_geometry("geometry").set_crs(gdf.crs)
    gdf_out = gdf_out.dissolve(by=["id_left", "id_right"])
    gdf_out = gdf_out.line_merge()
    gdf_out = gdf_out.reset_index(name="geometry").explode()
    gdf_out["geometry"] = gdf_out["geometry"].make_valid()
    gdf_out = _explode_gdf(gdf_out).reset_index().drop(columns="index")

    if map_type == "roughness":
        if (unique_z0d.reset_index()["d"] > 0).any():
            raise ValueError(
                "You map contains displacement heights. This information will be lost when map_type='roughness', use map_type='landcover' to keep this information"
            )
        if return_lctable:
            raise ValueError(
                "Cannot return a landcover table when using map_type='roughness', use map_type='landcover' instead if you want to obtain the landcover table."
            )
        return _landcover_to_roughness(gdf_out, lctable)
    else:
        if return_lctable:
            return (gdf_out, lctable)
        else:
            return gdf_out


def snap_to_layer(gdf, tolerance=0.1):
    """
    Snaps the geometries in a GeoDataFrame to each other within a specified tolerance.

    This function iterates over each geometry in the GeoDataFrame. For each geometry,
    it finds all other geometries that intersect it. It then snaps the geometry to each
    of the intersecting geometries within the specified tolerance.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        The GeoDataFrame containing the geometries to snap. The GeoDataFrame should
        contain a 'geometry' column with polygons.
    tolerance : float, optional
        The tolerance within which to snap geometries, by default 10. This is the maximum
        distance that points can be moved in order to snap them to another geometry.

    Returns
    -------
    GeoDataFrame
        The GeoDataFrame with the snapped geometries.

    """
    gdf = gdf.copy()  # avoid columns created below showing up in the output
    if gdf.crs is not None:
        if gdf.crs.is_geographic and tolerance >= 0.1:
            warnings.warn(
                "Your map is in a geographic coordinates so the tolerance argument is likely to large. Adapt it to a (smaller) number in the map units (degrees).",
            )

    if not all(gdf.is_valid):
        raise ValueError(
            "You have invalid geometries in your vector map. You can try to fix them by replacing the geometry with gdf.geometry.make_valid()"
        )

    # we add the number of points as meta data for checking polygons that have changed after snapping
    gdf["npoints"] = [
        len(row.geometry.exterior.coords)
        + sum([len(i.coords) for i in row.geometry.interiors])
        for i, row in gdf.iterrows()
    ]
    gdf["done"] = False  # set done to false, because none have been processed yet
    sum_vertices_old = -1

    while gdf["npoints"].sum() != sum_vertices_old:
        sum_vertices_old = gdf["npoints"].sum()
        # using spatial join using sjoin is much faster than looping over all items to find intersecting geometries
        gdf_intersects = gdf.sjoin(gdf, how="left", predicate="intersects")

        # insert vertices for polygons that intersect each other
        # we insert all modified polygons into list newgeoms
        newgeoms = []
        for i, row in gdf.iterrows():
            # get indices of intersecting polygons
            indices = np.atleast_1d(gdf_intersects.loc[i].index_right)
            # select the touching polygons from the geodataframe
            touched = gdf.loc[indices].geometry

            # by default the new geom is the same as the old one
            newgeom = gdf.loc[[i]]

            # if any of the polygons touches (size>1) or if
            # the polygon was already processed in a previous
            # iteration (done) we update the geom
            if touched.size > 1 and not newgeom.done.item():
                for t in touched:
                    newgeom = newgeom.snap(t, tolerance)
            else:
                newgeom = newgeom.geometry
            newgeoms.append(newgeom)

        # counter to compare nr of vertices on old structure
        gdf["npoints_old"] = [
            len(row.geometry.exterior.coords)
            + sum([len(i.coords) for i in row.geometry.interiors])
            for i, row in gdf.iterrows()
        ]
        # overwrite the old geometry column with the modified one
        gdf["geometry"] = pd.concat(newgeoms)
        # count new number of points for each polygon
        gdf["npoints"] = [
            len(row.geometry.exterior.coords)
            + sum([len(i.coords) for i in row.geometry.interiors])
            for i, row in gdf.iterrows()
        ]
        # we can get the number of new vertices inserted by doing gdf["npoints"].sum() - sum_vertices_old
        # we mark a polygon as done, if the number of points stays the same, i.e no snapping has occured.
        gdf["done"] = gdf["npoints"] - gdf["npoints_old"] == 0

    return gdf.drop(columns=["npoints", "npoints_old", "done"])
