# (c) 2022 DTU Wind Energy
"""
Wind rose plotting

In addition to providing a plot for wind drawing wind roses, three pre-defined lists of
wind speed intervals are included to highlight important regions of different IEC class
turbines. These can be used as a starting point for creating your own lists.
"""

import numpy as np

from windkit._errors import IEC_type_error
from windkit.import_manager import _import_optional_dependency
from windkit.plot._helpers import check_multipoint, check_plotting_attrs
from windkit.wind_climate.weibull_wind_climate import is_wwc, wwc_to_bwc

# Predefined wind speed intervals according to each wind turbine class
IEC_I = [0, 4, 6, 9, 12, 16, 20]
IEC_II = [0, 3, 6, 9, 12, 18]
IEC_III = [0, 3, 6, 9, 12, 15]


def _add_wind_speed_intervals(ds, wind_speed_bins):
    """Creation of a new Dataset which includes the information of each wind speed
        interval

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset representation of a binned wind climate

    wind_speed_bins : list of floats
        Represent the wind speed values that define the limits of each interval

    Returns
    -------
    ds_new : xarray.Dataset
        WindKit Dataset representation of a binned wind climate for a single point
        (for the moment) with the wind speed intervals
    """

    wind_speed_intervals = [
        f"{wind_speed_bins[i]} - {wind_speed_bins[i + 1]}"
        for i in range(len(wind_speed_bins) - 1)
    ]

    intervals = {key: [] for key in wind_speed_intervals}

    wsfreq_sect_int = np.full(
        (len(intervals), ds.sizes["sector"]),
        np.nan,
        dtype=ds.wsfreq.dtype,
    )

    for s in range(ds.sizes["sector"]):
        intervals = {key: [] for key in wind_speed_intervals}

        for w in range(ds.sizes["wsbin"]):
            for i in wind_speed_intervals:
                if (
                    float(i[0 : i.index(" ")])
                    <= ds.wsbin[w]
                    < float(i[i.index("-") + 1 :])
                ):
                    intervals[i].append(ds["wsfreq"][w, s].item())

        c = 0
        for i in wind_speed_intervals:
            wsfreq_sect_int[c, s] = np.mean(intervals[i])
            c += 1

        wsfreq_sect_int[:, s] = (
            wsfreq_sect_int[:, s] / np.sum(wsfreq_sect_int[:, s])
        ) * ds.wdfreq[s].item()

    ds_new = ds.expand_dims({"interval": len(intervals)})
    intervals_list = np.array([i for i in intervals])
    ds_new = ds_new.assign_coords({"interval": ("interval", intervals_list)})
    for i in ds:
        ds_new[i] = (ds[i].dims, ds[i].data)

    ds_new = ds_new.drop_vars("wsfreq")
    ds_new = ds_new.drop_vars("wsbin")
    ds_new = ds_new.drop_vars("wsceil")

    if "wsfloor" in ds_new:
        ds_new = ds_new.drop_vars("wsfloor")
    ds_new["ws_range_freq"] = (("interval", "sector"), wsfreq_sect_int)
    return ds_new


def wind_rose(
    ds,
    wind_speed_bins=None,
    style="rose",
    uniform_color="blue",
    cmap="Viridis_r",
    gap=False,
):
    """Create wind rose plot.

    The wind rose can be plotted in two different styles:

    - Simple wind rose which shows information regarding the wind direction for each
      sector.
    - Stacked wind rose which includes information for both the wind direction
      and the wind speed for each sector.

    The type of wind rose is controlled by the ``wind_speed_bins`` input which will
    define the style of the wind rose and, if it is desired, the wind speed intervals
    shown in the wind rose.

    Moreover, by using the style argument, one can define the plotting style of
    the wind rose: radar (line polar plot) or rose.

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset representing a either a binned "histogram" wind climate
        or a weibull wind climate in a single point.

    wind_speed_bins :  list of floats, str, optional
        Can take the following values:

        - None: results in a simple rose representation, representing only the wind
          direction frequency. (Default)
        - List of floats: Manually introduced list where each float defines one limit
          of each wind speed interval.
          e.g: wind_speed_bins = [0, 5.5, 10, 30] would create 3 gorups of
          wind speeds: 0 - 5.5, 5.5 - 10 and 10 - 30. Results in a stacked wind rose.
        - One of three different str ("IEC_I", "IEC_II" or "IEC_III"): Each class has
          predefined wind speed intervals that correspond to the turbine characteristics,
          defined in the plot.wind_rose module. Results in a stacked wind rose.

    style :  str, optional
        Can take the following values:

        - "rose": the plotting style is a rose.
        - "radar": the plotting style is a line polar plot.
          By default is defined as "rose".

    cmap : str, optional
        Determines the sequential color scale when representing the stacked wind rose.
        Strings should define valid built-in sequential color scales' names.
        By default is defined as "Viridis_r".

    uniform_color : str, optional
        Determines the uniform color when representing the simple rose.
        Strings should define valid CSS-colors.
        By default is defined as "blue".

    gap : bool, optional
        Include a gap between sectors? (Default: no gap)

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure for display, additional modification, or output
    """
    px = _import_optional_dependency("plotly.express")
    check_multipoint(ds)

    if is_wwc(ds):  # wwc to wwc if pwc as input
        pwc_pt = ds.squeeze()
        ds = wwc_to_bwc(pwc_pt, np.array(range(31)))

    ds = ds.squeeze()

    if wind_speed_bins is None:
        wind_rose_plot = ds.drop_vars(
            "wsfreq"
        )  # Creation of a new dataset based on ds for ensuring robustness

        wind_rose_plot = wind_rose_plot.drop_vars("wsbin")
        wind_rose_plot = wind_rose_plot.drop_vars("wsceil")

        if "wsfloor" in wind_rose_plot:
            wind_rose_plot = wind_rose_plot.drop_vars("wsfloor")

        color = None
        plot_dist_name = "wdfreq"
        labels = None
        color_scale = [uniform_color]
        custom_data = ["sector", "wdfreq"]
        wdfreq_title = check_plotting_attrs(wind_rose_plot.wdfreq)
        sector_title = check_plotting_attrs(wind_rose_plot.sector)

        hovertemplate = (
            sector_title
            + ": %{customdata[0]}<br>"
            + wdfreq_title
            + ": %{customdata[1]:.3f}"
        )

    else:
        legend_title = "Wind speed range [m/s]"

        if isinstance(wind_speed_bins, str):
            if wind_speed_bins == "IEC_I":
                wind_speed_bins = IEC_I
                legend_title = "IEC I class. Wind speed range [m/s]"

            elif wind_speed_bins == "IEC_II":
                wind_speed_bins = IEC_II
                legend_title = "IEC II class. Wind speed range [m/s]"

            elif wind_speed_bins == "IEC_III":
                wind_speed_bins = IEC_III
                legend_title = "IEC III class. Wind speed range [m/s]"

            else:
                raise IEC_type_error()

        wdfreq_title = check_plotting_attrs(ds.wdfreq)
        sector_title = check_plotting_attrs(ds.sector)

        wind_rose_plot = _add_wind_speed_intervals(ds, wind_speed_bins)
        hovertemplate = (
            sector_title
            + ": %{customdata[0]}<br>"
            + wdfreq_title
            + ": %{customdata[3]:.3f}<br>Wind speed range [m/s]: %{customdata[1]}<br>Probability density as function of wind speed [`%{customdata[3]:.3f}`]: %{customdata[2]:.3f}"
        )
        plot_dist_name = "ws_range_freq"
        color = "interval"
        labels = {
            "interval": legend_title,
        }
        custom_data = ["sector", "interval", "ws_range_freq", "wdfreq"]

        color_scale = [i[1] for i in px.colors.get_colorscale(cmap)]

    plot_dict = {
        "theta": "sector",
        "color": color,
        "r": plot_dist_name,
        "labels": labels,
        "color_discrete_sequence": color_scale,
        "custom_data": custom_data,
    }

    if style == "radar":
        plot_function = px.line_polar
        plot_dict["line_close"] = True

    else:
        plot_function = px.bar_polar

    df = wind_rose_plot.to_dataframe().reset_index().dropna()

    fig1 = plot_function(df, **plot_dict)

    fig1.update_traces(hovertemplate=hovertemplate)

    upd_dict = {"font": {"size": 13}, "hovermode": "closest"}

    if not gap:
        fig1.update_polars(bargap=0)

    return fig1.update_layout(**upd_dict)
