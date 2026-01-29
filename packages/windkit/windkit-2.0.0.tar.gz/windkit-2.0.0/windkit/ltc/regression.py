# (c) 2023 DTU Wind Energy
"""
Implements different regression methods to be used for the long term correction.
"""

import numpy as np
import scipy


class LinearRegression:
    """
    Wrapper class to use scipy.stats.linregress
    """

    def __init__(self):
        self.slope = None
        self.intercept = None

    def fit(self, x, y):
        """
        Fit model.
        Note that the input of this function is not validated, the validation
        is made in the MPCRegressor class.
        Parameters
        ----------
        X : array-like, shape (n_samples, 1)
            Training data
        y : array_like, shape (n_samples)
            Target values. Will be cast to X's dtype if necessary

        Returns
        -------
        self : returns an instance of self.
        """

        self.slope, self.intercept, _, _, _ = scipy.stats.linregress(
            x.flatten(), y.flatten()
        )

    def predict(self, X):
        """
        Predict using the model.
        Note that the input of this function is not validated, the validation
        is made in the MPCRegressor class.

        Parameters
        ----------
        X : array_like, shape (n_samples, 1)
            Samples.

        Returns
        -------
        C : array, shape (n_samples,)
            Returns predicted values.

        """
        return self.slope * X.flatten() + self.intercept


class VarianceRatioLinearRegression(object):
    """
    Variance Ratio Linear Regression class
    striving towards the sklearn fit/predict standard

    For now, only supports one independent variable.
    #TODO: multilinear variance ratio linear regression.

    Parameters
    ----------
    fit_intercept: bool
        Whether to force the linear regression line through x,y=(0,0)
        default is True

    Attributes
    ----------
    intercept_ : float
        Independent term in the linear regression.

    coef_ : array, float, shape (1, )
        Estimated coefficient(s) for the linear regression problem.

    """

    def __init__(self, fit_intercept=True):
        self.fit_intercept = fit_intercept
        self.intercept_ = 0
        self.coef_ = np.array(
            [
                1.0,
            ]
        )

    def fit(self, X, y):
        """
        Fit model.
        Note that the input of this function is not validated, the validation
        is made in the MPCRegressor class.
        Parameters
        ----------
        X : array-like, shape (n_samples, 1)
            Training data
        y : array_like, shape (n_samples)
            Target values. Will be cast to X's dtype if necessary

        Returns
        -------
        self : returns an instance of self.
        """

        x_mean = np.mean(X)
        y_mean = np.mean(y)

        x_std = np.std(X)
        y_std = np.std(y)

        self.coef_ = np.array([y_std / x_std])

        if self.fit_intercept:
            self.intercept_ = y_mean - ((y_std / x_std) * x_mean)
        else:
            self.intercept_ = 0.0

        return self

    def predict(self, X):
        """
        Predict using the model.
        Note that the input of this function is not validated, the validation
        is made in the MPCRegressor class.

        Parameters
        ----------
        X : array_like, shape (n_samples, 1)
            Samples.

        Returns
        -------
        C : array, shape (n_samples,)
            Returns predicted values.

        """

        return np.sum(X * self.coef_, axis=1) + self.intercept_
