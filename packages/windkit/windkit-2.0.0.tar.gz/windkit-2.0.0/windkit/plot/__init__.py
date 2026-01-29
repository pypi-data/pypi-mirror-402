# (c) 2022 DTU Wind Energy
"""
Plotting functionality for WindKit objects

Plots are largely broken into two categories statistical and maps. Statistical plots
are generally plotted at a single location, e.g. mast or turbine location, while
maps show an overview of the area.
"""

from ._colormaps import COLORMAP_LANDCOVER
from .elevation_map import elevation_map
from .histogram import histogram as histogram
from .histogram import histogram_lines as histogram_lines
from .landcover_map import landcover_map
from .operational_curves import power_ct_curves as power_ct_curves
from .operational_curves import single_curve as single_curve
from .raster_plot import raster_plot as raster_plot
from .roughness_rose import roughness_rose as roughness_rose

from .time_series import time_series as time_series
from .vertical_profile import vertical_profile as vertical_profile
from .wind_rose import wind_rose as wind_rose
from .wind_turbine import plot_wind_turbine_locations
