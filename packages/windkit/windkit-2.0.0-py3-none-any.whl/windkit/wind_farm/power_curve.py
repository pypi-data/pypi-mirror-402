"""
Module for working with a single wind turbine power curve as two simple
one-dimensional numpy-like arrays of the same length: wind speeds and power outputs.
"""

__all__ = []

import numpy as np


def _pad_power_curve_edges(wind_speeds, power_outputs, delta=1e-5, skip_if_zero=True):
    """
    Pad the edges of a wind turbine power curve with additional points to ensure
    that the power output is zero below the minimum wind speed and above the
    maximum wind speed.

    This is useful for interpolation and extrapolation of power curves, where we
    want to ensure that the power output is zero outside the defined range of
    wind speeds.

    Parameters
    ----------
    wind_speeds : array-like
        1D array of wind speeds (m/s).
    power_outputs : array-like
        1D array of power outputs (W) corresponding to the wind speeds.
    delta : float, optional
        Small value to extend the wind speed range at both ends. Default is 1e-5.
    skip_if_zero : bool, optional
        If True, skip padding on edges where power output is already zero.
        Default is True.

    Returns
    -------
    padded_wind_speeds : ndarray
        1D array of wind speeds with padded edges.
    padded_power_outputs : ndarray
        1D array of power outputs with padded edges.
    """
    wind_speeds = np.asarray(wind_speeds)
    power_outputs = np.asarray(power_outputs)

    # Determine whether to pad each edge
    pad_left = not (skip_if_zero and power_outputs[0] == 0)
    pad_right = not (skip_if_zero and power_outputs[-1] == 0)

    if not pad_left and not pad_right:
        return wind_speeds, power_outputs

    # Build padded wind speeds array
    parts = []
    if pad_left:
        parts.append([wind_speeds[0] - delta])
    parts.append(wind_speeds)
    if pad_right:
        parts.append([wind_speeds[-1] + delta])

    padded_wind_speeds = np.concatenate(parts)
    padded_power_outputs = np.pad(
        power_outputs,
        pad_width=(int(pad_left), int(pad_right)),
        mode="constant",
        constant_values=0,
    )

    return padded_wind_speeds, padded_power_outputs


def _unify_wind_speeds(*args):
    """
    Compute the union of multiple wind speed arrays.

    Parameters
    ----------
    *args : array-like
        Multiple 1D arrays of wind speeds (m/s).

    Returns
    -------
    unified_wind_speeds : ndarray
        1D array of unique wind speeds sorted in ascending order.
    """
    all_wind_speeds = np.concatenate([np.asarray(ws) for ws in args])
    return np.unique(all_wind_speeds)


def _unify_power_curves(wind_speeds_list, power_outputs_list):
    """
    Unify multiple wind turbine power curves to a common set of wind speeds.

    Each power curve is padded to ensure zero power output outside its defined
    range, then all curves are interpolated to a unified set of wind speeds.

    Parameters
    ----------
    wind_speeds_list : list of array-like
        List of 1D arrays of wind speeds (m/s) for each power curve.
    power_outputs_list : list of array-like
        List of 1D arrays of power outputs (W) corresponding to the wind speeds
        for each power curve.

    Returns
    -------
    unified_wind_speeds : ndarray
        1D array of unified wind speeds.
    unified_power_outputs_list : list of ndarray
        List of 1D arrays of power outputs interpolated to the unified wind
        speeds.
    """
    # Pad each power curve to ensure zero output outside its range
    padded_curves = [
        _pad_power_curve_edges(ws, po)
        for ws, po in zip(wind_speeds_list, power_outputs_list)
    ]
    padded_wind_speeds, padded_power_outputs = zip(*padded_curves)

    # Compute unified wind speeds and interpolate all curves
    unified_wind_speeds = _unify_wind_speeds(*padded_wind_speeds)
    unified_power_outputs_list = [
        np.interp(unified_wind_speeds, ws, po, left=0, right=0)
        for ws, po in zip(padded_wind_speeds, padded_power_outputs)
    ]

    return unified_wind_speeds, unified_power_outputs_list
