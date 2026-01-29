# (c) 2022 DTU Wind Energy
"""
Generic default colormap module
"""

import json
from pathlib import Path

import numpy as np

with open(
    Path(__file__).resolve().parents[1] / "data" / "color_table_roughness.json"
) as json_file:
    COLORMAP_LANDCOVER = json.load(json_file)
    COLORMAP_LANDCOVER = {float(k): v for k, v in COLORMAP_LANDCOVER.items()}

# Lazy-initialized colormap dictionary
_colormaps_dict = None


def _get_colormaps_dict():
    """Lazily initialize colormaps_dict on first access."""
    global _colormaps_dict
    if _colormaps_dict is not None:
        return _colormaps_dict

    import matplotlib as mpl
    import matplotlib.pyplot as plt

    colors_undersea = plt.cm.terrain(np.linspace(0, 0.17, 256))
    colors_land = plt.cm.terrain(np.linspace(0.25, 1, 256))
    elev_colors = np.vstack((colors_undersea, colors_land))
    colors_roughness = mpl.colors.ListedColormap(COLORMAP_LANDCOVER.values())

    _colormaps_dict = {
        "z0meso": mpl.colors.LinearSegmentedColormap.from_list(
            "",
            [
                "#2A479E",
                "#0DCF69",
                "#F9FA96",
                "#A8906A",
                "#006600",
            ],
        ),
        "user_def_speedups": "coolwarm",
        "orographic_speedups": "coolwarm",
        "obstacle_speedups": "coolwarm",
        "roughness_speedups": "coolwarm",
        "user_def_turnings": "coolwarm",
        "orographic_turnings": "coolwarm",
        "obstacle_turnings": "coolwarm",
        "roughness_turnings": "coolwarm",
        "site_elev": mpl.colors.LinearSegmentedColormap.from_list("", elev_colors),
        "z0": colors_roughness,
    }
    return _colormaps_dict


def colormap_check(key):
    return key in _get_colormaps_dict()


def colormap_selector(key):
    return _get_colormaps_dict()[key]
