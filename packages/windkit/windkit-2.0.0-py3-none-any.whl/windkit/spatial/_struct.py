# (c) 2022 DTU Wind Energy
"""
windkit.spatial functions for working with
the supported spatial structures of xarray objects.

The module includes functions for validating if objects are of a certain
spatial structure and getting the spatial structure
of an object.
"""

__all__ = [
    "is_point",
    "is_raster",
    "is_stacked_point",
    "is_cuboid",
    "get_spatial_struct",
]

from .._errors import WindkitError
from ._dimensions import (
    _cuboid_dims,
    _point_dim,
    _stacked_point_dim,
    _vertical_dim,
    _xy_dims,
)


def is_point(obj):
    """
    Check if WindKit xarray object has
    'point' spatial dimension. Meaning one dimension with
    'west_east', 'south_north', and 'height'
    coordinate variables along it.

    Parameters
    ----------
    obj : xarray.DataSet, xarray.DataArray
        object to check for 'point' dimension.

    Returns
    -------
    bool:
        True if 'point' dimension exists. False otherwise.

    """
    try:
        point_dim = _point_dim()
        return point_dim in obj.dims
    except Exception:
        return False


def is_raster(obj):
    """
    Check if WindKit xarray object has raster-like dimensions.

    Parameters
    ----------
    obj : xarray.DataSet, xarray.DataArray
        object to check for spatial dimensions.

    Returns
    -------
    bool:
        True if spatial dimensions exists. False otherwise.

    """
    try:
        raster_dims = _xy_dims()
        return all(dim in obj.dims for dim in raster_dims)
    except Exception:
        return False


def _is_vertical(obj):
    """
    Check if WindKit xarray object has vertical dimension.

    Parameters
    ----------
    obj : xarray.DataSet, xarray.DataArray
        object to check if vertical dimension are present.

    Returns
    -------
    bool:
        True if spatial dimensions exists. False otherwise.

    """
    try:
        vertical_dim = _vertical_dim()
        return vertical_dim in obj.dims
    except Exception:
        return False


def is_stacked_point(obj):
    """
    Check if WindKit xarray object has 'stacked_point' dimension.

    Parameters
    ----------
    obj : xarray.DataSet, xarray.DataArray
        object to check for 'stacked_point' dimension.

    Returns
    -------
    bool:
        True if spatial dimensions exists. False otherwise.

    """
    try:
        stacked_point_dim = _stacked_point_dim()
        return stacked_point_dim in obj.dims
    except Exception:
        return False


def is_cuboid(obj):
    """
    Check if WindKit xarray object has
    cuboid dimensions. Meaning dimensions in the
    west_east, south_north, and height-directions.

    Parameters
    ----------
    obj : xarray.DataSet, xarray.DataArray
        object to check for cuboid dimensions.

    Returns
    -------
    bool:
        True if cuboid dimensions exists. False otherwise.

    """

    try:
        cuboid_dims = _cuboid_dims()
        return all(dim in obj.dims for dim in cuboid_dims)
    except Exception:
        return False


def get_spatial_struct(obj):
    """Get the spatial structure of a WindKit xarray object.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object to determine the spatial structure from.

    Returns
    -------
    string :
        Spatial structure name. Can be on of:
            - 'point'
            - 'stacked_point'
            - 'raster'
            - 'cuboid'
        If no spatial structure is found None is returned.
    """
    if is_point(obj):
        return "point"
    elif is_stacked_point(obj):
        return "stacked_point"
    elif is_cuboid(obj):
        return "cuboid"
    elif is_raster(obj):
        return "raster"
    else:
        return None


def _from_scalar(obj):
    """
    Create a point spatial structure for a dataset with missing
    dimensions. The missing dimensions are built from coordinate
    information.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object with missing dimensions to build a new one from.

    Returns
    -------
    obj_n : xarray.Dataset, xarray.DataArray
        Object with point dimensions.

    Raises
    ------
    WindkitError :  WindkitError if the scalar cannot be converted
        to a point.
    """

    # if the spatial structure is already right, return it as is
    spatial_struct = get_spatial_struct(obj)
    if spatial_struct is not None and spatial_struct not in ("raster", "stacked_point"):
        return obj

    z_dim = _vertical_dim()
    x_y_dim = _xy_dims()
    x_y_z_dim = list(x_y_dim) + [z_dim]
    stacked_point_dim = _stacked_point_dim()

    if (
        z_dim in obj.dims
        and stacked_point_dim not in obj.dims
        and all(x in obj.coords for x in x_y_dim)
    ):
        # the scalar comes from a stacked point

        obj_n = (
            obj.reset_coords(x_y_dim)
            .expand_dims("stacked_point", -1)
            .set_coords(x_y_dim)
        )

    elif (
        all(x in obj.coords for x in x_y_z_dim)
        and all(x not in obj.dims for x in x_y_z_dim)
        and stacked_point_dim not in obj.dims
    ):
        obj_n = (
            obj.reset_coords(x_y_z_dim).expand_dims("point", -1).set_coords(x_y_z_dim)
        )
    elif (
        z_dim in obj.coords and z_dim not in obj.dims and stacked_point_dim in obj.dims
    ):
        # the scalar comes from a stacked point and the height is missing
        obj_n = obj.expand_dims(z_dim)
        # the dimensions must be rearranged like (...,height,stacked_point)
        all_dims = list(obj_n.dims)
        if len(all_dims) > 2:
            # there are more dimensions apart from stacked_point,height
            other_dims = [x for x in all_dims if x not in (stacked_point_dim, z_dim)]

            rearranged_dims = other_dims + [z_dim, stacked_point_dim]
            obj_n = obj_n.transpose(*rearranged_dims)
        else:
            obj_n = obj_n.transpose(z_dim, stacked_point_dim)
    elif spatial_struct is None:
        raise WindkitError("Cannot convert scalar, unknown spatial structure.")
    else:
        # it was a stacked point or a raster that was not a scalar
        return obj
    # drop height for 2D variables
    for k, val in obj_n.data_vars.items():
        if val.attrs.get("2d_or_3d", None) == "2D":
            obj_n[k] = val.isel(height=0).drop_dims("height", drop=True)
    return obj_n


def _get_xy_dims(obj):
    """Get the horizontal dimension(s) of a dataset.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to get the horizontal dimension(s) from.

    Returns
    -------
    tuple:
        Tuple containing the horizontal dimension(s) name(s).
        Results can be:
            ("point",)
            ("stacked_point",)
            ("west_east", "south_north")

    Raises
    ------
    ValueError
        Raised if no spatial dimension(s) could be found.

    """
    struct = get_spatial_struct(obj)
    if struct == "point":
        return ("point",)
    elif struct == "stacked_point":
        return ("stacked_point",)
    elif struct in ["cuboid", "raster"]:
        return ("west_east", "south_north")
    else:
        raise ValueError("Spatial struct not recognized!")
