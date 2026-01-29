# (c) 2022 DTU Wind Energy
"""

Roughness rose plotting
"""

import numpy as np

from ..import_manager import _import_optional_dependency
from ._helpers import check_multipoint, check_plotting_attrs


def _add_plot_dist(ds):
    """Calculate the width of each roughness level for every sector and add it to
    the Dataset

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset representation of a binned wind climate for a single point
        (for the moment)

    Returns
    -------
    ds : xarray.Dataset
        WindKit Dataset representation of a binned wind climate for a single point
        (for the moment)
    """
    max_dist = max(float(ds.dist.max()) * 1.1, 15_000)

    plot_dist = np.full(
        (ds.sizes["sector"], ds.sizes["max_rou_changes"] + 2),
        np.nan,
        dtype=ds.dist.dtype,
    )
    dist_from_origin = np.full(
        (ds.sizes["sector"], ds.sizes["max_rou_changes"] + 1),
        np.nan,
        dtype=ds.dist.dtype,
    )
    plot_dist[:, 0] = 0.0
    for s in range(ds.sizes["sector"]):
        nrch = ds.nrch.values[s]
        plot_dist[s, 1 : nrch + 1] = ds.dist.values[s, 0:nrch]  # rl changes
        plot_dist[s, nrch + 1] = max_dist  # No more rl changes

    ds["plot_dist"] = (ds.z0.dims, np.round(np.diff(plot_dist)))

    for s in range(ds.sizes["sector"]):
        for indx in range(len(ds["plot_dist"][s, :])):
            if not np.isnan(ds["plot_dist"][s, indx]):
                dist_from_origin[s, indx] = np.sum(ds["plot_dist"][s, 0 : indx + 1])

    ds["dist_from_origin"] = (ds.z0.dims, np.round(dist_from_origin))
    return ds


def _add_log_z0(ds):
    """Create a logarithmic scale of the roughness levels for every sector and add it
    to the Dataset

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset representation of a binned wind climate for a single point (for
        the moment)

     Returns
    -------
    ds : xarray.Dataset
        WindKit Dataset representation of a binned wind climate for a single point
        (for the moment)
    """
    log_z0 = np.full(
        (ds.sizes["sector"], ds.sizes["max_rou_changes1"]),
        np.nan,
        dtype=ds.dist.dtype,
    )

    for s in range(ds.sizes["sector"]):
        for r in range(ds.sizes["max_rou_changes1"]):
            if ds.z0[s, r] != 0:
                log_z0[s, r] = np.log(ds.z0[s, r])
            else:
                log_z0[s, r] = ds.z0[s, r]

    ds["log_z0"] = (ds.z0.dims, log_z0)
    return ds


def roughness_rose(ds, style="rose", gap=False):
    """Create roughness rose plot.

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset representation of a roughness rose single point (for the moment).
    style : str, optional
        stacked "bar" plot or circular "rose" plot, by default "rose".
    gap : bool, optional
        Include a gap between sectors? (Default: no gap).

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure for display, additional modification, or output.
    """
    px = _import_optional_dependency("plotly.express")
    plotly = _import_optional_dependency("plotly")
    hex_to_rgb = plotly.colors.hex_to_rgb

    ds = ds.transpose(..., "sector", "max_rou_changes1", "max_rou_changes").squeeze()

    check_multipoint(ds)

    ds = _add_plot_dist(ds)
    rou_rose_plot = _add_log_z0(ds)[["z0", "plot_dist", "log_z0", "dist_from_origin"]]

    df = rou_rose_plot.to_dataframe().reset_index().dropna()

    if style == "bar":
        plot_fun = px.bar
        plot_sect_name = "y"
        plot_dist_name = "x"
        orientation = "h"

    elif style == "rose":
        plot_fun = px.bar_polar
        plot_sect_name = "theta"
        plot_dist_name = "r"

    else:
        raise ValueError('Unknown plot style, please choose one of "bar" or "rose"')

    z0_title = check_plotting_attrs(rou_rose_plot.z0)
    distance_title = check_plotting_attrs(ds.dist)
    sector_title = check_plotting_attrs(rou_rose_plot.sector)
    hovertemplate = (
        sector_title
        + ": %{customdata[1]}<br>"
        + z0_title
        + ": %{customdata[0]:.3f}<br>"
        + distance_title
        + ": %{customdata[3]}<br>Width of roughness level [m]: %{customdata[2]}"
    )

    plot_dict = {
        plot_sect_name: "sector",
        plot_dist_name: "plot_dist",
        "color": "log_z0",
        "labels": {"sector": sector_title, "plot_dist": distance_title},
        "color_continuous_scale": [
            (0, f"rgb{hex_to_rgb('#2A479E')}"),
            (0.3, f"rgb{hex_to_rgb('#0DCF69')}"),
            (0.6, f"rgb{hex_to_rgb('#F9FA96')}"),
            (0.75, f"rgb{hex_to_rgb('#A8906A')}"),
            (1.0, f"rgb{hex_to_rgb('#006600')}"),
        ],
        "range_color": [np.log(0.0002), np.log(3.0)],
        "custom_data": [
            "z0",
            "sector",
            "plot_dist",
            "dist_from_origin",
        ],  # Data for the hover info
    }

    if style == "bar":
        plot_dict["orientation"] = orientation

    fig1 = plot_fun(df, **plot_dict)

    ticks = [0.0002, 0.03, 0.1, 0.4, 1.5]
    upd_dict = {
        "font": {"size": 13},
        "coloraxis_colorbar": dict(
            title="z0 [m]",
            tickvals=np.array(np.log(np.array(ticks))),
            ticktext=[f"{i:g}" for i in ticks],
        ),
    }

    if not gap:
        if style == "bar":
            upd_dict["bargap"] = 0

        elif style == "rose":
            fig1.update_polars(bargap=0)

    fig1.update_layout(**upd_dict)

    return fig1.update_traces(hovertemplate=hovertemplate)
