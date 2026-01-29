# (c) 2023 DTU Wind Energy
"""
Measure-Correlate-Predict MCP Module.
"""

import numpy as np

from ..wind import wd_to_sector
from ._validation import assert_timesteps_equal, assert_valid_values, ltc_validate
from .regression import LinearRegression, VarianceRatioLinearRegression


class MCPBase(object):
    """
    Sectorwise Regressor base-class used as a blueprint
    for sectorwise MCP methods based on regression models.

    Parameters
    ----------
    n_sectors : int
        Number of sectors to fit independant regression models to.
        Default is 12 sectors.

    quantiles : bool
        Whether to use a equal probability sectors or constant
        sector widths. Default is to use constant sector widths.

    """

    def _wd_to_sector(self, wd, sectors=12, quantiles=False):
        """
        function from loteco
        wd : numpy.ndarray
        """
        if isinstance(sectors, np.ndarray):
            if sectors[0] < 0.0:
                n_sectors = len(sectors) - 1
                sec, sector_coords, _ = wd_to_sector(
                    wd, sectors=n_sectors, quantiles=False
                )
                edg = np.union1d(sector_coords.sector_floor, sector_coords.sector_ceil)
                return sec, edg
            else:
                return np.digitize(wd, sectors) - 1, sectors
        elif isinstance(sectors, int):
            sec, sector_coords, _ = wd_to_sector(
                wd, sectors=sectors, quantiles=quantiles
            )
            edg = np.union1d(sector_coords.sector_floor, sector_coords.sector_ceil)
            return sec, edg

    def __init__(self, n_sectors=12, quantiles=False):
        self.n_sectors = n_sectors
        self.quantiles = quantiles
        self.sector_edges = None

    def wd_to_sector(self, wd, recalc_sectors=False):
        """
        Convert wind direction to sectors using the
        object n_sectors and constant_sector_width values

        Parameters
        ----------
        wd : array, float, shape (n_samples,)
            Wind directions.

        Returns
        -------
        sector : array, int, shape (n_samples, )
            Wind direction sector indicies.

        """

        if (not recalc_sectors) and (self.sector_edges is not None):
            sector, sector_edges = self._wd_to_sector(wd, sectors=self.sector_edges)
        else:
            sector, sector_edges = self._wd_to_sector(
                wd, sectors=self.n_sectors, quantiles=self.quantiles
            )

            self.sector_edges = sector_edges
        return sector


class MCPRegressor(MCPBase):
    """
    Sectorwise Regressor base-class used as a blueprint
    for sectorwise MCP methods based on regression models.

    Parameters
    ----------

    ws_cutoff : float

    model_kws : dict
        kwargs to input when the model is instanciated.

    Attributes
    ----------
    model: what model to use in each sector

    models : list, shape (n_sectors,)
        one instanciated model per sector
    """

    model = None

    def __init__(self, ws_cutoff=0.0, model_kws={}, **kwargs):
        super().__init__(**kwargs)

        self.ws_cutoff = ws_cutoff
        self.model_kws = model_kws

        self.models_ = [self.model(**model_kws) for i_sec in range(self.n_sectors)]

    @ltc_validate(n_args=2)
    def fit(self, ds_ref, ds_target, **kwargs):
        """
        Fit the reference data to the target data by looping
        through the sectors and fitting the model to the
        data for that sector.

        Parameters
        ----------
        ds_ref: xarray.Dataset
            Windkit time series wind climate dataset with wind speed
            and wind direction for the reference data.
        ds_target: xarray.Dataset
            Windkit time series wind climate dataset with wind speed
            and wind direction for the reference data.

        Returns
        -------
        self : returns an instance of self.

        """
        # check valid values
        assert_valid_values(ds_ref)
        assert_valid_values(ds_target)
        assert_timesteps_equal(ds_ref, ds_target)

        sector_ref = self.wd_to_sector(
            ds_ref.wind_direction.values.flatten(), recalc_sectors=True
        )

        for i_sec in range(self.n_sectors):
            x = ds_ref.wind_speed.values.flatten()
            y = ds_target.wind_speed.values.flatten()

            mask_sec = sector_ref == i_sec
            x = x[mask_sec]
            y = y[mask_sec]

            mask_na = np.isnan(x) | np.isnan(y)
            x = x[~mask_na]
            y = y[~mask_na]

            mask_ws = x < self.ws_cutoff
            x = x[~mask_ws]
            y = y[~mask_ws]

            X = x[:, np.newaxis]

            self.models_[i_sec].fit(X, y)

        return self

    @ltc_validate(n_args=1)
    def predict(self, ds_ref, **kwargs):
        """
        Predict the wind speed and direction from
        the reference data by looping
        through the sectors and predicting with the model
        for that sector.

        Parameters
        ----------
        ds_ref: xarray.Dataset
            Time series wind climate dataset
        Returns
        -------
        ds_pred : xarray.Dataset
            Predicted wind speeds and directions
        """

        assert_valid_values(ds_ref)
        ws_pred = np.empty_like(ds_ref.wind_speed.values.flatten(), dtype=np.float64)
        ds_pred = ds_ref.copy()

        sector_ref = self.wd_to_sector(
            ds_ref.wind_direction.values.flatten(), recalc_sectors=False
        )

        for i_sec in range(self.n_sectors):
            x = ds_ref.wind_speed.values.flatten()

            mask_sec = sector_ref == i_sec
            mask_na = np.isnan(x)
            mask = (mask_sec) & (~mask_na)

            X = x[mask, np.newaxis]

            ws_pred[mask] = self.models_[i_sec].predict(X)

        ds_pred["wind_speed"].values = ws_pred.reshape(ds_pred.wind_speed.shape)

        return ds_pred


class LinRegMCP(MCPRegressor):
    """
    Sectorwise MCP using Scipy's linear regression.

    Parameters
    ----------
    n_sectors : int
        Number of sectors to fit independant regression models to.
        Default is 12 sectors.

    quantiles : bool
        Whether to use a constant sector width or use quantiles.
        Default is True.

    ws_cutoff : float

    model_kws : dict
        kwargs to input when the model is instanciated.

    Attributes
    ----------
    model: what model to use in each sector

    models : list, shape (n_sectors,)
        one instanciated model per sector
    """

    model = LinearRegression

    def __init__(self, ws_cutoff=3.0, **kwargs):
        super().__init__(ws_cutoff=ws_cutoff, **kwargs)


class VarRatMCP(MCPRegressor):
    """
    Sectorwise MCP using variance ratio linear regression.

    Parameters
    ----------
    n_sectors : int
        Number of sectors to fit independant regression models to.
        Default is 12 sectors.

    quantiles : bool
        Whether to use a constant sector width or use quantiles.
        Default is True.

    ws_cutoff : float

    model_kws : dict
        kwargs to input when the model is instanciated.

    Attributes
    ----------
    model: what model to use in each sector

    models : list, shape (n_sectors,)
        one instanciated model per sector
    """

    model = VarianceRatioLinearRegression

    def __init__(self, fit_intercept=True, ws_cutoff=0.0, **kwargs):
        model_kws = {"fit_intercept": fit_intercept}
        super().__init__(model_kws=model_kws, ws_cutoff=ws_cutoff, **kwargs)
