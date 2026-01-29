# (c) 2023 DTU Wind Energy
"""
Functions to calculate common scoring metrics to be used on windkit
time series wind climate datasets.
"""

import numpy as np
import pandas as pd

from ._validation import ltc_validate


# @ltc_validate
@ltc_validate(n_args=2)
def rmse(ds_target, ds_pred):
    """
    Calculates the root mean square error for the wind speed of two
    time series wind climate datasets. The implementation is inspired
    by sklearn.metrics.root_mean_squared_error source code.

    Parameters
    ----------
    ds_target : xarray.Dataset
        target time series wind climate dataset
    ds_pred : xarray.Dataset
        predicted time series wind climate dataset

    Returns
    -------
    rmse: float
        root mean square error of the two wind speeds

    """
    y_tgt = ds_target.wind_speed.values.flatten()
    y_pred = ds_pred.wind_speed.values.flatten()
    return np.sqrt(
        np.average(
            (y_tgt - y_pred) ** 2,
            axis=0,
        )
    )


# @ltc_validate
@ltc_validate(n_args=2)
def r2(ds_target, ds_pred):
    """
    Calculates the r2 regression score for the wind speed of two
    time series wind climate datasets. The implementation is inspired
    by sklearn.metrics.r2_score source code.

    Parameters
    ----------
    ds_target : xarray.Dataset
        target time series wind climate dataset
    ds_pred : xarray.Dataset
        predicted time series wind climate dataset

    Returns
    -------
    r2: float
        r2 score of the two wind speeds

    """
    y_tgt = ds_target.wind_speed.values.flatten()
    y_pred = ds_pred.wind_speed.values.flatten()
    numerator = ((y_tgt - y_pred) ** 2).sum(axis=0, dtype=np.float64)
    denominator = ((y_tgt - np.average(y_tgt, axis=0)) ** 2).sum(
        axis=0, dtype=np.float64
    )
    return 1 - numerator / denominator


# @ltc_validate
@ltc_validate(n_args=2)
def bias(ds_target, ds_pred):
    """
    Calculates the bias for the wind speed of two time series wind climate
    datasets.

    Parameters
    ----------
    ds_target : xarray.Dataset
        target time series wind climate dataset
    ds_pred : xarray.Dataset
        predicted time series wind climate dataset

    Returns
    -------
    bias: float
        bias of the two wind speeds

    """
    y_tgt = ds_target.wind_speed.values.flatten()
    y_pred = ds_pred.wind_speed.values.flatten()
    return y_tgt.mean() - y_pred.mean()


# @ltc_validate
@ltc_validate(n_args=2)
def wasserstein_distance(ds_target, ds_pred):
    """
    Calculates the wasserstein distance for the wind speed of
    two time series wind climate datasets.

    Parameters
    ----------
    ds_target : xarray.Dataset
        target time series wind climate dataset
    ds_pred : xarray.Dataset
        predicted time series wind climate dataset

    Returns
    -------
    wasserstein_distance: float
        wasserstein distance of the two wind speeds
    """
    bins = np.linspace(0.0, 20.0, 21)
    y_tgt = ds_target.wind_speed
    y_pred = ds_pred.wind_speed
    p, _ = np.histogram(y_tgt, bins=bins, density=True)
    q, _ = np.histogram(y_pred, bins=bins, density=True)
    P = np.cumsum(p)
    Q = np.cumsum(q)
    return np.sum(np.abs(P - Q))


# @ltc_validate
@ltc_validate(n_args=2)
def calc_scores(ds_target, ds_pred, name="name", period="full"):
    """
    Helper function that calculates r2, rmse, bias and wasserstein distance
    scores and generate a pandas dataframe with useful headers for reporting.

    Parameters
    ----------
    ds_target : xarray.Dataset
        target time series wind climate dataset
    ds_pred : xarray.Dataset
        predicted time series wind climate dataset
    name: str
        a desired name for the case will be reported. Defaults to 'name'
    period: str
        the period for the datasets to be included in the report.
        Defaults to 'full'.

    Returns
    -------
    df : pandas.DataFrame
        dataframe with colummns "Name, "Period", "Metric" and "Score"
        including the calculated scores.

    """
    labels = ["R^2", "RMSE", "Mean bias", "EMD"]
    scoring = [r2, rmse, bias, wasserstein_distance]
    vals = np.array([f(ds_target, ds_pred) for f in scoring])
    names = [name] * len(vals)
    periods = [period] * len(vals)
    df = pd.DataFrame(
        columns=["Name", "Period", "Metric", "Score"],
        data={"Name": names, "Period": periods, "Metric": labels, "Score": vals},
    )
    return df
