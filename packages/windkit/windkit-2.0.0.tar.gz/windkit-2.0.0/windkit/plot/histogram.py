# (c) 2022 DTU Wind Energy
"""
Weibull distribution and histograms plotting
All sector distribution plotting
"""

import numpy as np

from windkit.import_manager import _import_optional_dependency
from windkit.plot._helpers import (
    _get_num_rows_cols,
    check_multipoint,
    check_plotting_attrs,
)
from windkit.plot.wind_rose import wind_rose
from windkit.weibull import get_weibull_probability
from windkit.wind_climate.binned_wind_climate import validate_bwc, weibull_fit
from windkit.wind_climate.weibull_wind_climate import is_wwc, wwc_to_bwc


def _plot_weibull(df_sector, da_sector, sector, uniform_color, weibull, gap):
    """
    Plots the weibull distribution and histogram for a sector
    """
    px = _import_optional_dependency("plotly.express")
    go = _import_optional_dependency("plotly.graph_objects")

    # Weibull plot properties
    plot_fun_histogram = px.bar
    plot_histogram_dict = {
        "x": "wsbin",
        "y": "wsfreq",
        "custom_data": ["wsbin", "wsfreq"],
        "title": f"{sector}°",
        "color_discrete_sequence": [uniform_color],
    }

    # Histogram
    fig_weibull = plot_fun_histogram(df_sector, **plot_histogram_dict)
    yaxes_title = check_plotting_attrs(da_sector)
    xaxes_title = check_plotting_attrs(da_sector["wsbin"])

    hovertemplate_hist = (
        yaxes_title
        + ": %{customdata[1]:.2f}<br>"
        + xaxes_title
        + ": %{customdata[0]:.2f}"
    )

    fig_weibull.update_yaxes(title_text=yaxes_title)
    fig_weibull.update_xaxes(title_text=xaxes_title)
    fig_weibull.update_traces(hovertemplate=hovertemplate_hist)

    if not gap:
        fig_weibull = fig_weibull.update_layout(bargap=0)

    # Weibull
    if weibull or (weibull is None and "A" in df_sector):
        A = float(df_sector.A.sample(1).iloc[0])
        k = float(df_sector.k.sample(1).iloc[0])
        speeds, prob = get_weibull_probability(
            A, k, [np.floor(df_sector.wsbin.min()), np.ceil(df_sector.wsbin.max())]
        )
        name = f"A = {A:.2f}, k = {k:.2f}"

        hovertemplate_weib = yaxes_title + ": %{y:.2f}<br>" + xaxes_title + ": %{x:.2f}"

        fig_weibull.add_trace(
            go.Scatter(x=speeds, y=prob, name=name, hovertemplate=hovertemplate_weib)
        )

    fig_weibull = fig_weibull.update_layout(hovermode="closest")
    return fig_weibull


def _plot_emergent_curve(ds):
    """
    Calculate and plot the emergent probability from a Binned wind climate at
    a single point.
    """
    go = _import_optional_dependency("plotly.graph_objects")

    speeds_vect = np.linspace(
        float(np.floor(ds.wsbin.min())), float(np.ceil(ds.wsbin.max())), 250
    )

    tot_prob_speed_all_Sect = np.full(
        len(speeds_vect),
        0.0,
        dtype="f",
    )
    wwc = weibull_fit(ds)  # wwc of same spatial extent as the input
    ds["A"] = wwc["A"]
    ds["k"] = wwc["k"]

    for indx, wsi in enumerate(speeds_vect):
        for si in range(len(ds["sector"])):
            A = ds.isel(sector=si).A
            k = ds.isel(sector=si).k
            freq = ds.isel(sector=si).wdfreq
            speeds, prob_speed_sect_Sect = get_weibull_probability(
                A, k, [wsi], single_speed=True
            )
            tot_prob_speed_all_Sect[indx] = (
                tot_prob_speed_all_Sect[indx] + freq * prob_speed_sect_Sect[0]
            )

    # Ploting
    yaxes_title = "Emergent frequency per wind_speed [1]"
    xaxes_title = check_plotting_attrs(
        ds["wsbin"]
    )  # Just checking for "wsbin" attrs, not for the calculated "emergent_prob".
    hovertemplate_emerg = yaxes_title + ": %{y:.2f}<br>" + xaxes_title + ": %{x:.2f}"
    title = "All sectors"
    fig_emergent = go.Figure()
    fig_emergent.add_trace(
        go.Scatter(
            x=speeds_vect,
            y=tot_prob_speed_all_Sect,
            name="Emergent distribution",
            hovertemplate=hovertemplate_emerg,
        )
    )

    fig_emergent.update_layout(
        title=title,
        xaxis_title=xaxes_title,
        yaxis_title=yaxes_title,
        hovermode="closest",
        showlegend=False,
    )

    return fig_emergent


def _dash_app_layout(df, app):
    dcc = _import_optional_dependency("dash.dcc")
    html = _import_optional_dependency("dash.html")

    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Br(),
                    html.Div(
                        "Select or deselect the sectors to be displayed on the wind rose:"
                    ),
                    html.Br(),
                    dcc.Dropdown(
                        id="sector_selection",
                        options=[{"label": f"{i}", "value": i} for i in df["sector"]],
                        value=df["sector"],
                        multi=True,
                        style={"width": "75%"},
                    ),
                ]
            ),
            html.Br(),
            html.Br(),
            html.Div(
                [
                    dcc.Graph(
                        id="wind_rose",
                        hoverData={"points": [{"theta": 0}]},
                        figure={},
                    )
                ],
                style={
                    "width": "50%",
                    "display": "inline-block",
                    "padding": "0.20",
                },
            ),
            html.Div(
                [
                    dcc.Graph(id="weibull_distribution"),
                ],
                style={
                    "width": "50%",
                    "display": "inline-block",
                    "padding": "0.20",
                },
            ),
        ]
    )
    return app


def histogram_lines(ds, colors="Phase", gap=False):
    """
    Create a "distribution" plot and matching frequency wind rose for binned wind climate.

    The distribution plot is created by drawing lines across the wind speed bins for each
    sector.

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Dataset at a single point representing either a binned or weibull wind
        climate.

    colors : str, optional
        str defining a valid plotly built-in color scale (preferred cyclical) name
        By default is defined as "Phase".

    gap : bool, optional
        Include or not gap between sectors
        By default is defined no False.

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure for display, additional modification, or output.
    """

    check_multipoint(ds)
    px = _import_optional_dependency("plotly.express")
    _import_optional_dependency("plotly.subplots")
    plotly = _import_optional_dependency("plotly")
    make_subplots = plotly.subplots.make_subplots

    if is_wwc(ds):  # wwc (wwc) to bwc if wwc (wwc) as input
        wwc_pt = ds.squeeze()
        ds = wwc_to_bwc(wwc_pt, np.array(range(31)))
    if "wsfloor" in ds:
        ds = ds.drop_vars("wsfloor")

    # Prepare data
    ds = ds.squeeze()
    dff = ds.to_dataframe().reset_index().dropna()

    ## Wind rose plot ##
    color_scale = [i[1] for i in px.colors.get_colorscale(colors)]
    adjusted_color_scale = px.colors.sample_colorscale(color_scale, len(ds.sector) + 1)
    fig_rose = wind_rose(ds, uniform_color=adjusted_color_scale)

    ## Wind distribution plot ##
    # Plot propertiees
    plot_fun_lines = px.line
    plot_lines_dict = {
        "x": "wsbin",
        "y": "wsfreq",
        "custom_data": ["wsbin", "wsfreq", "sector"],
        "color": "sector",
    }

    plot_lines_dict["color"] = [str(i) for i in dff["sector"]]
    plot_lines_dict["color_discrete_sequence"] = adjusted_color_scale

    fig_distr = plot_fun_lines(dff, **plot_lines_dict)

    da_sector = ds.isel(sector=0).wsfreq  # All the sectors have same attrs for wsfreq
    yaxes_title = check_plotting_attrs(da_sector)
    xaxes_title = check_plotting_attrs(da_sector["wsbin"])

    hovertemplate = (
        "Sector center angle: %{customdata[2]}°<br>"
        + yaxes_title
        + ": %{customdata[1]:.2f}<br>"
        + xaxes_title
        + ": %{customdata[0]:.2f}"
    )

    # Subplots
    fig_subplots = make_subplots(
        rows=1, cols=2, specs=[[{"type": "polar"}, {"type": "xy"}]]
    )

    for traces in fig_rose["data"]:
        fig_subplots.add_trace(traces, row=1, col=1)
    for traces in fig_distr["data"]:
        fig_subplots.add_trace(traces, row=1, col=2)

    if not gap:
        fig_withoutWeibull = fig_subplots.update_polars(
            angularaxis_rotation=90, angularaxis_direction="clockwise", bargap=0
        )

    else:
        fig_withoutWeibull = fig_subplots.update_polars(
            angularaxis_rotation=90, angularaxis_direction="clockwise"
        )

    fig_withoutWeibull.update_yaxes(title_text=yaxes_title, row=1, col=2)
    fig_withoutWeibull.update_xaxes(title_text=xaxes_title, row=1, col=2)
    fig_withoutWeibull.update_traces(hovertemplate=hovertemplate, row=1, col=2)

    fig_withoutWeibull.update_layout(
        legend=dict(
            title="Sector center angle [°]",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
        ),
        hovermode="closest",
    )
    return fig_withoutWeibull


def histogram(
    ds,
    style="faceted",
    color="dodgerblue",
    weibull=None,
    emergent_distribution=False,
    gap=False,
    share_yaxes=True,
    share_xaxes=True,
):
    """
    Plot the histogram represented in a binned wind climate.

    Has the option to include the weibull distribution represented as a line over top of
    the histogram to qualitatively evaluate the goodness of fit.

    Parameters
    ----------
    ds : xarray.Dataset
        WindKit Binned wind climate at a single point, optionally with weibull parameters
        (A & k) if the weibull fit overlay is desired.

    style : str or list of floats, optional
        Can take the following values, default is "faceted" (note that "list" is enforced for
        single sector datasets, returning the first plot):

        - "faceted" :  A single plot showing each sector as a separate sub-plot. The
          layout of the plot is designed to keep the plot "square".

        - "interactive" : Creates a Dash interactive plot that shows both the distribution
          and wind rose, hovering over different sectors in the wind rose will show
          the corresponding distribution plot

        - "list" : Returns a list of plotly figures, one for each sector

    color : str, optional
        Determines the color used for the histogram bars, default is "dodgerblue".
        Strings should define valid CSS-colors.

    weibull : bool, optional
        Should the weibull plot be drawn, default is None:

        - True : Add weibull using A & k from dataset if there, otherwise fit a weibull
          and use that for plotting

        - False : Don't add weibull to plot

        - None : Add weibull if A & k are in dataset

    emergent_distribution : bool, optional
        Should the emergent distribution be drawn, default is False:

        - True : Returns only the emergent distribution plot, ignoring the style
          and weibull arguments

        - False : Don't plot the emergent distribution

    gap : bool, optional
        Include a gap between sectors (True), default is False

    share_yaxes : bool, optional
        Link y-axis values and labels across subplots?, default True

    share_xaxes : bool, optional
        Link x-axis values and labels across subplots?, default True

    Returns
    -------
    plotly.graph_objects.Figure if style is "faceted" or "emergent_distribution" is True
        Plotly figure for display, additional modification, or output

    dash.dash.Dash object if style is "interactive"
        Dash app (interactive plot) for display, additional modification, or output

    List of plotly.graph_objects.Figure if style is "list"
        List of Plotly figures for display, additional modification, or output
    """
    check_multipoint(ds)

    validate_bwc(ds)  # Check if the input is actually a bwc, if not breaks
    plotly_subplots = _import_optional_dependency("plotly.subplots")
    make_subplots = plotly_subplots.make_subplots
    dash = _import_optional_dependency("dash")
    Input = dash.dependencies.Input
    Output = dash.dependencies.Output

    if emergent_distribution:
        return _plot_emergent_curve(ds)

    if weibull and ("A" or "k" not in ds.data_vars):
        wwc = weibull_fit(ds)  # wwc of same spatial extent as the input
        ds["A"] = wwc["A"]
        ds["k"] = wwc["k"]

    is_single_sector = ds.sizes["sector"] == 1
    if not is_single_sector:
        ds = ds.squeeze()

    # Prepare data
    dss = ds.drop_vars("wsfreq")
    dss = dss.drop_vars("wsbin")
    dss = dss.drop_vars("wsceil")
    if "wsfloor" in dss:
        dss = dss.drop_vars("wsfloor")

    df = dss.to_dataframe().reset_index().dropna()
    dff = ds.to_dataframe().reset_index().dropna()

    if style == "list" or is_single_sector:
        figs = []
        for i in range(len(ds.sector)):
            df_sector = dff.copy()
            df_sector = df_sector[df_sector["sector"] == dss.sector[i].item()]
            da_sector = ds.isel(sector=i).wsfreq
            fig_weibull = _plot_weibull(
                df_sector, da_sector, dss.sector[i].item(), color, weibull, gap
            )

            fig_weibull.update_layout(
                legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
            )

            figs.append(fig_weibull)

        return figs if not is_single_sector else figs[0]

    elif style == "interactive":
        Dash = _import_optional_dependency("jupyter_dash.JupyterDash", "dash")

        #### Interactive dash Weibull distribution plots #####
        app = Dash(__name__)

        # App layout
        app = _dash_app_layout(df, app)

        # Connect Plotly graphs with Dash Components
        @app.callback(
            Output(component_id="wind_rose", component_property="figure"),
            [Input(component_id="sector_selection", component_property="value")],
        )
        def update_wind_rose(sectors_selected):
            dsss = ds.sel(sector=sectors_selected)
            fig_wind_rose = wind_rose(dsss, uniform_color=color, gap=gap)

            fig_wind_rose.update_layout(margin={"l": 0, "b": 0, "t": 90, "r": 0})

            if gap:
                fig_wind_rose.update_polars(bargap=1)

            return fig_wind_rose

        @app.callback(
            Output(component_id="weibull_distribution", component_property="figure"),
            [Input(component_id="wind_rose", component_property="hoverData")],
        )
        def update_weibull_distribution(hoverData):
            sector = hoverData["points"][0]["theta"]
            df_sector = dff.copy()
            df_sector = df_sector[df_sector["sector"] == sector]
            indx = np.where(ds.sector.values == sector)
            da_sector = ds.isel(sector=indx[0][0]).wsfreq

            fig_weibull = _plot_weibull(
                df_sector, da_sector, sector, color, weibull, gap
            )
            fig_weibull.update_layout(
                legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
            )

            fig_weibull.update_layout(margin={"l": 0, "b": 0, "t": 90, "r": 0})

            return fig_weibull

        return app

    elif style == "faceted":
        if share_yaxes:
            share_Yaxes = "all"
        else:
            share_Yaxes = None

        if share_xaxes:
            share_Xaxes = "all"
        else:
            share_Xaxes = None
        da_sector = ds.isel(sector=1).wsfreq
        yaxes_title = check_plotting_attrs(da_sector)
        xaxes_title = check_plotting_attrs(da_sector["wsbin"])

        num_plots = len(dss["sector"])
        num_rows, num_cols = _get_num_rows_cols(num_plots)

        fig_subplots = make_subplots(
            rows=num_rows,
            cols=num_cols,
            subplot_titles=[f"{i}°" for i in dss["sector"].values],
            shared_yaxes=share_Yaxes,
            shared_xaxes=share_Xaxes,
            y_title=yaxes_title,
            x_title=xaxes_title,
        )
        col_num = 0
        row_num = 1

        for i in range(len(dss["sector"])):
            if col_num < num_cols:
                col_num += 1
            else:
                row_num += 1
                col_num = 1

            df_sector = dff.copy()
            df_sector = df_sector[df_sector["sector"] == dss.sector[i].item()]
            da_sector = ds.isel(sector=i).wsfreq
            fig_weibull = _plot_weibull(
                df_sector, da_sector, dss.sector[i].item(), color, weibull, gap
            )

            for traces in fig_weibull["data"]:
                fig_subplots.add_trace(traces, row=row_num, col=col_num)

            fig_subplots.update_layout(hovermode="closest", showlegend=True)

            if not gap:
                fig_subplots = fig_subplots.update_layout(bargap=0)
        return fig_subplots
