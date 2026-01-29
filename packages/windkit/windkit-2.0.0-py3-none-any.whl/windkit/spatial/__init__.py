# (c) 2022 DTU Wind Energy
"""
A collection of functions for working with geospatial object supported by WindKit.

Supported objects include:

1. Vector Maps in the form of geopandas objects: GeoDataFrame's and GeoSeries's
2. Array-like data in the form of xarray objects: DataArray's and xarray.Dataset's.
   Four structures of array-like objects are supported:

   1. **point** (..., *point*) with x, y, and z-coordinates each of length *point*
   2. **stacked_point** (..., *stacked_point*) with x, y-coordiantes each of length *stacked_point*
   3. **cuboid** (..., *height*, *south_north*, *west_east*) this requires regular spacing in the *south_north* and *west_east* dimensions
   4. **raster** (..., *south_north*, *west_east*) this is an internal structure that behaves like a 2D **cuboid**
"""

__all__ = [
    # _bbox.py
    "BBox",
    # _crs.py
    "get_crs",
    "add_crs",
    "set_crs",
    "crs_are_equal",
    # _cuboid.py
    "to_cuboid",
    # _interpolation.py
    "interp_structured_like",
    "interp_unstructured",
    "interp_unstructured_like",
    # _point.py
    "to_point",
    "to_stacked_point",
    # _raster.py
    "to_raster",
    # _struct.py
    "is_point",
    "is_stacked_point",
    "is_cuboid",
    "is_raster",
    # spatial.py
    "are_spatially_equal",
    "clip",
    "clip_with_margin",
    "covers",
    "count_spatial_points",
    "equal_spatial_shape",
    "mask",
    "nearest_points",
    "reproject",
    "warp",
    "gdf_to_ds",
    "ds_to_gdf",
    "add_projected_wrf_coordinates",
    "create_dataset",
    "create_point",
    "create_stacked_point",
    "create_raster",
    "create_cuboid",
]


# import each module to the namespace for easier access
from . import _bbox
from . import _crs
from . import _cuboid
from . import _dimensions
from . import _interpolation
from . import _latitude
from . import _point
from . import _raster
from . import _struct
from . import _utm
from . import _vector
from . import _vertical
from . import decorators

from ._crs import add_crs, get_crs, set_crs, crs_are_equal
from ._bbox import BBox
from ._cuboid import _create_isotropic_cuboid, to_cuboid
from ._interpolation import (
    interp_structured_like,
    interp_unstructured,
    interp_unstructured_like,
)
from ._latitude import _get_latitude

# nopycln: file
from ._point import to_point, to_stacked_point
from ._raster import to_raster
from ._struct import (
    get_spatial_struct,
    is_cuboid,
    is_point,
    is_raster,
    is_stacked_point,
    _is_vertical,
)
from .decorators import _stack_then_unstack
from .spatial import (
    add_projected_wrf_coordinates,
    equal_spatial_shape,
    are_spatially_equal,
    clip,
    clip_with_margin,
    covers,
    create_dataset,
    create_point,
    create_raster,
    create_stacked_point,
    create_cuboid,
    count_spatial_points,
    ds_to_gdf,
    gdf_to_ds,
    mask,
    nearest_points,
    reproject,
    _spatial_stack,
    _spatial_unstack,
    warp,
)
