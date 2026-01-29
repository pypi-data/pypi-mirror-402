"""Tools for converting a polygon map to line map.

The PolygonMap class provides comparison, conversion, and plotting methods.
The poly_to_lines function provides a simple functional conversion.
"""


# In this file a node is defined as any point of a polygon. A point that belongs
# to several polygons results in several nodes that are adjacent.

# All the polygons are oriented anticlockwise after loading the dataframe. The
# assumption that all the polygons are oriented is used in several methods of
# the class.

import warnings

import geopandas as gpd
import numpy as np
from geopandas.testing import assert_geodataframe_equal
from shapely import ops
from shapely.geometry import LinearRing, LineString, Point, Polygon
from shapely.geometry.polygon import orient as shapely_orient

from . import lines_to_poly
from ._polygons_constraints import _complete_polygons_vertices
from .helper_functions import _dict_to_df, _get_AL
from windkit.plot.color import Color, _get_valid_color

from ...import_manager import _import_optional_dependency
from ..map_conversions import snap_to_layer


def _check_poly_gdf_format(gdf):
    required = ["geometry", "id"]
    for column_name in required:
        if column_name not in gdf:
            raise Exception(f"Missing required column: {column_name}")
    if not (np.array(gdf.geom_type) == "Polygon").all():
        raise Exception("Geometry column should contain Polygons only")


class PolygonMap:
    """Class to convert a polygon geodataframe to a line geodataframe.

    The path argument has the priority over the poly_gdf argument.

    Parameters
    ----------
    polys: GeoDataFrame or string or path
        A geodataframe including the columns geometry filled with Polygons
        and id filled with integers or float, or a path to such a geodataframe
    background_lc_id: int or None, optional. Default: None
        To define when the map is not entirely filled. It will be used when a
        line is defined by only one polygon.
    """

    def __init__(self, polys, background_lc_id=None):
        if isinstance(polys, gpd.GeoDataFrame):
            poly_gdf = polys
        else:
            poly_gdf = gpd.read_file(polys)

        _check_poly_gdf_format(poly_gdf)
        if "index" not in poly_gdf:
            self._poly_gdf = poly_gdf.reset_index()
        else:
            index = poly_gdf.loc[:, "index"].astype(int)
            poly_gdf = poly_gdf.set_index(index, drop=True).drop(columns="index")
            self._poly_gdf = poly_gdf.reset_index()
        self._poly_gdf.geometry = self._poly_gdf.geometry.apply(shapely_orient)

        self.background_lc_id = background_lc_id
        self._remove_borders = False
        self._is_shell = None
        self._cumulative_nb_points = None
        self._points = None
        self._prev, self._next = None, None
        self._AL = None
        self._border_mask = None
        self._endpoints = None
        self._line_gdf = None

    def __string__(self):
        """Return the object representation."""
        return f"Polygon map.\nGeodataframe: {self._poly_gdf}"

    @property
    def poly_gdf(self):
        """Return the original polygon geodataframe."""
        try:
            index = self._poly_gdf.loc[:, "index"].astype(int)
            polys = self._poly_gdf.set_index(index, drop=True)
            return polys.drop(columns="index")
        except KeyError:
            return self._poly_gdf

    def assert_polygons_equal(self, map2, **kwargs):
        """
        Evaluate polygons dataframes equality with another map.

        Sort the points in each geometry and the geometries in the dataframes.

        Parameters
        ----------
        map2: ConvertibleMap
            The map that has the poly gdf to compare to.
        **kwargs:
            Will be passed to assert_geodataframe_equal
        """
        df1 = sort_poly_gdf(self._poly_gdf)
        df2 = sort_poly_gdf(map2._poly_gdf)
        try:
            assert_geodataframe_equal(df1, df2, check_dtype=False, **kwargs)
            return True
        except AssertionError:
            return False

    def plot(
        self,
        plot_endpoints=False,
        landcover_table=None,
        cmap=None,
        norm=None,
        ignore_collisions=True,
        **kwargs,
    ):
        """Plot the polygon GeoDataFrame.

        Parameters
        ----------
        plot_endpoints : bool, optional. Default: False
            Whether or not to plot the endpoints of the lines.
        landcover_table: windkit LandCoverTable or dict or None. Default: None
            Map ids to roughness values. If None, use ids for coloring polygons.
        cmap : matplotlib.colors.Colormap, optional. Default: None
            If cmap and norm are set to None, a default colormap is used.
        norm : matplotlib.colors.BoundaryNorm, optional. Default: None
            If cmap and norm are set to None, a default norm is used.
        ignore_collisions : bool, optional. Default: True
            If ignore_collisions is False and cmap and norm are None (i.e.
            default color is used), the function will raise an error if two
            different rougness values are mapped to the same colors.

        Return
        ------
        ax
        """
        try:
            poly_gdf = self._get_poly_gdf_with_z0(landcover_table)
        except (AttributeError, KeyError):
            poly_gdf = self.poly_gdf

        column = "z0" if "z0" in poly_gdf.columns else "id"
        if cmap is None and norm is None and (column == "z0"):
            try:
                color = Color._from_lc(landcover_table)
            except Exception:
                color = _get_valid_color(poly_gdf, ignore_collisions)
            cmap, norm = color.cmap, color.norm

        ax = poly_gdf.plot(column=column, cmap=cmap, norm=norm, **kwargs)

        if plot_endpoints:
            self._endpoints_plot(ax=ax)

        return ax

    def _get_poly_gdf_with_z0(self, landcover_table=None):
        """Return a copy of the polygon dataframe with roughness values.

        This is only possible if we have a landcover table.
        """
        poly_gdf = self.poly_gdf
        if isinstance(landcover_table, dict):
            landcover_table = _dict_to_df(landcover_table)
        if landcover_table is not None:
            id_ = poly_gdf.loc[:, "id"]
            poly_gdf["z0"] = np.array(landcover_table.loc[id_, "z0"])
        else:
            raise AttributeError(
                "Cannot add roughness values without a landcover table."
            )
        return poly_gdf

    def _endpoints_plot(self, **kwargs):
        plt = _import_optional_dependency("matplotlib.pyplot")

        if self._endpoints is None:
            self._preprocessing()
        if len(self._endpoints) == 0:
            return

        coords = self._points[self._endpoints].flatten()
        coords = np.array([np.array(c) for c in coords])
        if "ax" in kwargs:
            kwargs["ax"].plot(coords[:, 0], coords[:, 1], "r.")
        else:
            plt.plot(coords[:, 0], coords[:, 1], "r.")

    def to_line_map(
        self,
        apply_background_lc_id=False,
        atol=0,
        complete_polys=False,
        return_poly_map=False,
        **kwargs,
    ):
        """Compute and return the line map.

        Parameters
        ----------
        apply_background_lc_id: bool or list of bool, optional. Default: False
            Retain lines that only have a polygon on a single side? Requires
            background_lc_id to be not None.
        atol: float, optional. Default: 0
            maximum to distance to consider that two points are at the same place.
        complete_polys: bool, optional. Default: False
            Do not rely on the assumptions that neighbour polygons vertices match.
            Recommended for raster objects. Requires atol to be >0.
        return_poly_map: bool, optional. Default: False
            Return the PolygonMap used? When complete_polys is True, this map can differ
            from the original map.
        """
        original_polys = self._poly_gdf
        if complete_polys:
            method = kwargs.get("complete_method", "original")
            if method == "original":
                self._poly_gdf = _complete_polygons_vertices(self._poly_gdf, atol=atol)
            elif method == "new":
                self._poly_gdf = snap_to_layer(self._poly_gdf, atol=atol)

        if self.background_lc_id is None and apply_background_lc_id:
            raise ValueError(
                "background landcover id has to be set to use 'apply_background_lc_id'."
            )
        self._remove_borders = not apply_background_lc_id
        self._preprocessing(atol=atol)
        self._line_gdf = self._make_line_gdf(
            apply_background_lc_id=apply_background_lc_id
        )
        if self.poly_gdf.crs is not None:
            self._line_gdf = self._line_gdf.set_crs(self.poly_gdf.crs)

        modified_polys = self._poly_gdf
        self._poly_gdf = original_polys
        if return_poly_map:
            return (
                lines_to_poly.LineMap(self._line_gdf),
                PolygonMap(modified_polys, background_lc_id=self.background_lc_id),
            )
        else:
            return lines_to_poly.LineMap(self._line_gdf)

    def _preprocessing(self, **kwargs):
        """Create the attribute line_gdf."""
        (
            self._is_shell,
            self._cumulative_nb_points,
            origin,
        ) = self._get_types_and_cumulative_nb_points()
        self._points = self._polygons2points()
        self._prev, self._next = self._get_neighbours()
        self._AL = _get_AL(self._points, origin=origin, **kwargs)
        self._border_mask = self._get_border_mask()
        self._endpoints = self._get_endpoints()

    def _get_types_and_cumulative_nb_points(self):
        length_polygons = [0]
        is_shell = []
        for polygon in self._poly_gdf.loc[:, "geometry"]:
            shell = polygon.exterior.coords[:-1]
            holes = polygon.interiors

            length_polygons.append(len(shell))
            is_shell.append(1)

            if len(polygon.interiors) > 0:
                length_polygons += [len(h.coords) - 1 for h in holes]
                is_shell += [0] * len(holes)

        cumulative_nb_points = np.cumsum(length_polygons, dtype=int)
        return (
            np.array(is_shell, dtype=int),
            cumulative_nb_points,
            np.repeat(np.arange(len(length_polygons)), length_polygons),
        )

    def _polygons2points(self):
        """Return polygon points including duplicates."""
        points = np.zeros(self._cumulative_nb_points[-1], dtype=tuple)
        i = 0
        for polygon in self._poly_gdf.loc[:, "geometry"]:
            shell = polygon.exterior.coords[:-1]
            holes = polygon.interiors
            points[
                self._cumulative_nb_points[i] : self._cumulative_nb_points[i + 1]
            ] = shell
            i += 1
            for h in holes:
                points[
                    self._cumulative_nb_points[i] : self._cumulative_nb_points[i + 1]
                ] = h.coords[:-1]
                i += 1
        return points

    def _get_endpoints(self):
        """
        Find the endpoints of the lines.

        Either the previous and next nodes belong to two different groups of
        polygons, either the point belongs to at least 2 polygons and a border.
        """
        visited = np.zeros(len(self._points), dtype=bool)
        endpoints = []

        for i in range(len(self._points)):
            if not visited[i]:
                nodes = self._AL[i] + [i]
                visited[nodes] = 1
                prev_ = np.concatenate([self._AL[self._prev[i]], [self._prev[i]]])
                next_ = np.concatenate([self._AL[self._next[i]], [self._next[i]]])
                poly_node, _ = self._index_2D(nodes)
                poly_prev, _ = self._index_2D(prev_)
                poly_next, _ = self._index_2D(next_)
                if not np.array(
                    [p in poly_prev and p in poly_next for p in poly_node]
                ).all():
                    endpoints += nodes
        AL_count = np.array([len(self._AL[i]) for i in range(len(self._AL))])
        endpoints = np.concatenate(
            (endpoints, np.where(AL_count & self._border_mask)[0])
        )
        return np.sort(np.unique(endpoints)).astype(int)

    def _make_line_gdf(self, apply_background_lc_id):
        """Return a geodataframe with the lines."""

        line_nodes = self._get_line_nodes()
        lines = []
        left_id = []
        right_id = []
        self._visited = np.zeros(len(self._points), dtype=bool)
        for i, nodes in enumerate(line_nodes):
            if not self._is_duplicate_line(nodes, line_nodes[:i]):
                adjacent = self._find_adjacent_nodes_and_polygon(nodes)
                self._visited[nodes] = True
                self._visit_line(adjacent)

                poly, _ = self._index_2D(nodes[0])
                left, right, is_border = self._get_id(poly, adjacent)
                if not is_border or apply_background_lc_id:
                    points = [self._points[n] for n in nodes]
                    lines.append(LineString(points))
                    left_id.append(left)
                    right_id.append(right)

        return gpd.GeoDataFrame(
            {"geometry": lines, "id_left": left_id, "id_right": right_id}
        )

    def _get_id(self, poly, adjacent_info):
        """
        Get the id of the polygon and an adjacent polygon.

        Parameters
        ----------
        poly : int
            Number of the polygon. Holes included.
        adjacent_info : 3-uple or str
            If str, there are no adjacent polygons.

        Returns
        -------
        poly_id : int or float
            id of the polygon.
        adjacent_id : int, float or None
            id of the adjacent polygon if there is one, else background lc id.
        is_border : bool
            True if there is no adjacent polygon.

        """
        poly_position = np.sum(self._is_shell[: poly + 1]) - 1
        poly_id = self._poly_gdf.loc[poly_position, "id"]
        try:
            adjacent_poly, _, _ = adjacent_info
            adjacent_position = np.sum(self._is_shell[: adjacent_poly + 1]) - 1
            adjacent_id = self._poly_gdf.loc[adjacent_position, "id"]
            is_border = False
        except ValueError:
            adjacent_id = self.background_lc_id
            is_border = True

        return poly_id, adjacent_id, is_border

    def _get_line_nodes(self):
        """Return the list of lines as nodes."""
        line_nodes = []
        for i in range(len(self._cumulative_nb_points) - 1):
            start = self._cumulative_nb_points[i]
            stop = self._cumulative_nb_points[i + 1]
            endpoints = self._endpoints[
                (self._endpoints >= start) & (self._endpoints < stop)
            ]
            if len(endpoints) == 0:
                # complete list for plot.
                if not self._border_mask[start]:
                    self._endpoints = np.concatenate((self._endpoints, [start]))
                line_nodes.append(list(range(start, stop)) + [start])
            elif (endpoints[0] != start) or (endpoints[-1] != stop):
                line_nodes.append(
                    list(range(endpoints[-1], stop))
                    + list(range(start, endpoints[0] + 1))
                )
            for j in range(len(endpoints) - 1):
                line_nodes.append(list(range(endpoints[j], endpoints[j + 1] + 1)))
        return line_nodes

    def _get_border_mask(self):
        """Return mask depending on whether points in on the border or not."""
        union = ops.unary_union(self._poly_gdf.geometry)
        border_mask = np.array([not union.contains(Point(p)) for p in self._points])
        return border_mask

    def _get_neighbours(self):
        """Return the list of previous/next nodes inside the corresponding polygons."""
        nodes = np.array(range(self._cumulative_nb_points[-1]))
        prev_ = nodes - 1
        next_ = nodes + 1
        for i in range(len(self._cumulative_nb_points) - 1):
            first = self._cumulative_nb_points[i]
            last = self._cumulative_nb_points[i + 1] - 1
            prev_[first] = last
            next_[last] = first
        return prev_, next_

    def _is_duplicate_line(self, nodes, previous_lines_nodes):
        if len(nodes) == 2:
            possible_duplicates = np.array(previous_lines_nodes, dtype=object)[
                [len(line) == 2 for line in previous_lines_nodes]
            ]
            for nodes2 in possible_duplicates:
                if (
                    nodes[0] in self._AL[nodes2[0]] and nodes[1] in self._AL[nodes2[1]]
                ) or (
                    nodes[0] in self._AL[nodes2[1]] and nodes[1] in self._AL[nodes2[0]]
                ):
                    return True
        else:
            adjacents = np.concatenate(self._AL[nodes][1:-1])
            adjacents = np.concatenate((adjacents, nodes[1:-1]))
            if self._visited[adjacents.astype(int)].all():
                return True
        return False

    def _visit_line(self, adjacent):
        """Mark the nodes corresponding to the same line as visited."""
        try:
            _, i, j = adjacent
        except ValueError:
            return
        if i > j:
            self._visited[list(range(j, i + 1))] = True
        else:
            poly = np.searchsorted(self._cumulative_nb_points, i, side="right") - 1
            start = self._cumulative_nb_points[poly]
            end = self._cumulative_nb_points[poly + 1]
            self._visited[list(range(j, end))] = True
            self._visited[list(range(start, i + 1))] = True

    def _find_adjacent_nodes_and_polygon(self, nodes):
        """Return the number of the polygon adjacent to the nodes.

        Return
        ------
        poly: int
            number of the adjacent polygon
        i, j: int
            start and end of the adjacent nodes
        """
        for i in self._AL[nodes[0]]:
            for j in self._AL[nodes[-1]]:
                poly1, _ = self._index_2D(i)
                poly2, _ = self._index_2D(j)
                if poly1 == poly2:
                    if len(nodes) == 2:
                        if (i == self._prev[j]) or (j == self._prev[i]):
                            return poly1, i, j
                    else:
                        for k in self._AL[nodes[1]]:
                            poly_confirmation, _ = self._index_2D(k)
                            if poly_confirmation == poly1:
                                return poly1, i, j
        return "No adjacent line"

    def _index_2D(self, i):
        """Return the polygon number and the point position in the polygon.

        Parameters
        ----------
        i: int
            index of the point in the list
        """
        i_poly = np.searchsorted(self._cumulative_nb_points, i, side="right") - 1
        j = i - self._cumulative_nb_points[i_poly]
        return i_poly, j


def poly_to_lines(poly_gdf, background_lc_id=None, atol=0, complete_polys=False):
    """Convert a geodataframe of polygons to a geodataframe of lines.

    Parameters
    ----------
    poly_gdf: GeoDataFrame
        A geodataframe including the columns geometry filled with Polygons
        and id filled with integers or float.
    background_lc_id: int or None, optional. Default: None
        When not None, all empty area of the polygon map will be filled with this value.
        This will be used to create change lines between polygons and empty space.
    atol: float, optional. Default: 0
        maximum to distance to consider that two points are at the same place.
    complete_polys: bool, optional. Default: False
        Do not rely on the assumptions that neighbour polygons vertices match.
        Recommended for raster objects. Only has an effect when atol is >0.
    """

    warnings.warn(
        "`poly_to_lines` is deprecated, please use `polygons_to_lines` instead.",
        FutureWarning,
    )

    # Transform to polygon
    if (np.array(poly_gdf.geom_type) == "MultiPolygon").any():
        poly_gdf = poly_gdf.explode(index_parts=False)

    apply_background_lc_id = background_lc_id is not None
    poly_map = PolygonMap(poly_gdf, background_lc_id=background_lc_id)
    line_map = poly_map.to_line_map(
        apply_background_lc_id=apply_background_lc_id,
        atol=atol,
        complete_polys=complete_polys,
    )
    return line_map.line_gdf


def sort_poly_gdf(gdf):
    """Return the dataframe "sorted".

    Sorted depending on the length of the polygons, which is unique in the example
    maps. The order itself does not matter as long as we can recognize that two
    dataframes represent the same map
    """
    gdf.reset_index(drop=True)

    polys = np.zeros(len(gdf), dtype=object)
    for i, row in gdf.iterrows():
        original_poly = row.loc["geometry"]
        shell = _poly_sort(np.array(original_poly.exterior.coords))
        holes = [_poly_sort(np.array(p.coords)) for p in original_poly.interiors]
        polys[i] = Polygon(shell=shell, holes=holes)
    gdf = gpd.GeoDataFrame({"geometry": polys, "id": gdf.loc[:, "id"]})
    poly_length = [poly.length for poly in gdf.loc[:, "geometry"]]
    if len(np.unique(poly_length)) != len(poly_length):
        raise Exception("Current comparison criteria cannot separate some polygons.")
    sort_ = np.argsort(poly_length)
    return gdf.loc[sort_].reset_index(drop=True)


def _poly_sort(points, line=False):
    """Return "sorted" points assuming they are part of a polygon.

    The first point has the lowest abcissa (and ordinate in case of equality),
    the points are browsed in anti clockwise direction.
    """
    if (points[0] == points[-1]).all():
        points = points[1:]

    was_ccw = LinearRing(points).is_ccw
    if not was_ccw:
        points = points[::-1]
    sort = np.lexsort((points[:, 0], points[:, 1]))
    start = sort[0]
    points = np.concatenate(([points[start - 1]], points[start:], points[:start]))

    if line:
        return np.array(points), was_ccw
    return np.array(points)
