"""Tools for converting a line map to polygon map

The LineMap class provides comparison, conversion, and plotting
methods.
The lines_to_poly function provides a simple functional conversion
"""


# In this module a node is defined as an endpoint of a line. It results that
# there are two nodes for each lines and different nodes may be at the same
# position: in that case the nodes are adjacent.

import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from geopandas.testing import assert_geodataframe_equal
from shapely.geometry import LinearRing, LineString, Polygon
from shapely.geometry.polygon import orient as shapely_orient

from . import poly_to_lines
from .helper_functions import (
    _dict_to_df,
    _get_AL,
    _get_angle,
    _sort_counterclockwise_points,
)
from windkit.plot.color import Color, _get_valid_color

from ...import_manager import _import_optional_dependency


def _check_line_gdf_format(gdf):
    required = ["geometry", "id_left", "id_right"]
    for column_name in required:
        if column_name not in gdf:
            raise Exception(f"Missing required column: {column_name}")
    if not (np.array(gdf.geom_type) == "LineString").all():
        raise Exception("Geometry column should contain LineStrings only")


def _is_valid_buffer(buffer):
    if isinstance(buffer, float) or isinstance(buffer, int):
        return buffer >= 0
    else:
        return (np.array(buffer) >= 0).all()


class LineMap:
    """
    Class to convert a line geodataframe to a polygon geodataframe.

    The path argument has the priority over the line_gdf argument.

    Parameters
    ----------
    lines: GeoDataFrame or string or path
        A geodataframe including the columns geometry filled with LineString
        and id filled with integers or float, or path to such a geodataframe.
    """

    def __init__(self, lines):
        if isinstance(lines, gpd.GeoDataFrame):
            line_gdf = lines
        else:
            line_gdf = gpd.read_file(lines)

        _check_line_gdf_format(line_gdf)

        self._line_gdf = line_gdf.reset_index()
        self._original_n = len(self._line_gdf)
        self._visited = None
        self._nodes = None
        self._AL_nodes = None
        self._tight_bbox = None
        self._xleft, self._ydown, self._xright, self._yup = None, None, None, None
        self._middle = None
        self._poly_gdf = None
        self._buffer = None

    def __string__(self):
        """Return the object representation."""
        return f"Line map.\nGeodataframe: {self._line_gdf}"

    @property
    def line_gdf(self):
        """Return the original line geodataframe."""
        lines = self._line_gdf.iloc[: self._original_n]
        lines.set_index(lines.loc[:, "index"].astype(int), inplace=True)
        return lines.drop(columns="index")

    def assert_lines_equal(self, map2, **kwargs):
        """
        Evaluate lines dataframes equality with another map.

        Sort the points in each geometry and the geometries in the dataframes.

        Parameters
        ----------
        map2: ConvertibleMap
            The map that has the line gdf to compare to.
        **kwargs:
            Will be passed to assert_geodataframe_equal
        """
        df1 = sort_line_gdf(self.line_gdf)
        df2 = sort_line_gdf(map2.line_gdf)
        try:
            assert_geodataframe_equal(df1, df2, check_dtype=False, **kwargs)
            return True
        except AssertionError:
            return False

    def plot(
        self,
        plot_endpoints=False,
        landcover_table=None,
        color_lines=False,
        cmap=None,
        norm=None,
        ignore_collisions=True,
        **kwargs,
    ):
        """
        Plot the original line GeoDataFrame.

        Parameters
        ----------
        plot_endpoints : bool, optional. Default: False
            Whether or not to plot the endpoints of the lines.
        landcover_table: windkit LandCoverTable or dict or None. Default: None
            Map ids to roughness values. If None, use ids for coloring lines.
        color_lines : bool or string: "right" or "left", optional. Default: False
            Whether to use the left or right id to color the lines.
            The lines are colored according to "z0" if available else "id".
            If False, the lines will be uniform in color.
        cmap : matplotlib.colors.Colormap, optional. Default: None
            Colormap to color the lines. If cmap and norm are set to None and
            color_lines is True, use a default colormap.
        norm : matplotlib.colors.BoundaryNorm, optional. Default: None
            norm used when coloring the lines. If cmap and norm are set to None
            and color_lines is True, use a default norm.
        ignore_collisions : bool, optional. Default: True
            If ignore_collisions is False, cmap is None and color_lines is True,
            (i.e. default color is used), the function will raise an error if two
            different rougness values are mapped to the same colors.
        """
        if isinstance(color_lines, str):
            side = color_lines
            color_lines = True
        else:
            side = "left"
        try:
            line_gdf = self._get_line_gdf_with_z0(
                side=side, landcover_table=landcover_table
            )
        except (AttributeError, KeyError):
            line_gdf = self.line_gdf

        if color_lines:
            column = "z0" if "z0" in line_gdf.columns else f"id_{side}"
        else:
            column = None

        if cmap is None and norm is None and (column == "z0"):
            try:
                color = Color._from_lc(landcover_table)
            except Exception:
                color = _get_valid_color(line_gdf, ignore_collisions)
            cmap, norm = color.cmap, color.norm

        ax = line_gdf.plot(aspect=1, cmap=cmap, column=column, **kwargs)
        if plot_endpoints:
            self._endpoints_plot(ax=ax)

    def _get_line_gdf_with_z0(self, landcover_table=None, side="left"):
        """Return a copy of the line dataframe with roughness values.

        This is only possible if we have a landcover table.
        """
        line_gdf = self.line_gdf
        if isinstance(landcover_table, dict):
            landcover_table = _dict_to_df(landcover_table)
        if landcover_table is not None:
            id_ = line_gdf.loc[:, f"id_{side}"]
            line_gdf["z0"] = np.array(landcover_table.loc[id_, "z0"])
        else:
            raise AttributeError(
                "Cannot add roughness values without a landcover table."
            )
        return line_gdf

    def _endpoints_plot(self, **kwargs):
        plt = _import_optional_dependency("matplotlib.pyplot")

        if self._nodes is None:
            self._nodes = self._get_nodes()
        coords = np.array([np.array(c) for c in self._nodes[: 2 * self._original_n]])
        if "ax" in kwargs:
            kwargs["ax"].plot(coords[:, 0], coords[:, 1], "r.")
        else:
            plt.plot(coords[:, 0], coords[:, 1], "r.")

    def to_poly_map(self, bbox=None, buffer=0, **kwargs):
        """Compute and return the polygon map.

        Parameters
        ----------
        bbox: 4-uple, optional. Default: None
            x_left, y_down, x_right, y_up. If None, the bbox will fit the data.
        buffer: float or 4-uple, optional. Default: 0
            If lines of the gdf touches the border continuously, the border will
            be moved by the value of the buffer. The buffer has to be non negative.
            null buffer may cause invalid polygons if a line touches a border
            continuously.
        **kwargs: rtol and atol can be used to assess that two points are at the same
            place with np.isclose.
        """
        if not _is_valid_buffer(buffer):
            raise ValueError("Invalid value for buffer argument.")
        self._buffer = buffer

        self._nodes = self._get_nodes()
        self._AL_nodes = _get_AL(self._nodes, **kwargs)

        bbox = self._get_buffered_borders(bbox_user=bbox)
        self._xleft, self._ydown, self._xright, self._yup = bbox
        self._middle = ((self._xleft + self._xright) / 2, (self._yup + self._ydown) / 2)

        self._make_all_polygons(**kwargs)

        # reset the dataframe for next time / for getting the correct lines
        self._line_gdf = self._line_gdf.iloc[: self._original_n]

        return poly_to_lines.PolygonMap(self._poly_gdf)

    def _make_all_polygons(self, **kwargs):
        """Create/update the attribute poly_gdf."""

        self._link_borders()
        # nodes have to be updated after linking.
        self._nodes = self._get_nodes()
        self._AL_nodes = _get_AL(self._nodes, **kwargs)

        self._visited = np.zeros(2 * len(self._line_gdf), bool)
        polygons = []
        polygons_id = []
        polygons_nodes = []
        holes = []
        holes_id = []
        holes_nodes = []

        for i in range(2 * self._original_n):
            if not self._visited[i]:
                polygon_nodes = self._get_polygon(i)
                points = self._nodes2polygon_points(polygon_nodes)
                id_, type_ = self._get_id_and_type(polygon_nodes)
                if type_ == "shell":
                    polygons.append(Polygon(points))
                    polygons_id.append(id_)
                    polygons_nodes.append(polygon_nodes)
                elif type_ == "hole":
                    holes.append(Polygon(points))
                    holes_id.append(id_)
                    holes_nodes.append(polygon_nodes)

        polygons, polygons_id = self._cut_holes(
            polygons, holes, holes_id, polygons_id, polygons_nodes, holes_nodes
        )

        self._poly_gdf = gpd.GeoDataFrame(
            {"geometry": polygons, "id": polygons_id}, crs=self.line_gdf.crs
        )

    def _cut_holes(
        self, polygons, holes, holes_id, polygons_id, polygons_nodes, holes_nodes
    ):
        """Return a list of polygon without intersections."""
        areas = np.array([Polygon(h).area for h in holes])
        sort_holes = np.argsort(-areas)
        holes = np.array(holes, dtype=object)[sort_holes]
        holes_id = np.array(holes_id)[sort_holes]
        holes_nodes = np.array(holes_nodes, dtype=object)[sort_holes]
        covered = np.zeros(len(holes), dtype=bool)

        for i, poly_int in enumerate(holes):
            for j, poly_ext in enumerate(polygons):
                if poly_ext.contains(poly_int) and not poly_int.covers(poly_ext):
                    if holes_id[i] != polygons_id[j]:
                        self._matching_error(
                            [holes_id[i], polygons_id[j]],
                            np.r_[holes_nodes[i], polygons_nodes[j]],
                        )

                    h = [p.coords for p in poly_ext.interiors] + [
                        poly_int.exterior.coords
                    ]
                    polygons[j] = shapely_orient(
                        Polygon(poly_ext.exterior.coords, holes=h)
                    )
                    covered[i] = True
        if not covered.all():
            holes_id = holes_id[~covered]
            if len(np.unique(holes_id)) != 1:
                self._matching_error(
                    np.unique(holes_id),
                    np.concatenate(holes_nodes[~covered]),
                )

            block = Polygon(
                shell=[
                    (self._xleft, self._yup),
                    (self._xleft, self._ydown),
                    (self._xright, self._ydown),
                    (self._xright, self._yup),
                ],
                holes=[h.exterior.coords for h in holes[~covered]],
            )
            block = shapely_orient(block)
            polygons.append(block)
            polygons_id.append(holes_id[0])

        return polygons, polygons_id

    def _matching_error(self, common_ids, nodes=None):
        common_ids = np.array(common_ids)
        error_message = (
            f"\nMore than one id found: {', '.join((common_ids).astype(str))}"
        )
        if nodes is not None:
            lines = np.array(nodes) // 2
            error_message += f" for line(s) {', '.join((lines).astype(str))}."
        raise ValueError(error_message)

    def _get_buffered_borders(self, bbox_user=None):
        self.total_bounds
        expected_sign = np.array([-1, -1, 1, 1])
        if bbox_user is not None:
            buffer = bbox_user - self._tight_bbox
            where_bbox_user = buffer * expected_sign > 0
            for i in range(4):
                if buffer[i] * expected_sign[i] < 0:
                    raise ValueError(f"bbox[{i}] inside map.")
        else:
            buffer = expected_sign * self._buffer
            where_bbox_user = [0, 0, 0, 0]

        bbox = self._add_buffers(buffer, where_bbox_user)
        return bbox

    @property
    def total_bounds(self):
        """
        Return the coordinates of the borders (left, down, right, top).

        Return the ordinate of the bottom and the top and the absissa of the
        right and left borders. Not that the extreme points can be in the
        middle of a line.
        """
        if self._tight_bbox is None:
            points = []
            cum_len = [0]
            for i in range(self._original_n):
                points += self._node2line_points(2 * i, get_full_line=1)
                cum_len.append(len(points))
            x = np.array([p[0] for p in points])
            y = np.array([p[1] for p in points])
            self._tight_bbox = np.array([min(x), min(y), max(x), max(y)])
        return self._tight_bbox

    def _add_buffers(self, buffer, where_bbox_user):
        border_end_points = self._get_node_points(self._get_borders_indices())
        x = np.array([p[0] for p in border_end_points])
        y = np.array([p[1] for p in border_end_points])
        for i in [0, 2]:
            if (
                (x == self._tight_bbox[i])
                & ~(y == self._tight_bbox[1])
                & ~(y == self._tight_bbox[3])
            ).any():
                buffer[i] = 0
                if where_bbox_user[i]:
                    raise ValueError(
                        f"Cannot extend the map on {'left' if i == 0 else 'right'} border because open lines stop."
                    )
        for i in [1, 3]:
            if (
                (y == self._tight_bbox[i])
                & ~(x == self._tight_bbox[0])
                & ~(x == self._tight_bbox[2])
            ).any():
                buffer[i] = 0
                if where_bbox_user[i]:
                    raise ValueError(
                        f"Cannot extend the map on {'bottom' if i == 1 else 'top'} border because open lines stop."
                    )
        return self._tight_bbox + buffer

    def _get_nodes(self):
        """Get all the lines endpoints or nodes."""
        nodes = np.zeros(2 * len(self._line_gdf), dtype=tuple)
        for i, line in enumerate(self._line_gdf.loc[:, "geometry"]):
            nodes[2 * i] = line.coords[0]
            nodes[2 * i + 1] = line.coords[-1]
        return nodes

    def _get_node_points(self, nodes):
        """Return the coordinates of the nodes."""
        points = []
        for node in nodes:
            line = self._line_gdf.loc[node // 2, "geometry"]
            if node % 2 == 0:
                point = (line.coords[0][0], line.coords[0][1])
            else:
                point = (line.coords[-1][0], line.coords[-1][1])
            points.append(point)
        return points

    def _get_borders_indices(self):
        """Return the index of the nodes on the edge."""
        AL_count = [len(self._AL_nodes[i]) for i in range(len(self._AL_nodes))]
        borders = np.where(np.array(AL_count) == 0)[0]
        return borders

    def _get_sorted_borders_with_corners(self):
        """
        Return the border nodes indices sorted.

        Returns
        -------
        points: list of tuples

        """

        corners = [
            (self._xleft, self._ydown),
            (self._xleft, self._yup),
            (self._xright, self._ydown),
            (self._xright, self._yup),
        ]
        borders = self._get_borders_indices()
        points = np.unique(self._get_node_points(borders) + corners, axis=0)
        points = [(p[0], p[1]) for p in points]
        ref = (self._xleft, self._yup)
        sorted_indices = _sort_counterclockwise_points(self._middle, ref, points)
        return np.array(points)[sorted_indices]

    def _link_borders(self):
        sorted_borders = self._get_sorted_borders_with_corners()
        border_lines = []
        for i in range(len(sorted_borders)):
            points = [sorted_borders[i], sorted_borders[i - 1]]
            border_lines.append(LineString(points))
        id_ = [-1] * len(border_lines)
        self._line_gdf = pd.concat(
            [
                self._line_gdf,
                gpd.GeoDataFrame(
                    {"geometry": border_lines, "id_left": id_, "id_right": id_},
                    crs=self.line_gdf.crs,
                ),
            ],
            ignore_index=True,
        )

    def _get_polygon(self, next_node):
        """
        Return a polygon starting with line1 and point node i.

        To get a polygon starting with a node, always take the line with the
        smallest angle and continue until the polygon is closed

        Parameters
        ----------
        next_node: integer
            index of the node in the list of nodes.

        Returns
        -------
        poly : list of int
            nodes forming the polygon starting with next_node.

        """
        first_node = next_node
        polygon_nodes = []
        k = 0
        while (next_node != first_node) or (k == 0):
            polygon_nodes.append(next_node)
            next_node = self._get_next_node(next_node)
            k += 1
            if k > len(self._line_gdf):
                raise ValueError(
                    "Lines cannot create closed polygon, please update linemap to close areas."
                )
            self._visited[next_node] = True
        return polygon_nodes

    def _get_next_node(self, i_node):
        """
        Return the next line of a given polygon.

        Parameters
        ----------
        i_node: int
            index of the node considered.

        Returns
        -------
        next_node: int
            index of the node to continue the polygon with.

        """
        AL_node = self._AL_nodes[i_node]

        angles = np.zeros(len(AL_node))
        for j, j_node in enumerate(AL_node):
            a, b, c = self._get_angle_points(i_node, j_node)
            angles[j] = _get_angle(a, b, c)
        j = np.argmin(angles)
        next_node = AL_node[j] // 2 * 2 + 1 - AL_node[j] % 2
        return next_node

    def _get_angle_points(self, i, j):
        """
        Return the 3 points a, b, c that form an angle bac given two lines ab, ac.

        Parameters
        ----------
        i, j: int
            the node i is part of a line (line1) and j part of a line (line2)

        Returns
        -------
        a, b1, b2: tuple
            points so that a belongs to line 1 and line2, b1 to line1 and b2 to
            line2

        """
        line1 = self._line_gdf.loc[i // 2, "geometry"]
        line2 = self._line_gdf.loc[j // 2, "geometry"]
        if i % 2 == 0:
            a = line1.coords[0]
            b1 = line1.coords[1]
        else:
            a = line1.coords[-1]
            b1 = line1.coords[-2]
        if j % 2 == 0:
            b2 = line2.coords[1]
        else:
            b2 = line2.coords[-2]
        return a, b1, b2

    def _nodes2polygon_points(self, polygon_nodes):
        """
        Return the points of the corresponding polygon.

        points: list of tuples
            Can be used to build a polygon object
        """
        points = []
        for node in polygon_nodes:
            points += self._node2line_points(node)
        return points

    def _node2line_points(self, i, get_full_line=0):
        """
        Return all the points of the line expect one.

        The points are returned as tuple. They may be returned in order or in
        inverse order depending on the node used: in order if the node is the
        start of the line, revered if it is the last. The other node is not
        returned as it belongs to the next line, or to the first if the line is
        the last of the polygon.
        """
        line = self._line_gdf.loc[i // 2, "geometry"]
        if i % 2 == 1:
            points = [
                (line.coords[j][0], line.coords[j][1])
                for j in range(len(line.coords) - 1 + get_full_line)
            ]
        else:
            points = [
                (line.coords[-j][0], line.coords[-j][1])
                for j in range(1 - get_full_line, len(line.coords))
            ]
        return points

    def _get_id_and_type(self, nodes):
        """
        Return the id of a polygon.

        Parameters
        ----------
        nodes : list of int
            nodes belonging to a polygon

        """
        nodes = np.array(nodes)
        points = self._nodes2polygon_points(nodes)
        is_ccw = LinearRing(points).is_ccw
        nodes = nodes[nodes < 2 * self._original_n]
        common_id = np.zeros(len(nodes), dtype=int)

        for i, node in enumerate(nodes):
            side = "right" if node % 2 else "left"
            common_id[i] = self._line_gdf.loc[node // 2, f"id_{side}"]
        common_id = np.unique(common_id)
        if len(common_id) != 1:
            self._matching_error(common_id, nodes=nodes)
        type_ = self._polygon_type(common_id[0], nodes, is_ccw)
        return common_id[0], type_

    def _polygon_type(self, id_, nodes, is_ccw):
        if is_ccw:
            type_ = "hole"
        else:
            type_ = "shell"
        return type_


def lines_to_poly(line_gdf, bbox=None, buffer=0):
    """Convert a geodataframe of lines to a geodataframe of polygons.

    Parameters
    ----------
    line_gdf: GeoDataFrame
        A geodataframe including the columns geometry filled with LineString
        and id filled with integers or float.
    bbox: 4-uple, optional. Default: None
        x_left, y_down, x_right, y_up
    buffer: float, optional. Default: 0
        If lines of the gdf touches the border continuously, this border will
        be moved by the value of the buffer. The buffer has to be non negative.
        null buffer may cause invalid polygons if a line touches a border
        continuously.
    """
    warnings.warn(
        "`lines_to_poly` is deprecated, please use `lines_to_polygons` instead.",
        FutureWarning,
    )

    line_map = LineMap(line_gdf)
    poly_map = line_map.to_poly_map(bbox=bbox, buffer=buffer)
    poly_map = poly_map._poly_gdf.drop(columns="index").rename(columns={"index": "id"})
    poly_map["geometry"] = poly_map["geometry"].make_valid()
    return poly_map


def sort_line_gdf(gdf):
    """Return the dataframe "sorted".

    Sorted depending on the length of the line, which is unique in the example
    maps. The order itself does not matter as long as we can get a unique order.
    """

    gdf.reset_index(inplace=True, drop=True)

    lines = np.zeros(len(gdf), dtype=object)
    id_left = np.zeros(len(gdf))
    id_right = np.zeros(len(gdf))
    for i in range(len(gdf)):
        lines[i], id_left[i], id_right[i] = _line_sort(gdf.loc[i])
    gdf = gpd.GeoDataFrame(
        {
            "geometry": [LineString(line) for line in lines],
            "id_left": id_left,
            "id_right": id_right,
        },
    )

    line_length = [line.length for line in gdf.loc[:, "geometry"]]
    if len(np.unique(line_length)) != len(line_length):
        raise Exception("Current comparison criteria cannot separate some lines.")
    sort_ = np.argsort(line_length)
    return gdf.loc[sort_].reset_index(drop=True)


def _line_sort(df_row):
    """Ensure a given line is always given in the same direction.

    Parameters
    ----------
    df_row: pandas series
        row of a map line geodataframe.
    """
    id_left = df_row.loc["id_left"]
    id_right = df_row.loc["id_right"]
    points = np.array(df_row.loc["geometry"].coords)

    sort = np.lexsort((points[:, 0], points[:, 1]))
    if sort[0] > sort[-1]:
        points = points[::-1]
        id_left, id_right = id_right, id_left

    if (points[0] == points[-1]).all():
        points, was_ccw = poly_to_lines._poly_sort(points, line=True)
        if not was_ccw:
            id_left, id_right = id_right, id_left

    return np.array(points), id_left, id_right
