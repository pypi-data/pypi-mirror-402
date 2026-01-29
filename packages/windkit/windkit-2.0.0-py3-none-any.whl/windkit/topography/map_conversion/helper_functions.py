"""Functions used in several modules."""

import geopandas as gpd
import numpy as np


def _get_AL(nodes, origin=None, atol=0, rtol=0):
    """
    Create the adjency list of the nodes.

    Nodes are connected if points they have the same position.

    Parameters
    ----------
    nodes: list of tuples
        position of the points
    origin: None or list
        Nodes can only be adjacent if they have different origin. An example of
        origin would be the polygon number.
    atol, rtol: floats
        absolute and relative tolerances, to be passed to np.isclose
    """
    n = len(nodes)
    sorted_index = np.argsort(nodes)
    nodes = np.array(nodes)[sorted_index]

    # initialise adjency lists
    AL = np.zeros(n, set)
    for i in range(n):
        AL[i] = []

    # link lines together
    i = 0
    while i < n - 1:
        end = False
        k = 1
        while (not end) and (i + k < n):
            if np.isclose(nodes[i], nodes[i + k], atol=atol, rtol=0).all():
                a = sorted_index[i]
                b = sorted_index[i + k]
                k += 1
                if origin is not None and origin[a] == origin[b]:
                    continue
                AL[a].append(b)
                AL[b].append(a)
            else:
                end = True
        i += 1
    return AL


def _sort_counterclockwise_points(middle, ref, points):
    """Return index to sort the points in counterclockwise direction."""
    angles = [_get_angle(middle, ref, points[i]) for i in range(len(points))]
    return np.argsort(angles)


def _get_angle(a, b1, b2):
    """
    Return the angle between ab1, ab2.

    Parameters
    ----------
    a, b1, b2:

    Returns
    -------
    angle: float
        angle in radians

    """
    angle1 = np.arctan2(b1[1] - a[1], b1[0] - a[0])
    angle2 = np.arctan2(b2[1] - a[1], b2[0] - a[0])

    angle = angle2 - angle1
    if angle < 0:
        angle = 2 * np.pi + angle
    return angle


def _dict_to_df(landcover_table):
    """Convert a dict landcover table to a df."""
    return gpd.GeoDataFrame.from_dict(landcover_table, orient="index")


def find_duplicate_lines(gdf, remove=False):
    """Find duplicate lines in a GeoDataFrame of lines and return
    a list of indices of duplicated lines.
    """

    gdf_strtree = gdf.sindex

    indices = []
    for i, row in gdf.iterrows():
        possible_matches_index = list(gdf_strtree.intersection(row.geometry.bounds))
        possible_matches = gdf.iloc[possible_matches_index]

        for j, row2 in possible_matches.iterrows():
            if i == j:
                continue
            if row.geometry.equals(row2.geometry):
                pair = sorted([i, j])
                if pair not in indices:
                    indices.append(pair)

    if remove:
        for i, j in indices:
            gdf.drop(i, inplace=True)

    return indices
