# (c) 2022 DTU Wind Energy
"""
Wind speed time-series plotting including wind speed and wind direction
"""

__all__ = ["time_series"]

# Check time series with range slider for subplots

import numpy as np
import pandas as pd
import xarray as xr

from ..import_manager import _import_optional_dependency
from ._helpers import check_multipoint, check_plotting_attrs


def _missing_data(ds):
    """
    Identifies if the data has gaps and returns a new xarray.Dataset or
    xarray.DataArray with the mising values added equal to NaN.
    """
    t_to_round = ds.time.values + np.timedelta64(500, "ms")
    ds = ds.assign_coords({"time": t_to_round.astype(dtype="datetime64[m]")})
    if isinstance(ds, xr.Dataset):
        if True in np.isnan(ds.to_array().data):  # there's already nan values in data
            ds_new = ds.expand_dims({"time_2": len(ds.time.values)})
            ds_new = ds_new.assign_coords({"time_2": ("time_2", ds.time.values)})

            ds_new["wind_speed_2"] = (("time_2"), ds.wind_speed.values)
            ds_new["wind_direction_2"] = (("time_2"), ds.wind_direction.values)
            ds_new = ds_new.drop_vars("time")
            ds_new = ds_new.drop_vars("wind_speed")
            ds_new = ds_new.drop_vars("wind_direction")
        else:
            time_complete = np.array(
                pd.date_range(ds.time[0].values, ds.time[-1].values, freq="10min")
            )
            ws_complete = np.empty(len(time_complete))
            wd_complete = np.empty(len(time_complete))
            ws_complete[:] = np.nan
            wd_complete[:] = np.nan
            check = np.isin(time_complete, ds.time)
            indxs = np.where(check)[0]
            np.put(ws_complete, indxs, ds.wind_speed.values)
            np.put(wd_complete, indxs, ds.wind_direction.values)

            ds_new = ds.expand_dims({"time_2": len(time_complete)})
            ds_new = ds_new.assign_coords({"time_2": ("time_2", time_complete)})

            ds_new["wind_speed_2"] = (("time_2"), ws_complete)
            ds_new["wind_direction_2"] = (("time_2"), wd_complete)
            ds_new = ds_new.drop_vars("time")
            ds_new = ds_new.drop_vars("wind_speed")
            ds_new = ds_new.drop_vars("wind_direction")

    if isinstance(ds, xr.DataArray):
        if True in np.isnan(ds.data):  # there's already nan values in data
            data_complete = ds.data.copy()
            time_complete = ds.time.values.copy()
            ds_new_1 = xr.DataArray(
                data=data_complete,
                dims=["time_2"],
                coords={"time_2": ("time_2", time_complete)},
            )
        else:
            time_complete = np.array(
                pd.date_range(ds.time[0].values, ds.time[-1].values, freq="10min")
            )
            data_complete = np.empty(len(time_complete))
            data_complete[:] = np.nan
            check = np.isin(time_complete, ds.time)
            indxs = np.where(check)[0]
            np.put(data_complete, indxs, ds.values)
            ds_new_1 = xr.DataArray(
                data=data_complete,
                dims=["time_2"],
                coords={"time_2": ("time_2", time_complete)},
            )
        ds_new = ds_new_1.rename(ds.name + "_2")

    return ds_new


def _mark_gaps(da, fig, row, col):
    """
    Marks the beggining and ending of regions without data with an hourglass
    symbol.
    """
    go = _import_optional_dependency("plotly.graph_objects")

    # Need for the indexes where there's change from having to not having data
    aux_array = da.data.copy()
    aux_array[~np.isnan(aux_array)] = 1  # non nan values to 1
    aux_array[np.isnan(aux_array)] = 0  # nan values to 0

    # Take indexes where changes happen
    change_indexes_1 = np.where(np.roll(aux_array, 1) != aux_array)[0]
    change_indexes_2 = np.where(np.roll(aux_array, -1) != aux_array)[0]
    change_indexes = np.sort(
        np.concatenate(
            [
                change_indexes_1,
                change_indexes_2[~np.isin(change_indexes_2, change_indexes_1)],
            ]
        )
    )[1:-1]
    # Adding a scatter plot with the marks
    fig.add_trace(
        go.Scatter(
            x=da.time_2.values[change_indexes],
            y=da.values[change_indexes],
            mode="markers",
            hoverinfo="skip",
            showlegend=False,
            marker=dict(symbol="hourglass", color="red"),
        ),
        row=row,
        col=col,
    )
    return fig


def time_series(ds, range_slider=True, time_range=None, mark_data_gaps=False):
    """Create time series plot

    The time series plot can be displayed for both a xarray.Dataset o
    xarray.DataAarray input argument. When the input is a Dataset, plots
    both the wind direction and wind speed time series. If the input is a
    DataAarray plot the its data variable. For both cases the gaps of data are
    identified in the time series.

    Parameters
    ----------
    ds : either a xarray.Dataset or a xarray.DataArray

        xarray.Dataset representing  the wind direction and wind speed time
        series.

        xarray.DataArray representing a data variable time series.

    range_slider :  bool, optional
         Include range slider?
         Default: with range slider

    time_range : list of two values [start, end] that can convert to numpy.datetime64
        The time series is directly shown in the defined interval.

        e.g: ``time_range=['2015-12-27', '2016-01-12']`` will display the
        timeseries for this time interval.

        NOTE: all data is still plotted, only the initial view to the data is changed.

        Default shows the full data range

    mark_data_gaps : bool, optional
        Mark beggining and ending of regions with data gaps in the time series?

        NOTE: Mark data gaps increases a bit the plotting time (1 to 3 sec).

        Default: without marks

    Returns
    -------
    plotly.graph_objects.Figure
        Plotly figure for display, additional modification, or output
    """
    px = _import_optional_dependency("plotly.express")
    _import_optional_dependency("plotly.subplots")
    plotly = _import_optional_dependency("plotly")
    make_subplots = plotly.subplots.make_subplots

    check_multipoint(ds)
    dss = ds.squeeze()
    dsss = _missing_data(dss)
    dff = dsss.to_dataframe().reset_index()

    if isinstance(ds, xr.Dataset):  # here we plot 2 subplots with wd and ws
        fig_subplots = make_subplots(
            shared_xaxes=True,
            rows=2,
            cols=1,
        )
        xaxes_title = check_plotting_attrs(dss["time"])
        yaxes_title_wd = check_plotting_attrs(dss["wind_direction"])
        yaxes_title_ws = check_plotting_attrs(dss["wind_speed"])

        fig_ws = px.line(
            dff,
            x="time_2",
            y="wind_speed_2",
            custom_data=["wind_direction_2", "wind_speed_2"],
        )

        fig_wd = px.line(
            dff,
            x="time_2",
            y="wind_direction_2",
            custom_data=["wind_direction_2", "wind_speed_2"],
        )

        hovertemplate = (
            yaxes_title_ws
            + ": %{customdata[1]:.2f}<br>"
            + yaxes_title_wd
            + ": %{customdata[0]:.2f}"
        )

        for traces in fig_ws["data"]:
            fig_subplots.add_trace(traces, row=1, col=1)
        for traces in fig_wd["data"]:
            fig_subplots.add_trace(traces, row=2, col=1)

        fig_subplots.update_yaxes(title_text=yaxes_title_ws, row=1, col=1)
        fig_subplots.update_yaxes(title_text=yaxes_title_wd, row=2, col=1)
        fig_subplots.update_xaxes(
            title_text=xaxes_title,
            rangeslider={"visible": range_slider, "thickness": 0.05},
            type="date",
            row=2,
            col=1,
        )
        fig_subplots.update_traces(
            hovertemplate=hovertemplate, connectgaps=False, row=1, col=1
        )
        fig_subplots.update_traces(
            hovertemplate=hovertemplate, connectgaps=False, row=2, col=1
        )
        fig = fig_subplots.update_layout(hovermode="x unified", xaxis_range=time_range)
        fig.update_traces(connectgaps=False)

        if mark_data_gaps:
            fig = _mark_gaps(dsss["wind_direction_2"], fig, row=2, col=1)
            fig = _mark_gaps(dsss["wind_speed_2"], fig, row=1, col=1)

    elif isinstance(ds, xr.DataArray):  # here we plot 1 plot with the dataArray
        xaxes_title = check_plotting_attrs(dss["time"])
        yaxes_title = check_plotting_attrs(dss)
        fig = px.line(dff, x="time_2", y=ds.name + "_2", custom_data=[ds.name + "_2"])
        hovertemplate = yaxes_title + ": %{customdata[0]:.2f}"
        fig.update_yaxes(title_text=yaxes_title)
        fig.update_xaxes(
            title_text=xaxes_title,
            rangeslider={"visible": range_slider, "thickness": 0.05},
            type="date",
        )
        fig.update_traces(hovertemplate=hovertemplate, connectgaps=False)

        fig.update_layout(hovermode="x unified", xaxis_range=time_range)

        if mark_data_gaps:
            fig = _mark_gaps(dsss, fig, row=None, col=None)

    return fig
