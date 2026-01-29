from ._helpers import _get_map_units


def elevation_map(gdf, column="elev", **kwargs):
    """
    Plot the elevation contours in a map colored by a certain field, picking some
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
    import matplotlib.pyplot as plt

    if column == "elev":
        units = _get_map_units(gdf)

        # default for keyword arguments passed to plot
        kwargs = {
            **dict(column=column, cmap="terrain", linewidth=0.5),
            **kwargs,
        }

        # plot a elevation map including legend and colorbar
        fig, ax = plt.subplots()
        gdf.plot(ax=ax, **kwargs)
        plt.title("Elevation contour map")
        plt.xlabel(f"Easting ({units})")
        plt.ylabel(f"Northing ({units})")
        sm = plt.cm.ScalarMappable(
            cmap="terrain",
            norm=plt.Normalize(vmin=gdf[column].min(), vmax=gdf[column].max()),
        )
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax)
        cbar.set_label("Elevation (m)")
    else:
        fig, ax = plt.subplots()
        gdf.plot(column=column, ax=ax, **kwargs)

    return ax
