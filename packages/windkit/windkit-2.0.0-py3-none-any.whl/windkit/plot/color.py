"""Helper functions for colors and colormaps."""

import numpy as np

from ..import_manager import _import_optional_dependency


def reformat_colors(colors, output_type=int):
    """
    Conversion to RGB colors.

    Parameters
    ----------
    colors: list of str or tuples of int
        list of RGB colors, 0-255 range RGB colors or HTML format
    output_type: int or float, optional. Default: int
        Whether to write RGB colors in 0-255 or 0-1 range. Chose float to use
        with matplotlib.

    Return
    ------
    colors: list of tuples
        RGB colors
    """
    mplc = _import_optional_dependency("matplotlib.colors")

    reformatted = colors.copy()
    for i, c in enumerate(reformatted):
        try:
            reformatted = np.array(reformatted, dtype=float)
            reformatted[i] = mplc.to_rgb(np.array(c) / 255)
        except (TypeError, ValueError):
            try:
                reformatted[i] = mplc.to_rgb(c)
            except ValueError:
                reformatted[i] = mplc.to_rgb(f"#{c}")
    if output_type is int:
        return _float2int(reformatted)
    elif output_type is float:
        return reformatted
    else:
        raise TypeError(f"Function not implemented for output type {type}")


def _float2int(colors):
    rgb_int = (np.array(colors) * 255).astype(int)
    return [tuple(c) for c in rgb_int]


def _get_valid_color(gdf, ignore_collisions=True):
    """
    Return a color object if the default cmap is appropriate for the gdf.

    Used in map_conversion plots.
    """
    color = Color()
    if ignore_collisions:
        return color
    else:
        try:
            color.match_colors_with_roughness(np.unique(gdf["z0"]))
            return color
        except Exception as e:
            raise Exception(
                "{} {}\n{}".format(
                    "The default colormap and norm of the class is not appropriate.",
                    e,
                    "Please specify a colormap to plot.",
                )
            )


class Color:
    """Class to create and store color dictionnaries and maps.

    Parameters
    ----------
    levels: list of float, optional. Default: None
        List of values marking different color bins, both min and max level should be
        included. If levels is None, a default list of 15 levels from 0 to 1, plus a
        level of 100 is included.
    colors: list of colors (rgb-tuple or html-str), optional. Default: None
        If tuple, should have 3 values, if string should have leading '#'.  List should
        be one less than the number of levels. If None, a default list of 15 colors that
        represent the levels as roughness lengths is provided.

    """

    def __init__(self, levels=None, colors=None):
        if levels is None and colors is None:
            levels = [
                0,
                0.0002,
                0.0003,
                0.001,
                0.005,
                0.008,
                0.01,
                0.03,
                0.05,
                0.1,
                0.2,
                0.4,
                0.5,
                0.8,
                1,
                100,
            ]
            colors = [
                (0, 0, 255),
                (255, 244, 137),
                (255, 255, 255),
                (197, 143, 112),
                (156, 255, 151),
                (167, 167, 167),
                (108, 193, 75),
                (213, 228, 75),
                (161, 191, 11),
                (114, 133, 17),
                (16, 182, 19),
                (255, 175, 1),
                (255, 60, 21),
                (5, 151, 0),
                (0, 95, 9),
            ]
        elif levels is None or colors is None:
            raise Exception(
                "{}{}{}".format(
                    "Either level or color has not been specified. ",
                    "To use default levels and colors do not define any of them. ",
                    "To use custom levels and colors please specify both of them. ",
                )
            )
        self._levels = levels
        self._colors = colors
        self.cmap = None
        self.norm = None
        self.update(self._levels, self._colors)

    @classmethod
    def _from_lc(cls, landcover_table):
        colors = [properties["color"] for properties in landcover_table.values()]
        levels = [properties["z0"] for properties in landcover_table.values()]
        levels, index = np.unique(levels, return_inverse=True)
        colors = reformat_colors(np.array(colors)[index])
        levels = np.concatenate((levels, [100]))
        return cls(levels, colors)

    def get_color_list(self, html=False, index=None):
        """Return a formatted list of colors.

        Parameters
        ----------
        html: bool, optional. Default: False
            If True, the colors will be in html format.
        index: list, optional. Default: None
            If not None, return only the colors at the specified indices.
        """
        if index is None:
            index = list(range(0, len(self._colors)))
        if html:
            return np.array(["%02X%02X%02X" % color for color in self._colors])[index]
        else:
            return [tuple(c) for c in np.array(self._colors)[index]]

    def add_color(self, lower_level, color):
        """
        Add a color to the set.

        Parameters
        ----------
        color : tuple or string
            0-255 RGB color or HTML format.
        lower_bound: float
        """
        i = np.searchsorted(self._levels, lower_level)
        color = reformat_colors([color])[0]
        self._levels = np.insert(self._levels, i, lower_level)
        self._colors = np.insert(self._colors, i, color, axis=0)

    def update(self, levels, colors):
        """Update the ranges and colors of the object."""
        if len(levels) != len(colors) + 1:
            raise ValueError("The number of levels should be the number of colors + 1")
        self._levels = levels
        self._colors = reformat_colors(colors)
        self._update_cmap()

    def _update_cmap(self):
        """Return a colormap and norm using the object colors and levels."""
        mplc = _import_optional_dependency("matplotlib.colors")

        colors = reformat_colors(self._colors, output_type=float)
        self.cmap, self.norm = mplc.from_levels_and_colors(
            self._levels, colors, extend="neither"
        )

    def match_colors_with_roughness(self, z0, html=False, ignore_collisions=True):
        """
        Return the list of colors corresponding to the list of roughness values.

        Parameters
        ----------
        z0 : list of roughness values
        html: bool, optional. Default: False
            If True, the colors will be in html format.
        ignore_collisions: bool, optional. Default: True
            if True, will raise an error if several roughness map to the same
            color.
        """
        index = np.searchsorted(self._levels, z0, side="right") - 1
        colors = self.get_color_list(html=html, index=index)
        if not ignore_collisions:
            self._check_for_duplicates(index, z0)
        return colors

    def _check_for_duplicates(self, index, z0, retrieve=False):
        """Raise an error if a given color is assigned to several roughness values."""
        duplicate_indices = np.argwhere(np.bincount(index) > 1).flatten()
        if len(duplicate_indices) > 0:
            duplicate_roughness = [
                np.sort(np.array(z0)[np.argwhere(index == i).flatten()])
                for i in duplicate_indices
            ]
            duplicate_messages = [
                "roughness values {} assigned to color {}".format(
                    ", ".join(duplicate_roughness[i].astype(str)),
                    self._colors[j],
                )
                for i, j in enumerate(duplicate_indices)
            ]
            error_message = "{}\n{}".format(
                "Several roughness values assigned to the same color:",
                "\n".join(duplicate_messages),
            )
            if retrieve:
                error_message += "\nYou can add level/color pairs using the method add_color or retrieve the landcover as is from the object if you wish."
            raise Exception(error_message)


def _df_to_dict(df):
    """Convert a df landcover table to a dictionary."""
    return {i: {key: df.loc[i, key] for key in df.columns} for i in df.index}
