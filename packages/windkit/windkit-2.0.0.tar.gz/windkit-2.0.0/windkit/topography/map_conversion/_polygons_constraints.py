"""Module to add the necessary constraint on polygon gdf."""

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.ops as ops
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient as shapely_orient


def _complete_polygons_vertices(polygons, atol=0):
    """
    Add necessary points to enable polygon matching.

    Parameters
    ----------
    polygons: geopandas.GeoDataFrame
    tolerance: float
        maximum distance to consider that a point is on a line.
    """
    lines, i_holes = _poly_to_brute_lines(polygons)
    points = _lines_to_points_gdf(lines)
    matches = _match(lines, points, atol)

    # TODO
    # This for loop is what takes most of the time:
    for i, row in matches.iterrows():
        line = lines.loc[row["intersected_line"], "geometry"]
        line_from = lines.loc[row["line_that_pt_is_from"], "geometry"]
        p = row["point"]
        if row["snap_dist"] > 0:
            p = ops.nearest_points(p, line)[1]
        line = ops.split(line, p)
        line = ops.linemerge(line)
        line = ops.snap(line, line_from, tolerance=atol)
        lines.loc[row.intersected_line, "geometry"] = line
        lines.loc[row.line_that_pt_is_from, "geometry"] = ops.snap(
            line_from, line, tolerance=atol
        )

    holes = lines.loc[len(polygons) :]
    lines.set_index(lines.loc[:, "index"], drop=True, inplace=True)
    for i in polygons.index:
        poly = Polygon(
            lines.loc[i, "geometry"],
            holes=[
                h.coords for h in holes.loc[i_holes[i] : i_holes[i + 1] - 1].geometry
            ],
        )
        polygons.loc[i, "geometry"] = shapely_orient(poly.buffer(0))

    return polygons


def _poly_to_brute_lines(polygons):
    i_holes = [len(polygons)]
    holes = []
    for i in polygons.index:
        holes_tmp = polygons.loc[i, "geometry"].interiors[:]
        i_holes.append(i_holes[-1] + len(holes_tmp))
        for h in holes_tmp:
            holes.append(LineString(h.coords[:]))
    holes = gpd.GeoDataFrame(geometry=holes)

    lines = polygons.geometry.apply(
        lambda row: LineString(row.exterior.coords[:])
    ).reset_index()
    lines = pd.concat([lines, holes], ignore_index=True).reset_index(drop=True)
    return lines, np.array(i_holes, dtype=int)


def _lines_to_points_gdf(lines):
    lines_coords = [line.coords[:-1] for line in lines.geometry]
    points = np.concatenate(lines_coords)
    line_that_pt_is_from = np.repeat(
        a=np.arange(len(lines)), repeats=[len(coords) for coords in lines_coords]
    )
    points = gpd.GeoDataFrame(
        {
            "geometry": [Point(p) for p in points],
            "line_that_pt_is_from": line_that_pt_is_from,
        }
    )
    return points


def _match(lines, points, atol):
    bbox = points.bounds + [-atol, -atol, atol, atol]
    hits = bbox.apply(lambda row: list(lines.sindex.intersection(row)), axis=1)
    pt_idx = np.array(np.repeat(hits.index, hits.apply(len)))

    tmp = pd.DataFrame(
        {
            "pt_idx": pt_idx,
            "line_that_pt_is_from": points.loc[pt_idx, "line_that_pt_is_from"],
            "intersected_line": np.concatenate(hits.values),
        }
    )
    tmp = tmp.join(lines.drop(columns="index"), on="intersected_line")
    tmp = tmp.join(points.geometry.rename("point"), on="pt_idx")
    tmp = gpd.GeoDataFrame(tmp, geometry="geometry", crs=points.crs)
    tmp["snap_dist"] = tmp.geometry.distance(gpd.GeoSeries(tmp.point))
    tmp = tmp.loc[
        (tmp.snap_dist <= atol) & (tmp.intersected_line != tmp.line_that_pt_is_from)
    ]
    return tmp
