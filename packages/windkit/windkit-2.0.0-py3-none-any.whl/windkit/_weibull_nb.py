import math
from functools import wraps

import numpy as np

try:
    import numba
    from numba import guvectorize, jit
except ModuleNotFoundError:
    numba = None

    # Set jit and guvectorize to identity decorator (do nothing to function)
    # This is to ensure that the decorators are still callable even if numba is not installed
    def jit(*args, **kwargs):
        def wrapper_jit(func):
            @wraps(func)
            def wrapped_jit(*args_f, **kwargs_f):
                return func(*args_f, **kwargs_f)

            return wrapped_jit

        return wrapper_jit

    def guvectorize(*args, **kwargs):
        def wrapper_guvectorize(func):
            @wraps(func)
            def wrapped_guvectorize(*args_f, **kwargs_f):
                return func(*args_f, **kwargs_f)

            return wrapped_guvectorize

        return wrapper_guvectorize


@jit(nopython=True)
def _func_fit_wasp_m1_m3_fgtm_nb(ca, cb, x):
    """fit03 function to find roots for in fit03

    Parameters
    ----------
    ca : float
        Constant a, calculated from the first and third moment (m1 and m3) as:
        -(np.log(m3) - 3.0 * np.log(m1))

    cb : float
        Constant b, calculated from fraction of density greater than the mean as:
        np.log(-np.log(freq_gt_mean))

    x : float
        3 / k, the fitting parameter

    Returns
    -------
    float
        The value of the fit03 function at x

    """
    return ca + math.lgamma(1.0 + x) - cb * x


@guvectorize(
    "(float64[:], float64[:], float64[:], float64, float64[:], float64[:])",
    "(n), (n), (n), () -> (n), (n)",
)
def _fit_wasp_m1_m3_fgtm_gu(m1, m3, freq_gt_mean, atol, A, k):
    """Numba generalized universal function (gufunc) implementation of the fit03 function from WAsP

    A gufunc is a function that operates on ndarrays in an element-by-element fashion,
    supporting array broadcasting, type casting, and several other standard features.
    This means that we can pass in arrays of values and get back arrays of values.

    Parameters
    ----------
    m1 : np.ndarray
        Array of mean wind speed (first moment) values

    m3 : np.ndarray
        Array of third moment wind speed values

    freq_gt_mean : np.ndarray
        Array of frequency of wind speeds greater than the mean wind speed

    atol : float
        Absolute tolerance for the fit03 fitting function

    Returns
    -------
    A : np.ndarray
        Array of Weibull A values (scale)

    k : np.ndarray
        Array of Weibull k values (shape)


    """

    # Factor used to reduce/increase cl, ch, and cc in the effort to
    # approximate value
    fact = 2.0
    one_third = 1.0 / 3.0
    cmax = 30

    for i in range(m1.shape[0]):
        if np.isnan(m1[i]) or np.isnan(m3[i]) or np.isnan(freq_gt_mean[i]):
            A[i] = np.nan
            k[i] = np.nan
            continue

        cb = np.log(-np.log(freq_gt_mean[i]))
        ca = -(np.log(m3[i]) - 3.0 * np.log(m1[i]))

        # initial values of constants cl, ch, cc
        cl = 3.0 / 2.0
        ch = 3.0 / 2.0
        cc = 3.0 / 2.0

        # The goal of step one is to get two constants (c1, c2) that correspond to
        # values on both 'sides' of 0 (i.e. one negative and one positive).
        c = _func_fit_wasp_m1_m3_fgtm_nb(ca, cb, ch)

        # ABS
        abs_c = np.abs(c)

        # SI, SL, and SH are used to store the sign of value at a given time.
        si = np.sign(c)
        sl = np.sign(c)
        sh = np.sign(c)

        # The while loop below keeps iterating the constants CL, CH, CC
        # Until two of the constants represent value's that are negative and
        # positive respectively. Then those constants are used in the next
        # procedure.
        while (si == sl) & (sh == si):
            ci = cl
            cl = ci / fact

            c = _func_fit_wasp_m1_m3_fgtm_nb(ca, cb, cl)

            if np.abs(c) < abs_c:
                abs_c = np.abs(c)
                cc = cl

            sl = np.sign(c)

            if sl != si:
                c1 = ci
                c2 = cl
                break

            ci = ch
            ch = ch * fact

            if ch > cmax:
                ci = cc
                k[i] = 3.0 / ci
                A[i] = (m3[i] / math.gamma(1.0 + ci)) ** one_third
                break

            c = _func_fit_wasp_m1_m3_fgtm_nb(ca, cb, ch)

            if np.abs(c) < abs_c:
                abs_c = np.abs(c)
                cc = ch

            sh = np.sign(c)

            if sh != si:
                c1 = ci
                c2 = ch

        # The procedure below lets the constants C1 and C2 approach each other
        # until the difference between them is small enough. Then the constant
        # that is found is used to derive k and A.
        diff = np.abs(c2 - c1)
        while diff > atol:
            ci = 0.5 * (c1 + c2)
            c = _func_fit_wasp_m1_m3_fgtm_nb(ca, cb, ci)

            if np.sign(c) != si:
                c2 = ci
            else:
                c1 = ci

            diff = np.abs(c2 - c1)

        k[i] = 3.0 / ci
        A[i] = (m3[i] / math.gamma(1.0 + ci)) ** one_third


def _fit_wasp_m1_m3_fgtm_nb(m1, m3, freq_gt_mean, atol=1e-8):
    """Numba generalized universal function (gufunc) implementation of the fit03 function from WAsP

    A gufunc is a function that operates on ndarrays in an element-by-element fashion,
    supporting array broadcasting, type casting, and several other standard features.
    This means that we can pass in arrays of values and get back arrays of values.

    Numba is required for this function to work.

    Parameters
    ----------
    m1 : np.ndarray
        Array of mean wind speed (first moment) values

    m3 : np.ndarray
        Array of third moment wind speed values. Skewneess term.

    freq_gt_mean : np.ndarray
        Array of frequency of wind speeds greater than the mean wind speed

    atol : float
        Absolute tolerance for the fit03 fitting function

    Returns
    -------
    A : np.ndarray
        Array of Weibull A values (scale)

    k : np.ndarray
        Array of Weibull k values (shape)

    Raises
    ------
    ImportError
        If numba is not installed

    """
    if numba is None:
        raise ImportError("Numba is required for this function to work.")

    if any(np.isscalar(arg) for arg in (m1, m3, freq_gt_mean)):
        m1, m3, freq_gt_mean = np.atleast_1d(m1, m3, freq_gt_mean)
        A, k = _fit_wasp_m1_m3_fgtm_gu(m1, m3, freq_gt_mean, atol)
        return A[0], k[0]
    else:
        return _fit_wasp_m1_m3_fgtm_gu(m1, m3, freq_gt_mean, atol)


@jit(nopython=True)
def _func_fit_sumlogm_nb(x, c, powl, powu):
    """fit_sumlogm function to find roots for

    Parameters
    ----------
    x : float
        The value of the function at x

    c : float
        The fitting parameter

    powl : float
        The lower power

    powu : float
        The upper power

    Returns
    -------
    float
        The value of the fit_sumlogm function at x

    """
    return x - math.lgamma(1.0 + powu / c) / powu + math.lgamma(1.0 + powl / c) / powl


@guvectorize(
    "(float64[:], int16, int16, float64, float64[:])",
    "(n), (), (), () -> (n)",
)
def _fit_k_sumlogm_gu(sumlogm, order_m_first, order_m_higher, atol, k):
    """Numba generalized universal function (gufunc) implementation of the sumlogm weibull
    fitting function from WAsP

    A gufunc is a function that operates on ndarrays in an element-by-element fashion,
    supporting array broadcasting, type casting, and several other standard features.
    This means that we can pass in arrays of values and get back arrays of values.

    Parameters
    ----------
    sumlogm : np.ndarray
        Array of sumlogm values. sumlogm is the sum of log of moments. For example, sum of log of
        first and third moments:
        sumlogm = np.log(m3)/3 - np.log(m1)

    order_m_first : int
        First moment order, must match the first moment order used to calculate sumlogm

    order_m_higher : int
        The higher order moment, must match the higher order moment used to calculate sumlogm

    atol : float
        Absolute tolerance for the fitting function

    Returns
    -------
    k : np.ndarray
        Array of Weibull k values (shape)

    """

    # Factor used to reduce/increase CL, CH, and CC in the effort to
    # approximate value
    fact = 2.0

    for i in range(sumlogm.shape[0]):
        if np.isnan(sumlogm[i]):
            k[i] = np.nan
            continue

        # initial values of constants cl, ch, cc
        cl = 2.0
        ch = 2.0

        # The goal of step one is to get two constants (C1, C2) that correspond to
        # values on both 'sides' of 0 (i.e. one negative and one positive).
        c = _func_fit_sumlogm_nb(sumlogm[i], cl, order_m_first, order_m_higher)

        # ABS
        abs_c = np.abs(c)

        # SI, SL, and SH are used to store the sign of value at a given time.
        si = np.sign(c)
        sl = np.sign(c)
        sh = np.sign(c)

        # The while loop below keeps iterating the constants CL, CH, CC
        # Until two of the constants represent value's that are negative and
        # positive respectively. Then those constants are used in the next
        # procedure.
        while (si == sl) & (sh == si):
            ci = cl
            cl = ci / fact
            c = _func_fit_sumlogm_nb(sumlogm[i], cl, order_m_first, order_m_higher)

            if np.abs(c) < abs_c:
                abs_c = np.abs(c)

            sl = np.sign(c)

            if sl != si:
                c1 = ci
                c2 = cl
                break

            ci = ch
            ch = ch * fact
            c = _func_fit_sumlogm_nb(sumlogm[i], ch, order_m_first, order_m_higher)

            if np.abs(c) < abs_c:
                abs_c = np.abs(c)

            sh = np.sign(c)

            if sh != si:
                c1 = ci
                c2 = ch

        # The procedure below lets the constants C1 and C2 approach each other
        # until the difference between them is small enough. Then the constant
        # that is found is used to derive k and A.
        diff = np.abs(c2 - c1)
        while diff > atol:
            ci = 0.5 * (c1 + c2)
            c = _func_fit_sumlogm_nb(sumlogm[i], ci, order_m_first, order_m_higher)

            if np.sign(c) != si:
                c2 = ci
            else:
                c1 = ci

            diff = np.abs(c2 - c1)

        k[i] = ci


def _fit_k_sumlogm_nb(sumlogm, order_m_first, order_m_higher, atol=1e-8):
    """Numba generalized universal function (gufunc) implementation of the sumlogm weibull
    fitting function from WAsP

    A gufunc is a function that operates on ndarrays in an element-by-element fashion,
    supporting array broadcasting, type casting, and several other standard features.
    This means that we can pass in arrays of values and get back arrays of values.

    Numba is required for this function to work.

    Parameters
    ----------
    sumlogm : np.ndarray
        Array of sumlogm values. sumlogm is the sum of log of moments. For example, sum of log of
        first and third moments:
        sumlogm = np.log(m3)/3 - np.log(m1)

    order_m_first : int
        First moment order, must match the first moment order used to calculate sumlogm

    order_m_higher : int
        The higher order moment, must match the higher order moment used to calculate sumlogm

    atol : float
        Absolute tolerance for the fitting function

    Returns
    -------
    k : np.ndarray
        Array of Weibull k values (shape)

    Raises
    ------
    ImportError
        If numba is not installed

    """
    if numba is None:
        raise ImportError("Numba is required for this function to work.")

    if np.isscalar(sumlogm):
        sumlogm = np.atleast_1d(sumlogm)
        k = _fit_k_sumlogm_gu(sumlogm, order_m_first, order_m_higher, atol)
        return k[0]
    else:
        return _fit_k_sumlogm_gu(sumlogm, order_m_first, order_m_higher, atol)


@guvectorize(
    "(float64[:], float64[:])",
    "(n) -> (n)",
)
def _gamma_gu(x, out):
    """Numba generalized universal function (gufunc) implementation of the gamma function"""
    for i in range(x.shape[0]):
        out[i] = math.gamma(x[i])


def _fit_wasp_m1_m3_nb(m1, m3, atol=1e-8):
    """Numba generalized universal function (gufunc) implementation of the fit02 function from WAsP
    which fits a webibull distribution from the first and third moments.

    A gufunc is a function that operates on ndarrays in an element-by-element fashion,
    supporting array broadcasting, type casting, and several other standard features.
    This means that we can pass in arrays of values and get back arrays of values.

    Numba is required for this function to work.

    Parameters
    ----------
    m1 : np.ndarray
        Array of mean wind speed (first moment) values

    m3 : np.ndarray
        Array of third moment wind speed values. Skewness term.

    atol : float
        Absolute tolerance for the fit03 fitting function

    Returns
    -------
    A : np.ndarray
        Array of Weibull A values (scale)

    k : np.ndarray
        Array of Weibull k values (shape)

    Raises
    ------
    ImportError
        If numba is not installed

    """
    if numba is None:
        raise ImportError("Numba is required for this function to work.")

    if any(np.isscalar(arg) for arg in (m1, m3)):
        is_scalar = True
        m1, m3 = np.atleast_1d(m1, m3)
    else:
        is_scalar = False

    sumlogm = np.log(m3) / 3.0 - np.log(m1)
    k = _fit_k_sumlogm_nb(sumlogm, 1, 3, atol=atol)
    A = (m3 / _gamma_gu(1.0 + 3.0 / k)) ** (1.0 / 3.0)

    if is_scalar:
        return A[0], k[0]
    else:
        return A, k
