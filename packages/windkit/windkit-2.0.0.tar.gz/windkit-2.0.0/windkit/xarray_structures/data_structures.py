# (c) 2022 DTU Wind Energy
"""WindKit data structres defines as Enum enumeration class"""

__all__ = []

from enum import Enum


class _DataStructures(Enum):
    HIS = "Wind Histogram"
    HIS_STAB = "Stability histogram"
    MEAN_STAB = "Mean stability histogram"
    ELEV_ROSE = "Elevation Rose"
    ROU_ROSE = "Roughness rose"
    BWC = "Binned Wind Climate"
    WWC = "Weibull Wind Climate"
    GWC = "Generalized Wind Climate"
    GEWC = "Generalized Extreme Wind Climate"
    GEOWC = "Geostrophic Wind Climate"
    LINCOM_V50 = "LINCOM V50 Wind"
    LINCOM_V50_LUT = "LINCOM Lookup Table"
    LINCOM_WIND_LEVEL = "LINCOM Wind Level"
    LINCOM_WIND_POINT = "LINCOM Wind Point"
    V50_GUMBEL = "V50 Gumbel"
    MAP_TYPE = "Rastermap"
    MET = "Met fields"
    SPECTRUM = "Spectrum/spectral Correction Factor"
    TOPO_EFFECTS = "Topographic effects"
    TOPO_CFD_EFFECTS = "Topographic CFD effects"
    WASP_SITE_COND = "WAsP site conditions"
    LINCOM_GEWC = "LINCOM GEWC"
    TS = "Time Series Wind Climate"
    WTG = "Wind Turbine Generator"
    AEP = "Anual Energy Production"
    WF_FLOW_MAP = "Wind Farm Flow Map"
