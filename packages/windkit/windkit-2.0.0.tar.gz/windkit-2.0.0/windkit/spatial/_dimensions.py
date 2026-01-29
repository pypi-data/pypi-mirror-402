# (c) 2022 DTU Wind Energy
"""
windkit.spatial module for code and metadata for working
with the supported WindKit xarray objects dimensions.

Supported spatial structures are:

point (public)
    dimensions: (..., 'point')
    coords:
        height: ('point',)
        south_north: ('point',)
        west_east: ('point',)

cuboid (public)
    dimensions: (..., 'height', 'south_north', 'west_east')
    coords:
        height: ('height',)
        south_north: ('south_north',)
        west_east: ('west_east',)

raster (partly public)
    dimensions: (..., south_north', 'west_east')
    coords:
        south_north: ('south_north',)
        west_east: ('west_east',)

vertical (partly public)
    dimensions: (..., 'height')
    coords:
        height: ('height',)

stacked_point (private)
    dimensions: (..., 'height', 'stacked_point')
    coords:
        south_north: ('stacked_point',)
        west_east: ('stacked_point',)
        height: ('height',)

"""

_WINDKIT_X_DIM = "west_east"
_WINDKIT_Y_DIM = "south_north"
_WINDKIT_Z_DIM = "height"
_WINDKIT_STACKED_POINT_DIM = "stacked_point"
_WINDKIT_POINT_DIM = "point"


def _xy_dims():
    return _WINDKIT_X_DIM, _WINDKIT_Y_DIM


def _vertical_dim():
    return _WINDKIT_Z_DIM


def _point_dim():
    return _WINDKIT_POINT_DIM


def _stacked_point_dim():
    return _WINDKIT_STACKED_POINT_DIM


def _cuboid_dims():
    return _WINDKIT_X_DIM, _WINDKIT_Y_DIM, _WINDKIT_Z_DIM
