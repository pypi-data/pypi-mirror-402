# (c) 2022 DTU Wind Energy
"""
WindKit provides an API for working with wind resource assessment related file formats.
"""

__all__ = [
    "__version__",
    # Subpackage - spatial
    "spatial",
    # Subpackage - LTC
    "ltc",
    # Wind
    "wind_speed",
    "wind_direction",
    "wind_speed_and_direction",
    "wind_vectors",
    "wind_direction_difference",
    "wd_to_sector",
    "vinterp_wind_direction",
    "vinterp_wind_speed",
    "rotor_equivalent_wind_speed",
    "tswc_resample",
    "shear_extrapolate",
    "shear_exponent",
    "veer_extrapolate",
    "wind_veer",
    # Time Series Wind Climate
    "validate_tswc",
    "is_tswc",
    "create_tswc",
    "read_tswc",
    "tswc_from_dataframe",
    # Binned wind climate
    "validate_bwc",
    "is_bwc",
    "create_bwc",
    "read_bwc",
    "bwc_from_tswc",
    "bwc_to_file",
    "combine_bwcs",
    "weibull_fit",
    # Weibull wind climate
    "validate_wwc",
    "is_wwc",
    "create_wwc",
    "read_wwc",
    "read_mfwwc",
    "wwc_to_file",
    "wwc_to_bwc",
    "weibull_combined",
    # Generalized wind climate
    "validate_gwc",
    "is_gwc",
    "create_gwc",
    "read_gwc",
    "gwc_to_file",
    # Geostrophic wind climate
    "validate_geowc",
    "is_geowc",
    "create_geowc",
    # Predicted Wind Climate
    "create_pwc",
    # Wind Climate
    "create_met_fields",
    "mean_ws_moment",
    "ws_cdf",
    "ws_freq_gt_mean",
    "mean_wind_speed",
    "mean_power_density",
    "get_cross_predictions",
    "extrapolate_to_height",
    # Landcover
    "LandCoverTable",
    "get_landcover_table",
    # Raster map
    "create_raster_map",
    # Vector map
    "create_vector_map",
    "add_landcover_table",
    # Topography
    "create_wasp_site_effects",
    "read_elevation_map",
    "read_roughness_map",
    "read_landcover_map",
    "elevation_map_to_file",
    "roughness_map_to_file",
    "landcover_map_to_file",
    "roughness_to_landcover",
    "landcover_to_roughness",
    # cfd
    "read_cfdres",
    # wind_turbine_generator
    "validate_wtg",
    "is_wtg",
    "RegulationType",
    "estimate_regulation_type",
    "read_wtg",
    "wtg_power",
    "wtg_cp",
    "wtg_ct",
    # wind_turbines
    "validate_windturbines",
    "is_windturbines",
    "check_wtg_keys",
    "create_wind_turbines_from_dataframe",
    "create_wind_turbines_from_arrays",
    "wind_turbines_to_geodataframe",
    # workspace
    "Workspace",
    # weng_workspace
    "WengWorkspace",
    # module - weibull
    "weibull",
    # subpackage - plot
    "plot",
    # map_conversion
    "lines_to_polygons",
    "polygons_to_lines",
    "snap_to_layer",
    "check_dead_ends",
    "check_lines_cross"
    # get_map
    "get_raster_map",
    "get_vector_map",
    # wind_data
    "get_era5",
    # loss
    "validate_loss_table",
    "get_loss_table",
    "total_loss",
    "loss_table_summary",
    "total_loss_factor",
    # sector
    "create_sector_coords",
    # wsbin
    "create_wsbin_coords",
    # uncertainty
    "validate_uncertainty_table",
    "get_uncertainty_table",
    "total_uncertainty",
    "uncertainty_table_summary",
    "total_uncertainty_factor",
    # tutorial_data
    "get_tutorial_data",
]

from windkit._version import version as __version__
from windkit import spatial
from windkit import ltc
from windkit.wind import (
    wind_speed,
    wind_direction,
    wind_speed_and_direction,
    wind_vectors,
    wind_direction_difference,
    wd_to_sector,
    vinterp_wind_direction,
    vinterp_wind_speed,
    rotor_equivalent_wind_speed,
    tswc_resample,
    shear_extrapolate,
    shear_exponent,
    veer_extrapolate,
    wind_veer,
)
from windkit.wind_climate.time_series_wind_climate import (
    validate_tswc,
    is_tswc,
    create_tswc,
    read_tswc,
    tswc_from_dataframe,
)
from windkit.wind_climate import time_series_wind_climate  # noqa: F401
from windkit.wind_climate.binned_wind_climate import (
    validate_bwc,
    is_bwc,
    create_bwc,
    read_bwc,
    bwc_from_tswc,
    bwc_to_file,
    combine_bwcs,
    weibull_fit,
)
from windkit.wind_climate import binned_wind_climate  # noqa: F401
from windkit.wind_climate.weibull_wind_climate import (
    validate_wwc,
    is_wwc,
    create_wwc,
    read_wwc,
    read_mfwwc,
    wwc_to_file,
    wwc_to_bwc,
    weibull_combined,
)
from windkit.wind_climate import weibull_wind_climate  # noqa: F401
from windkit.wind_climate.generalized_wind_climate import (
    validate_gwc,
    is_gwc,
    create_gwc,
    read_gwc,
    gwc_to_file,
    _reproject_gwc,
)
from windkit.wind_climate import generalized_wind_climate  # noqa: F401
from windkit.wind_climate.geostrophic_wind_climate import (
    validate_geowc,
    is_geowc,
    create_geowc,
)
from windkit.wind_climate import geostrophic_wind_climate  # noqa: F401
from windkit.wind_climate.predicted_wind_climate import create_pwc
from windkit.wind_climate import predicted_wind_climate  # noqa: F401
from windkit.wind_climate.wind_climate import (
    create_met_fields,
    mean_ws_moment,
    ws_cdf,
    ws_freq_gt_mean,
    mean_wind_speed,
    mean_power_density,
    get_cross_predictions,
    extrapolate_to_height,
)
from windkit.cfd import read_cfdres
from windkit.wind_farm.wind_turbine_generator import (
    validate_wtg,
    is_wtg,
    RegulationType,
    estimate_regulation_type,
    read_wtg,
    wtg_power,
    wtg_cp,
    wtg_ct,
)
from windkit.wind_farm.wind_turbines import (
    validate_windturbines,
    is_windturbines,
    check_wtg_keys,
    create_wind_turbines_from_dataframe,
    create_wind_turbines_from_arrays,
    wind_turbines_to_geodataframe,
)
from windkit.workspace import Workspace
from windkit.weng_workspace import WengWorkspace
from windkit import weibull
from windkit import plot  # Order of imports matters

from windkit.topography.map_conversions import (
    lines_to_polygons,
    polygons_to_lines,
    snap_to_layer,
    check_dead_ends,
    check_lines_cross,
)
from windkit.topography.get_map import _get_ee_map, get_raster_map, get_vector_map
from windkit.topography.landcover import LandCoverTable, get_landcover_table
from windkit.topography.raster_map import (
    create_raster_map,
)
from windkit.topography.vector_map import create_vector_map, add_landcover_table
from windkit.topography.topography import (
    create_wasp_site_effects,
    read_elevation_map,
    read_roughness_map,
    read_landcover_map,
    elevation_map_to_file,
    roughness_map_to_file,
    landcover_map_to_file,
    roughness_to_landcover,
    landcover_to_roughness,
)

from windkit.wind_data import get_era5
from windkit.import_manager import _import_optional_dependency
from windkit.wind_farm.loss import (
    validate_loss_table,
    get_loss_table,
    total_loss,
    loss_table_summary,
    total_loss_factor,
)
from windkit.wind_farm.uncertainty import (
    validate_uncertainty_table,
    get_uncertainty_table,
    total_uncertainty,
    uncertainty_table_summary,
    total_uncertainty_factor,
)
from windkit.xarray_structures.metadata import (
    _ALL_VARS_META,
    _create_coords,
    _update_var_attrs,
    _update_history,
    _update_coord_attrs,
)
from windkit.xarray_structures.sector import (
    create_sector_coords,
)
from windkit.xarray_structures.direction import (
    _create_direction_coords,
)
from windkit.xarray_structures.wsbin import (
    create_wsbin_coords,
)
from windkit.tutorial_data import get_tutorial_data
