# (c) 2022 DTU Wind Energy
"""
Utility functions for Weibull distributions
"""

__all__ = [
    "fit_weibull_wasp_m1_m3_fgtm",
    "fit_weibull_wasp_m1_m3",
    "fit_weibull_k_sumlogm",
    "weibull_moment",
    "weibull_pdf",
    "weibull_cdf",
    "weibull_freq_gt_mean",
    "get_weibull_probability",
]

import math
import os

import numpy as np
import xarray as xr
from scipy.optimize import root_scalar
from scipy.special import gamma

# Lazy numba availability check - cached after first call
_numba_available = None


def _get_numba():
    """Lazily check if numba is available and enabled."""
    global _numba_available
    if _numba_available is not None:
        return _numba_available

    use_numba = True
    env_val = os.environ.get("WK_USE_NUMBA")
    if env_val is not None:
        use_numba = env_val.lower() in ["true", "1", "t"]

    if use_numba:
        try:
            import numba

            _numba_available = numba
        except ModuleNotFoundError:
            _numba_available = False
    else:
        _numba_available = False

    return _numba_available


def _fit_wasp_m1_m3_fgtm(m1, m3, freq_gt_mean, atol=1e-8):
    """WAsP Weibull fit algorithm which perserves:
       1. Third moment
       2. Fraction of probability mass above and below the mean

    Obtains the same weibull shape and scaler parameters as
    WAsP core (and WAsP GUI) for low-enough tolerances.

    Parameters
    ----------
    m1 : float
        First moment/mean

    m3 : float
        Third moment

    freq_gt_mean : float
        Skewness term: frequency-mass that falls above the mean value

    atol : float
        Absolute tolerance for root-finding algorithm

    Returns
    -------
    A : float
        Weibull scale parameter

    k : float
        Weibull shape parameter

    """

    if any(np.isnan([m1, m3, freq_gt_mean])):
        return np.nan, np.nan

    c2 = 3.0 * np.log(-np.log(freq_gt_mean))
    c1 = -(np.log(m3) - 3.0 * np.log(m1))

    def _func_fit_wasp_m1_m3_fgtm(k):
        return c1 + math.lgamma(1.0 + 3.0 / k) - c2 / k

    k = root_scalar(
        _func_fit_wasp_m1_m3_fgtm, method="brentq", bracket=[0.01, 50], xtol=atol
    ).root
    A = (m3 / math.gamma(1.0 + 3.0 / k)) ** (1.0 / 3.0)

    return A, k


def fit_weibull_wasp_m1_m3_fgtm(m1, m3, freq_gt_mean, atol=1e-8):
    """
    Fit weibull parameters from the first and third moments
    and the fraction of probability mass above the mean

    Parameters
    ----------
    m1 : xarray.DataArray
        First moment / mean

    m3 : xarray.DataArray
        Third moment / skewness

    freq_gt_mean : xarray.DataArray
        Skewness term: frequency-mass that falls above the mean value

    atol : float
        Absolute tolerance for root-finding algorithm

    Returns
    -------
    A : xarray.DataArray
        Weibull scale parameter

    k : xarray.DataArray
        Weibull shape parameter

    Notes
    -----
    This function has the optional dependency 'numba'. If numba is installed,
    the function will use a numba-compiled version of the algorithm which
    is much faster. If numba is not installed, the function will use a
    scipy-based root-finding algorithm and vectorization through np.vectorize which
    is much slower.

    """

    kwargs = dict(
        input_core_dims=[[], [], []],
        output_core_dims=[[], []],
        kwargs={"atol": atol},
        keep_attrs=True,
    )

    numba = _get_numba()
    if not numba:
        _fit_func = _fit_wasp_m1_m3_fgtm
        kwargs["vectorize"] = True
        kwargs["dask"] = "allowed"
    else:
        from ._weibull_nb import _fit_wasp_m1_m3_fgtm_nb as _fit_func

        kwargs["vectorize"] = False
        kwargs["dask"] = "parallelized"
        kwargs["output_dtypes"] = ["float64", "float64"]

    A, k = xr.apply_ufunc(
        _fit_func,
        m1,
        m3,
        freq_gt_mean,
        **kwargs,
    )
    return A, k


def _fit_wasp_m1_m3(m1, m3, atol=1e-8):
    """
    Fit weibull perserving the third moment

    Parameters
    ----------
    m1 : float
        First moment / mean

    m3: float
        Third moment / skewness

    atol : float
        Absolute tolerance for root finding algorithm

    Returns
    -------
    A : float
        Weibull scale parameter

    k : float
        Weibull shape parameter

    """
    if any(np.isnan([m1, m3])):
        return np.nan, np.nan

    c1 = np.log(m3) / 3.0 - np.log(m1)

    def _func_fit_wasp_m1_m3(k):
        return c1 - math.lgamma(1.0 + 3.0 / k) / 3.0 + math.lgamma(1.0 + 1.0 / k)

    k = root_scalar(
        _func_fit_wasp_m1_m3, method="brentq", bracket=[0.01, 50], xtol=atol
    ).root
    A = (m3 / math.gamma(1.0 + 3.0 / k)) ** (1.0 / 3.0)

    return A, k


def fit_weibull_wasp_m1_m3(m1, m3, atol=1e-8):
    """
    Fit weibull parameters from the first and third moments

    Parameters
    ----------
    m1 : xarray.DataArray
        First moment / mean

    m3 : xarray.DataArray
        Third moment / skewness

    atol : float
        Absolute tolerance for root finding algorithm

    Returns
    -------
    A : xarray.DataArray
        Weibull scale parameter

    k : xarray.DataArray
        Weibull shape parameter

    Notes
    -----
    This function has the optional dependency 'numba'. If numba is installed,
    the function will use a numba-compiled version of the algorithm which
    is much faster. If numba is not installed, the function will use a
    scipy-based root-finding algorithm and vectorization through np.vectorize which
    is much slower.

    """

    kwargs = dict(
        input_core_dims=[[], []],
        output_core_dims=[[], []],
        kwargs={"atol": atol},
        keep_attrs=True,
    )

    numba = _get_numba()
    if not numba:
        _fit_func = _fit_wasp_m1_m3
        kwargs["vectorize"] = True
        kwargs["dask"] = "allowed"
    else:
        from ._weibull_nb import _fit_wasp_m1_m3_nb as _fit_func

        kwargs["vectorize"] = False
        kwargs["dask"] = "parallelized"
        kwargs["output_dtypes"] = ["float64", "float64"]

    A, k = xr.apply_ufunc(
        _fit_func,
        m1,
        m3,
        **kwargs,
    )
    return A, k


def _fit_k_sumlogm(sumlogm, order_m_first=1, order_m_higher=3, atol=1e-8):
    """WAsP Weibull fit algorithm using methods
    of moments preserving sum of logs of the chosen moments

    Parameters
    ----------
    sumlogm : float
        Precalculated sum of log of moments. For example, sum of log of
        first and third moments:
        sumlogm = np.log(m3)/3 - np.log(m1)

    order_m_first : int
        First moment order

    order_m_higher : int
        The higher order moment

    atol : float
        Absolute tolerance for root finding algorithm

    Returns
    -------
    float
        Weibull scale parameter (k)

    """
    if np.isnan(sumlogm):
        return np.nan

    def _func_fit_sumlogm(k):
        return (
            sumlogm
            - math.lgamma(1.0 + order_m_higher / k) / order_m_higher
            + math.lgamma(1.0 + order_m_first / k) / order_m_first
        )

    weibull_k = root_scalar(
        _func_fit_sumlogm, method="brentq", bracket=[0.01, 50], xtol=atol
    ).root

    return weibull_k


def fit_weibull_k_sumlogm(sumlogm, order_m_first=1, order_m_higher=3, atol=1e-8):
    """Fit weibull shape parameter from the sum of log of moments

    Parameters
    ----------
    sumlogm : xr.DataArray
        xr.DataArray with sum of the log of moments

    order_m_first : int
        First moment that is conserved when solving k

    order_m_higher : int
        Higher moment that is conserved when solving k

    atol : float
        Absolute tolerance for root finding algorithm

    Returns
    -------
    xr.DataArray
        Weibull shape parameter (k)

    Notes
    -----
    This function has the optional dependency 'numba'. If numba is installed,
    the function will use a numba-compiled version of the algorithm which
    is much faster. If numba is not installed, the function will use a
    scipy-based root-finding algorithm and vectorization through np.vectorize which
    is much slower.


    """

    kwargs = dict(
        input_core_dims=[[]],
        output_core_dims=[[]],
        kwargs={
            "order_m_first": 1,
            "order_m_higher": 3,
            "atol": atol,
        },
        keep_attrs=True,
    )

    numba = _get_numba()
    if not numba:
        _fit_func = _fit_k_sumlogm
        kwargs["vectorize"] = True
        kwargs["dask"] = "allowed"
    else:
        from ._weibull_nb import _fit_k_sumlogm_nb as _fit_func

        kwargs["vectorize"] = False
        kwargs["dask"] = "parallelized"
        kwargs["output_dtypes"] = ["float64"]

    weibull_k = xr.apply_ufunc(
        _fit_func,
        sumlogm,
        **kwargs,
    )
    return weibull_k


def weibull_moment(A, k, n=1):
    """Calculate moment for a weibull distribution.

    Parameters
    ----------
    A : xarray.DataArray
        Weibull scale parameter.

    k : xarray.DataArray
        Weibull shape parameter.

    n : int
        Moment to consider, defautls to 1.

    Returns
    -------
    xarray.DataArray
        Moment of the weibull distribution.

    """

    return A**n * gamma(1.0 + n / k)


def weibull_pdf(A, k, x):
    """Calculate the probability density function for a weibull distribution.

    Parameters
    ----------
    A : xarray.DataArray
        Weibull scale parameter.

    k : xarray.DataArray
        Weibull shape parameter.

    x : xarray.DataArray
        Values to calculate the PDF for.

    Returns
    -------
    xarray.DataArray
        PDF values for the given x values.

    """
    return (k / A) * (x / A) ** (k - 1.0) * np.exp(-((x / A) ** k))


def weibull_cdf(A, k, x):
    """Calculate the cumulative distribution function for a weibull distribution.

    Parameters
    ----------
    A : xarray.DataArray
        Weibull scale parameter.

    k : xarray.DataArray
        Weibull shape parameter.

    x : xarray.DataArray
        Values to calculate the CDF for.

    Returns
    -------
    xarray.DataArray
        CDF values for the given x values.

    """
    return 1.0 - np.exp(-((x / A) ** k))


def weibull_freq_gt_mean(A, k):
    """Calculate the fraction of probability mass
    that lie above the mean wind speed
    for a weibull distribution

    Parameters
    ----------
    A : xarray.DataArray
        Weibull scale parameter.

    k : xarray.DataArray
        Weibull shape parameter.

    Returns
    -------
    xarray.DataArray
        Probability mass above the mean.
        Fraction between 0 and 1.

    """
    mean = weibull_moment(A, k, n=1)
    return 1 - weibull_cdf(A, k, mean)


def get_weibull_probability(
    A: float, k: float, speed_range: np.ndarray, single_speed=False
):
    """Calculate Weibull probability.

    Parameters
    ----------
    A : float
        Scale parameter of the Weibull distribution.

    k :  float
        Shape parameter of the Weibull distribution.

    speed_range :  numpy.ndarray
        List of floats representing the wind speed bins contained in the binned
        "histogram" wind climate.

    single_speed : bool, optional
        Should the weibull probability be calculed for a single wind speed,
        default False.

        - True : Calculate the probability for the single wind speed defined by a
            single float element in the speed_range list.

        - False : Calculate the probability for the hole wind speed range defined.

    Returns
    -------
    speeds : numpy.ndarray
        List of floats representing the wind speed bins.

    prob : numpy.ndarray
        List of floats representing the Weibull probability for each element of
        the speeds list.
    """
    if single_speed:
        speeds = speed_range
    else:
        speeds = np.linspace(speed_range[0], speed_range[1], 500)

    if A == 0:
        return "0"
    elif k > 1.0:
        prob = (
            (k / A) * np.power(speeds / A, k - 1.0) * np.exp(-np.power(speeds / A, k))
        )
    elif k == 1:
        prob = (k / A) * np.power(-np.power(speeds / A, k))
    else:
        prob = (
            (k / A) * np.power(A / speeds, 1.0 - k) * np.exp(-np.power(speeds / A, k))
        )
        prob = np.where(speeds == 0, np.zeros_like(speeds), prob)
    return speeds, prob
