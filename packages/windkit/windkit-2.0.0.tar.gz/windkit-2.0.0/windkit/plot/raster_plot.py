# (c) 2022 DTU Wind Energy
"""
Plot raster maps with the ability to add overlays
"""

import geopandas as gpd
import xarray as xr

from ..import_manager import _import_optional_dependency
from ._colormaps import colormap_check, colormap_selector


def raster_plot(
    da,
    contour=None,
    contour_color="white",
    pts=None,
    points_color="red",
    colormap=None,
    color_scale_limits=None,
    plot_title=None,
    **kwargs,
):
    """
    Creates a raster map plot.

    Parameters
    ----------
    da : xarray.DataArray
        WindKit 2d data array in south_north,west_east.

    contour : xarray.DataArray or geopandas.GeoDataFrame
        WindKit 2d array in south_north,west_east or geopandas.GeoDataFrame of lines.

    contour_color : str, optional
        String defining the color of the countor lines, default at "white".
        Strings should define valid CSS-colors.

    pts : xarray.DataArray
        WindKit point data array of points to "highlight" on map

    points_color : str, optional
        String defining the color of points, default at "red".
        Strings should define valid CSS-colors.

    colormap : str, optional
        Matplotlib colormap name. If not provided, this will be:

        - a predefined colormap, if defined for the variable, currently defined for:
          z0meso, site_elev, and speedup and turning variables
        - The default colors for xarray.plot.colormesh: 'viridis' (sequential dataset)
          or 'RdBu_r' (diverging dataset)

    color_scale_limits : array of two floats, optional
        Defines the color scale limits. If not provided the limits will be the minimum
        and the maximum value of 'da'.

    plot_title : str, optional
        Defines the title of the map. If not provided the map won't have title.

    kwargs : dict, optional
        Extra keyword arguments to Matplotlib plotting functions (pcolormesh and contour).

    Returns
    -------
    matplotlib.figure.Figure
        Matplotlib figure for display, additional modification, or output.

    """
    mpl = _import_optional_dependency("matplotlib")
    plt = _import_optional_dependency("matplotlib.pyplot")

    variable = da.name
    da = da.squeeze()

    # Definition of the properties of the pcolormesh plot
    if colormap is None and colormap_check(variable):
        colormap = colormap_selector(variable)

    if color_scale_limits is None:
        color_scale_limits = [da.min(), da.max()]

    if ("speedups" in variable) and (color_scale_limits[0] < 1 < color_scale_limits[1]):
        norm = mpl.colors.CenteredNorm(vcenter=1)
    elif ("turnings" in variable) and (
        color_scale_limits[0] < 1 < color_scale_limits[1]
    ):
        norm = mpl.colors.CenteredNorm(vcenter=0)
    elif variable == "z0meso":
        norm = mpl.colors.LogNorm(
            vmin=color_scale_limits[0], vmax=color_scale_limits[1]
        )
    elif variable == "site_elev":
        norm = mpl.colors.TwoSlopeNorm(
            vmin=color_scale_limits[0] - 1,
            vcenter=color_scale_limits[0] + 0.001,
            vmax=color_scale_limits[1],
        )
    else:
        norm = plt.Normalize(color_scale_limits[0], color_scale_limits[1])

    fig, ax = plt.subplots()

    # set equal aspect for the different layers
    ax.set_aspect("equal")

    fig = da.plot.pcolormesh(ax=ax, cmap=colormap, norm=norm, **kwargs)

    if contour is not None:
        if isinstance(contour, xr.DataArray):
            contour.plot.contour(
                ax=ax, colors=contour_color, add_labels=True, linestyles="-", **kwargs
            )

        elif isinstance(contour, gpd.GeoDataFrame):
            contour.plot(
                ax=ax,
                edgecolor=contour_color,
                linestyles="-",
            )

    if pts is not None:
        plt.plot(pts.west_east, pts.south_north, "or", points_color, ms=8)

    if plot_title is None:
        plt.title("")
    elif plot_title is not None:
        plt.title(plot_title)

    plt.show()
    return fig
