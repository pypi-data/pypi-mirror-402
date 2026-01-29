"""Plot the line maps and polygon maps."""

from ._colormaps import COLORMAP_LANDCOVER, colormap_selector
from ._helpers import _get_map_units


def landcover_map(gdf, column="z0", ax=None, **kwargs):
    """
    Plot the polygons in a map colored by a certain field, picking some
    reasonable defaults for the colors and legend

    Parameters
    ----------
    gdf: GeoDataFrame
        the dataframe to plot.
    column:
        The name of the dataframe column to be plotted.
    **kwargs:
        Will be passed to gdf.plot()

    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import matplotlib.ticker as tkr
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    if column == "z0":
        # example how to plot a landcover map including legend
        # this is identical to the colors used in QGIS
        units = _get_map_units(gdf)
        cmap = colormap_selector("z0")
        bounds = list(COLORMAP_LANDCOVER.keys())
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N + 1, extend="both")

        kwargs = {
            **dict(column=column, cmap=cmap, norm=norm),
            **kwargs,
        }
        # plot an roughness map including legend and colorbar
        if ax is None:
            fig, ax = plt.subplots()
        gdf.plot(ax=ax, **kwargs)
        plt.title("")
        plt.xlabel(f"Easting ({units})")
        plt.ylabel(f"Northing ({units})")
        # Create a divider for the existing axes instance
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        cbar = mpl.colorbar.ColorbarBase(
            ax=cax,
            cmap=cmap,
            norm=norm,
            format=tkr.FormatStrFormatter("%.4g"),
            extend="both",
        )
        cbar.set_label("Roughness length (m)")
    else:
        if ax is None:
            fig, ax = plt.subplots()
        gdf.plot(column=column, ax=ax, **kwargs)

    return ax
