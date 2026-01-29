from windkit.import_manager import _import_optional_dependency


def plot_wind_turbine_locations(wts, ax=None):
    """Plot the locations of the turbines.

    Parameters
    ----------
    ax : matplotlib.pyplot.axis, optional
        axis to use for plotting, by default None, which
        means the current axis is used (via plt.gca())

    Returns
    -------
    matplotlib.pyplot.axis
        Axis used for the plot

    """
    plt = _import_optional_dependency("matplotlib.pyplot")

    if ax is None:
        ax = plt.gca()

    for i, (wtg, pts) in enumerate(wts):
        x, y = pts.west_east, pts.south_north
        ax.scatter(x, y, c=f"C{i}", label=f"{i}: " + str(wtg.name.data))

    # Add turbine id's
    x, y = wts.coords.west_east, wts.coords.south_north
    turbine_id = wts.coords.turbine_id.data
    for i in range(x.size):
        ax.text(x[i], y[i], turbine_id[i], size=12)

    ax.legend(frameon=False)

    ax.set(
        xlabel=pts.west_east.attrs["standard_name"],
        ylabel=pts.south_north.attrs["standard_name"],
    )

    return ax
