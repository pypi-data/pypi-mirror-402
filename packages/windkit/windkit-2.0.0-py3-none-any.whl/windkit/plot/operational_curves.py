# (c) 2022 DTU Wind Energy
"""
Wind turbine generator operational curves.
"""

import numpy as np

from ..import_manager import _import_optional_dependency
from ._helpers import _get_num_rows_cols, check_plotting_attrs


def _plot_curve(da, modes, color, x_lims):
    """
    Plots a curve for the dataArray given as input
    """

    px = _import_optional_dependency("plotly.express")

    # Values of the parameter outside operational region:
    if "thrust" in da.name:  # for thrust and thrust coeff
        value = da.min()
    elif "Thrust" in da.name:  # for thrust and thrust coeff
        value = da.min()
    else:  # for power and power coeff
        value = 0.0

    if modes is not None and not isinstance(modes, list):
        param_2 = np.append(
            da.sel(mode=modes), np.array([value, value], dtype=da.dtype)
        )
        param_2 = np.insert(param_2, 0, np.array([value, value], dtype=da.dtype))
        ws = np.append(
            da.wind_speed,
            np.array(
                [da.wind_speed.max() - 0.000001, x_lims[1]], dtype=da.wind_speed.dtype
            ),
        )
        ws = np.insert(
            ws,
            0,
            np.array(
                [x_lims[0], da.wind_speed.min() + 0.000001], dtype=da.wind_speed.dtype
            ),
        )

        da_new = da.sel(mode=modes).expand_dims({"wind_speed_2": len(ws)})
        da_new = da_new.assign_coords({"wind_speed_2": ("wind_speed_2", ws)})
        da_new["param_2"] = (("wind_speed_2"), param_2)

        df_mode = da_new.to_dataframe().reset_index().dropna()
        plot_dict = {
            "x": "wind_speed_2",
            "y": "param_2",
            "custom_data": ["param_2", "wind_speed_2"],
            "color_discrete_sequence": [color],
        }

    elif isinstance(modes, list):
        ws = np.append(
            da.wind_speed,
            np.array(
                [da.wind_speed.max() - 0.000001, x_lims[1]], dtype=da.wind_speed.dtype
            ),
        )
        ws = np.insert(
            ws,
            0,
            np.array(
                [x_lims[0], da.wind_speed.min() + 0.000001], dtype=da.wind_speed.dtype
            ),
        )

        param_2 = np.full((len(da["mode"]), len(ws)), np.nan, dtype=da.dtype)

        for indx, mod in enumerate(modes):
            param_mode = np.append(
                da.sel(mode=mod), np.array([value, value], dtype=da.dtype)
            )
            param_mode = np.insert(
                param_mode, 0, np.array([value, value], dtype=da.dtype)
            )
            param_2[indx] = param_mode

        da_new = da.expand_dims({"wind_speed_2": len(ws)})
        da_new = da_new.assign_coords({"wind_speed_2": ("wind_speed_2", ws)})
        da_new["param_2"] = (("mode", "wind_speed_2"), param_2)
        df_mode = da_new.to_dataframe().reset_index().dropna()

        plot_dict = {
            "x": "wind_speed_2",
            "y": "param_2",
            "custom_data": ["param_2", "wind_speed_2"],
            "color": "mode",
        }

    elif modes is None:
        da = da.squeeze()
        param_mod = np.append(da, [value, value])
        param_mod = np.insert(param_mod, 0, [value, value])
        ws = np.append(da.wind_speed, [da.wind_speed.max() - 0.000001, x_lims[1]])
        ws = np.insert(ws, 0, [x_lims[0], da.wind_speed.min() + 0.000001])

        da_new = da.expand_dims({"wind_speed_2": len(ws)})
        da_new = da_new.assign_coords({"wind_speed_2": ("wind_speed_2", ws)})
        da_new["param_2"] = (("wind_speed_2"), param_mod)

        df_mode = da_new.to_dataframe().reset_index().dropna()
        plot_dict = {
            "x": "wind_speed_2",
            "y": "param_2",
            "custom_data": ["param_2", "wind_speed_2"],
            "color_discrete_sequence": [color],
        }

    fig = px.line(df_mode, **plot_dict)

    yaxes_title = check_plotting_attrs(da)
    xaxes_title = check_plotting_attrs(da["wind_speed"])

    hovertemplate = (
        yaxes_title
        + ": %{customdata[0]:.2f}<br>"
        + xaxes_title
        + ": %{customdata[1]:.2f}"
    )

    fig.update_yaxes(title_text=yaxes_title)
    fig.update_xaxes(title_text=xaxes_title)
    fig.update_traces(hovertemplate=hovertemplate)
    fig = fig.update_layout(hovermode="closest")
    return fig


def _mark_rated(fig, ds, mark_rated, color, row=None, col=None):
    """add vertical line at rated power

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset subset to a single mode
    """
    index_rated = np.where(ds.power_output >= (mark_rated * ds.rated_power))[0][0]
    ds = ds.isel(wind_speed=index_rated)
    fig.add_shape(
        type="line",
        x0=float(ds.wind_speed),
        x1=float(ds.wind_speed),
        y0=0,
        y1=float(ds.power_output),
        line=dict(color=color, width=2, dash="dash"),
        row=row,
        col=col,
    )


def single_curve(
    da,
    style="faceted",
    color="dodgerblue",
    share_yaxes=True,
    x_axis_range=[0.0, 30.0],
    title=None,
):
    """
    Plots the curve of the given input data variable among the wind speed for
    the different wind turbine modes if there are any.

    Parameters
    ----------
    da : xarray.DataArray
        DataArray representing a data variable from a wind turbine generator
        Dataset
    style : str, optional
        Can take the following values, default is "faceted":

        - "faceted" :  A single plot showing a curve for each wind turbine mode
          as a separate sub-plot. The layout of the plot is designed to keep
          the plot "square".

        - "combined" : Returns a multi line plot showing a curve for each wind
          turbine mode.
    color : list of str, optional
        Determines the color used for the the curves, default is "dodgerblue".
        When plotting with "combined" style, this defines the color of
        the first curve, the other curve colors are assignated automatically.
        Strings should define valid CSS-colors.
    share_yaxes : bool, optional
        Link y-axis values and labels across subplots?, default True
    x_axis_range : list of floats, optional
        Defines the x axis range. By default the axis range is [0., 30.]
    title : str, optional
        Sets the title for the plot. Needs to be defined by the user, default None

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure for display, additional modification, or output

    """
    plotly = _import_optional_dependency("plotly")
    make_subplots = plotly.subplots.make_subplots

    if "mode" in da.dims:
        num_modes = len(da["mode"])
    else:
        num_modes = 1

    da = da.squeeze()
    yaxes_title = check_plotting_attrs(da)
    xaxes_title = check_plotting_attrs(da["wind_speed"])

    if share_yaxes:
        share_Yaxes = "all"
    else:
        share_Yaxes = None

    if num_modes >= 2:
        if style == "faceted":
            num_rows, num_cols = _get_num_rows_cols(num_modes)
            fig = make_subplots(
                rows=num_rows,
                cols=num_cols,
                subplot_titles=[f"{i}" for i in da["mode"].values],
                shared_yaxes=share_Yaxes,
                y_title=yaxes_title,
                x_title=xaxes_title,
            )
            col_num = 0
            row_num = 1

            for i in range(num_modes):
                if col_num < num_cols:
                    col_num += 1
                else:
                    row_num += 1
                    col_num = 1

                mode = da.mode[i].item()
                fig_mode = _plot_curve(da, mode, color, x_axis_range)

                for traces in fig_mode["data"]:
                    fig.add_trace(traces, row=row_num, col=col_num)

            fig.update_layout(hovermode="closest")

        elif style == "combined":
            mode = [str(i) for i in da["mode"].values]
            fig = _plot_curve(da, mode, color, x_axis_range)

    else:
        mode = None
        fig = _plot_curve(da, mode, color, x_axis_range)

    fig.update_xaxes(range=x_axis_range)
    return fig.update_layout(title_text=title, hovermode="closest")


def power_ct_curves(
    ds,
    color=["red", "dodgerblue"],
    mark_rated=0.995,
    share_yaxes=True,
    x_axis_range=[0.0, 30.0],
    title=False,
):
    """
    Plots the electrical power output and thrust coefficient curves for the different
    wind turbine modes if there are any. If there is more than one
    mode, a single plot showing the curves for each wind turbine mode as a
    separate sub-plot is displayed. If just a mode is studied, a single plot
    showing the curves is displayed.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset representing a wind turbine generator, must have ``mode`` dimension
    color : list of str, optional
        Determines the color used for the both curves. The first element defines
        the color for the power curve and the second for the thrust coefficient
        one. Default is ["red", "dodgerblue"].
        Strings should define valid CSS-colors.
    mark_rated : float, optional
        Draw a line at fraction of rated power. Set to 0 or False to not display at all.
    share_yaxes : bool, optional
        Link y-axis values across subplots?, default True
    x_axis_range : list of floats, optional
        Defines the x axis range. By default the axis range is [0, 30]
    title : bool, optional
        Should the wind turbine model be added as title, default False

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure for display, additional modification, or output

    """
    _import_optional_dependency("plotly.subplots")
    plotly = _import_optional_dependency("plotly")
    make_subplots = plotly.subplots.make_subplots

    if share_yaxes:
        share_Yaxes = "all"
        showLabel = True
    else:
        share_Yaxes = None
        showLabel = None

    if "mode" in ds.dims:
        num_modes = len(ds["mode"])
    else:
        num_modes = 1

    xaxes_title = check_plotting_attrs(ds["wind_speed"])

    title_name = None
    ds = ds.squeeze()
    if title:
        title_name = ds.name.item()

    if num_modes >= 2:
        num_rows, num_cols = _get_num_rows_cols(num_modes)

        specs = [
            [{"secondary_y": True} for x in range(num_cols)] for x in range(num_rows)
        ]
        fig = make_subplots(
            rows=num_rows,
            cols=num_cols,
            subplot_titles=[f"{i}" for i in ds["mode"].values],
            specs=specs,
            shared_yaxes=share_Yaxes,
            x_title=xaxes_title,
        )
        col_num = 0
        row_num = 1

        for i in range(num_modes):
            if col_num < num_cols:
                col_num += 1
            else:
                row_num += 1
                col_num = 1
            mode = ds.mode[i].item()
            yaxes_title = []
            for j in range(2):
                if j == 0:
                    dss = ds.power_output
                    unif_color = color[0]
                    sec_y = False
                elif j == 1:
                    dss = ds.thrust_coefficient
                    unif_color = color[1]
                    sec_y = True
                fig_mode = _plot_curve(dss, mode, unif_color, x_axis_range)
                yaxes_title.append(fig_mode["layout"]["yaxis"]["title"]["text"])
                for traces in fig_mode["data"]:
                    fig.add_trace(traces, row=row_num, col=col_num, secondary_y=sec_y)
                fig.update_yaxes(
                    secondary_y=sec_y,
                    row=row_num,
                    col=col_num,
                    showticklabels=showLabel,
                    color=unif_color,
                )

            if mark_rated:
                _mark_rated(
                    fig, ds.isel(mode=i), mark_rated, color[0], row_num, col_num
                )

        # Add global y-axis labels
        fig.add_annotation(
            x=-0.1,
            y=0.5,
            text=yaxes_title[0],
            font=dict(color=color[0], size=14),
            textangle=-90,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
        fig.add_annotation(
            x=1.02,
            y=0.5,
            text=yaxes_title[1],
            font=dict(color=color[1], size=14),
            textangle=-90,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
    else:
        mode = None
        if title:
            title_name = ds.name.item()
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for j in range(2):
            if j == 0:
                dss = ds.power_output
                unif_color = color[0]
                sec_y = False
            elif j == 1:
                dss = ds.thrust_coefficient
                unif_color = color[1]
                sec_y = True
            fig_single = _plot_curve(dss, mode, unif_color, x_axis_range)
            yaxes_title = fig_single["layout"]["yaxis"]["title"]["text"]
            for traces in fig_single["data"]:
                fig.add_trace(traces, secondary_y=sec_y)
            fig.update_yaxes(
                title_text=yaxes_title, secondary_y=sec_y, color=unif_color
            )
        fig.update_xaxes(title_text=xaxes_title)
        if mark_rated:
            _mark_rated(fig, ds, mark_rated, color[0])

    fig.update_yaxes(rangemode="tozero")
    fig.update_xaxes(range=x_axis_range)
    return fig.update_layout(title_text=title_name, hovermode="closest")
