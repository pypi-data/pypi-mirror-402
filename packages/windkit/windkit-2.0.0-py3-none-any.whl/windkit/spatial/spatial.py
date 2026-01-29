# (c) 2022 DTU Wind Energy
"""
Public interface to all of the spatial tools in WindKit
"""

__all__ = [
    "are_spatially_equal",
    "clip",
    "clip_with_margin",
    "create_dataset",
    "create_point",
    "create_stacked_point",
    "create_cuboid",
    "create_raster",
    "count_spatial_points",
    "equal_spatial_shape",
    "mask",
    "reproject",
    "warp",
    "nearest_points",
    "covers",
    "gdf_to_ds",
    "ds_to_gdf",
    "add_projected_wrf_coordinates",
]

import logging
import warnings

import geopandas as gpd
import numpy as np
import pyproj
import xarray as xr
from scipy.spatial import KDTree

from ..xarray_structures.metadata import (
    _GLOBAL_CONVENTIONS,
    _ALL_VARS_META,
    _update_history,
)
from ._crs import set_crs, get_crs
from ._bbox import BBox
from ._dimensions import _point_dim, _stacked_point_dim, _vertical_dim, _xy_dims
from ._point import _mask_point, is_point, is_stacked_point, to_point, to_stacked_point
from ._raster import _bounds as _raster_bounds
from ._raster import (
    _can_be_raster,
    _clip_to_bbox_raster,
    _has_raster_dims,
    _mask_raster,
)
from ._raster import _resolution as _raster_resolution
from ._raster import (
    _warp_raster,
    to_raster,
)
from ._struct import (
    _from_scalar,
    get_spatial_struct,
    is_cuboid,
    is_raster,
    _is_vertical,
)
from ._vector import _clip_vector
from ._vertical import has_height_coord, has_height_dim

logger = logging.getLogger(__name__)

_STACK_ATTRS = ("_pwio_was_stacked_point", "_pwio_was_cuboid", "_pwio_orig_srs_wkt")


def count_spatial_points(obj):
    """Get the number of spatial points for a dataset or DataArray

    Parameters
    ----------
    obj: xarray.Dataset, xarray.DataArray
        WindKit xarray dataset or dataarray containing spatial dimensions.

    Raises
    ------
    ValueError
        Undetectable spatial structure
    """
    obj = _from_scalar(obj)
    dims = obj.sizes

    # Get dimension names
    xdim, ydim = _xy_dims()
    pt_dim = _point_dim()
    vert_dim = _vertical_dim()
    spt_dim = _stacked_point_dim()

    if is_cuboid(obj):
        return dims[vert_dim] * dims[ydim] * dims[xdim]
    elif is_raster(obj):
        return dims[ydim] * dims[xdim]
    elif is_stacked_point(obj):
        return dims[vert_dim] * dims[spt_dim]
    elif is_point(obj):
        return dims[pt_dim]
    else:
        raise ValueError("Unknown data structure cannot count points.")


def are_spatially_equal(obj_a, obj_b):
    """Checks that the spatial points are equivalent for both datasets

    Parameters
    ----------
    obj_a, obj_b : xarray.Dataset, xarray.DataArray
        WindKit xarray dataset or dataarray containing spatial
        dimensions and CRS variable

    Returns
    -------
    bool
        True if spatial coords are numpy.allclose

    """
    x_dim, y_dim = _xy_dims()

    if obj_a.coords[x_dim].size != obj_b.coords[x_dim].size:
        return False
    if obj_a.coords[y_dim].size != obj_b.coords[y_dim].size:
        return False
    return np.allclose(obj_a[x_dim], obj_b[x_dim]) and np.allclose(
        obj_a[y_dim], obj_b[y_dim]
    )


def create_dataset(west_east, south_north, height, crs, struct="auto", thresh=1e-9):
    """Create a WindKit dataset given a set of locations.

    Parameters
    ----------
    west_east : array_like
        1D array of west_east locations of interest
    south_north : array_like
        1D array of south_north locations of interest
    height : array_like
        Array of heights to create in output WindKit xarray dataset
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize :py:class:`pyproj.crs.CRS`
    struct : str
        Used to specify the type of dataset that is desired
        Valid values are 'auto', 'cuboid', 'point' and
        'stacked_point'. The default value of 'auto' tries to create a cuboid,
        but falls back to point depending on the values specified.
    thresh : float
        Threshold value for raster detection
        Default set to 1e-9 m

    Returns
    -------
    xarray.Dataset
        WindKit formated zero-filled Dataset with one variable "output"
        and with the grid dimensions specified

    Notes
    -----
    This function will create a WindKit formatted dataset including all of the
    geospatial information that is desired.

    If ds_fmt is set to "auto", the function will attempt to create a cuboid,
    if the deviation between the largest and smallest interval along west_east
    and south_north are lower than value in thresh (west_east and south north
    can be different lengths). Otherwise, the function will attempt to make a
    point dataset. Specifically, it will create a 3D point object,
    if west_east, south_north and heights have the same lengths.
    If west_east and south_north have the same lengths but heights length is
    different the function will create a 2D point object.

    Alternatively, ds_fmt can be set to desired output format, that is  'cuboid',
    'stacked_point' and 'point', which accordingly requires specific structures
    of west_east, south_north and heights (as described above):

        * ``cuboid``:
            west_east, south_north, and heights must contain unique points along their
            dimension, and west_east and south_north are evenly spaced

        * ``stacked_point``:
            west_east and south_north must have the same length, but heights will have
            unique values representing the dimension values

        * ``point``:
            west_east, south_north and heights must have same lengths

    """

    # Ensure that all input arrays are 1d
    x, y, z = np.atleast_1d(west_east, south_north, height)

    if struct.lower() == "auto":
        if _has_raster_dims(x, y):
            struct = "cuboid"
        elif (y.size == x.size) and (x.size != z.size):
            struct = "stacked_point"
        elif (y.size == x.size) and (y.size == z.size):
            struct = "point"
        else:
            raise ValueError("Cannot identify struct of input data.")

    # Get names of dimensions
    x_dim, y_dim = _xy_dims()
    z_dim = _vertical_dim()
    pt_dim = _point_dim()
    stacked_pt_dim = _stacked_point_dim()

    if struct.lower() == "cuboid":
        if not _has_raster_dims(x, y):
            raise ValueError("Data cannot be converted to raster or cuboid dataset.")

        # Create spatial data arrays
        shape = z.size, y.size, x.size
        dims = (z_dim, y_dim, x_dim)
        z_coord = ((z_dim,), z)
        y_coord = ((y_dim,), y)
        x_coord = ((x_dim,), x)

    elif struct.lower() == "stacked_point":
        # Raise error if point array cannot be made
        if y.size != x.size:
            err_str = "south_north and west_east sizes do not match."
            raise ValueError(err_str)

        # make sure the heights in the z array are unique
        z = np.unique(z)
        # Create spatial data arrays
        shape = z.size, x.size
        dims = (z_dim, stacked_pt_dim)
        z_coord = ((z_dim,), z)
        y_coord = ((stacked_pt_dim,), y)
        x_coord = ((stacked_pt_dim,), x)

    elif struct.lower() == "point":
        # Raise error if point array cannot be made
        if (y.size != x.size) | (y.size != z.size):
            err_str = (
                "point dataset cannot be made with input " + "arrays of differing sizes"
            )
            raise ValueError(err_str)

        # Create spatial data arrays
        shape = (x.size,)
        dims = (pt_dim,)
        z_coord = ((pt_dim,), z)
        y_coord = ((pt_dim,), y)
        x_coord = ((pt_dim,), x)

    else:
        raise ValueError("Unknown struct provided.")

    # Build DataArray
    data = np.zeros(shape)
    coords = {z_dim: z_coord, y_dim: y_coord, x_dim: x_coord}
    out_da = xr.DataArray(data=data, dims=dims, coords=coords)

    # Build dataset with crs for storing results
    out_ds = out_da.to_dataset(name="output")
    out_ds = set_crs(out_ds, crs)

    out_ds[z_dim].attrs = _ALL_VARS_META[z_dim]
    out_ds.attrs = _GLOBAL_CONVENTIONS
    return _update_history(out_ds)


def create_point(west_east, south_north, height, crs):
    """Create a WindKit point dataset given a set of locations.

    Parameters
    ----------
    west_east : array_like
        1D array of west_east locations of interest
    south_north : array_like
        1D array of south_north locations of interest
    height : array_like
        Array of heights to create in output WindKit xarray dataset
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize :py:class:`pyproj.crs.CRS`

    Returns
    -------
    xarray.Dataset
        WindKit formated zero-filled Dataset with one variable "output"
        and with the grid dimensions specified

    Notes
    -----
    This function will create a WindKit formatted dataset including all of the
    geospatial information that is desired.

    """

    return create_dataset(west_east, south_north, height, crs, struct="point")


def create_stacked_point(west_east, south_north, height, crs):
    """Create a WindKit stacked point dataset given a set of locations.

    Parameters
    ----------
    west_east : array_like
        1D array of west_east locations of interest
    south_north : array_like
        1D array of south_north locations of interest
    height : array_like
        Array of heights to create in output WindKit xarray dataset
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`

    Returns
    -------
    xarray.Dataset
        WindKit formated zero-filled Dataset with one variable "output"
        and with the grid dimensions specified

    Notes
    -----
    This function will create a WindKit formatted dataset including all of the
    geospatial information that is desired.

    """

    return create_dataset(west_east, south_north, height, crs, struct="stacked_point")


def create_cuboid(west_east, south_north, height, crs):
    """Create a WindKit cuboid dataset given a set of locations.

    Parameters
    ----------
    west_east : array_like
        1D array of west_east locations of interest
    south_north : array_like
        1D array of south_north locations of interest
    height : array_like
        Array of heights to create in output WindKit xarray dataset
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`

    Returns
    -------
    xarray.Dataset
        WindKit formated zero-filled Dataset with one variable "output"
        and with the grid dimensions specified

    Notes
    -----
    This function will create a WindKit formatted dataset including all of the
    geospatial information that is desired.

    """

    return create_dataset(west_east, south_north, height, crs, struct="cuboid")


def create_raster(west_east, south_north, crs):
    """Create a WindKit raster dataset given a set of locations.

    Parameters
    ----------
    west_east : array_like
        1D array of west_east locations of interest
    south_north : array_like
        1D array of south_north locations of interest
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`

    Returns
    -------
    xarray.Dataset
        WindKit formated zero-filled Dataset with one variable "output"
        and with the grid dimensions specified

    Notes
    -----
    This function will create a WindKit formatted dataset including all of the
    geospatial information that is desired.

    """

    return create_dataset(west_east, south_north, [0], crs, struct="cuboid")


def _replace_close(arr, thresh=1e-9):  # pragma:no cover internal
    """Replace all values that are close to each other with an identical value

    Parameters
    ----------
    arr : array_like
        Array to be examined
    thresh : float
        Threshold value for checking spatial separation between coordinates
        Default set to 1e-9 m


    Returns
    -------
    array_like
        Array of the same shape and dtype as arr,
        but with close values replaced
    """

    unq = np.sort(np.unique(arr))
    diff_unq = np.diff(unq)
    if any(diff_unq <= thresh):
        for i, diff in enumerate(diff_unq):
            if diff <= thresh:
                val = unq[i]
                arr = np.where(np.isclose(arr, val), val, arr)

    return arr


def reproject(obj, to_crs, copy=True):
    """Reprojects WindKit object a new CRS without changing the data.

    If the input is a xarray.Dataset or xarray.DataArray with
    a 'cuboid' spatial structure, the spatial
    structure will be changed to 'stacked_point', since the coordiates of the new
    dataset will no longer be regularly spaced.

    Parameters
    ----------
    obj : geopandas.GeoDataFrame, xarray.DataArray, xarray.Dataset, or BBox
        WindKit object that will be reprojected.
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize :py:class:`pyproj.crs.CRS`
    copy : bool
       If true, the object is copied. Defaults to True.

    Returns
    -------
    geopandas.GeoDataFrame, xarray.DataArray,xarray.Dataset, or BBox
        WindKit object with new projection

    See Also
    --------
    warp

    Notes
    -----
    This script reprojects the coordinates of the data, and reshapes the data
    from ``cuboid`` or ``raster`` to ``stacked_point``. This is done so that none of
    the data is interpolated, but rather the coordinates are just changed to match
    those of the new projection. If you want to keep your data in ``cuboid`` or
    ``raster`` format, use the function ``warp`` instead, which however does do
    interpolation of the data.

    """

    #
    if isinstance(obj, gpd.GeoDataFrame) or isinstance(obj, gpd.GeoSeries):
        return obj.to_crs(to_crs)
    elif isinstance(obj, BBox):
        return obj.reproject(to_crs)

    # From here we know that the input object is
    # a xarray.Dataset or xarray.DataArray

    if copy:
        obj = obj.copy()

    # Get input CRS object
    try:
        from_crs = get_crs(obj)
    except ValueError:
        raise ValueError(
            "No CRS found on object! Please set with:" + " obj = set_crs(obj, crs)!"
        )

    # Get spatial dim names
    x_dim, y_dim = _xy_dims()

    # Get output CRS object
    to_crs = pyproj.CRS.from_user_input(to_crs)

    # Reproject dimensions
    transformer = pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=True)

    struct = get_spatial_struct(obj)

    if struct in ["raster", "cuboid"]:
        obj = to_stacked_point(obj)
        struct = "stacked_point"
    elif struct is None:
        try:
            obj = _from_scalar(obj)
            struct = get_spatial_struct(obj)
        except Exception:
            raise RuntimeError("Could not determine spatial structure of your data.")

    # Add warnings filter for numpy=1.25 from pyproj.
    # See: https://github.com/pyproj4/pyproj/issues/1307
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message="Conversion of an array with ndim > 0"
        )
        x_new, y_new = transformer.transform(obj[x_dim].values, obj[y_dim].values)

    x_new = _replace_close(x_new)
    y_new = _replace_close(y_new)

    obj = obj.drop_vars([x_dim, y_dim])
    obj = obj.assign_coords({x_dim: ((struct), x_new), y_dim: ((struct), y_new)})

    obj = set_crs(obj, to_crs)

    return obj


def warp(
    obj, to_crs, resolution=None, method="nearest", nodata=None, coerce_to_float=True
):
    """Warp cuboid WindKit object to another in a new CRS using data interpolation.

    Parameters
    ----------
    obj : xarray.DataArray or xarray.Dataset
        WindKit object to warp.
    to_crs : int, dict, str or CRS
        Value to create CRS object or an existing CRS object
    resolution :  tuple (x resolution, y resolution) or float, optional
        Target resolution, in units of target coordinate reference
        system. Default: None calculates a resolution in the target crs similar
        to the resolution of the original crs.
    method : str
        Interpolation method, passed to rasterio.warp.reproject. Defaults to "nearest".
    nodata : scalar
        Initial data to fill output arrays, passed to rasterio.warp.reproject. Defaults to
        numpy.nan.

    Returns
    -------
    xarray.DataArray or xarray.Dataset
        Warped WindKit object.

    See Also
    --------
    reproject
    """
    kwargs = {
        "resolution": resolution,
        "method": method,
        "nodata": nodata,
        "coerce_to_float": coerce_to_float,
    }
    if isinstance(obj, (xr.Dataset, xr.DataArray)):
        struct = get_spatial_struct(obj)
        if struct in ["raster", "cuboid"]:
            obj = _warp_raster(obj, to_crs, **kwargs)
            if isinstance(obj, xr.Dataset):
                return _update_history(obj)
            else:
                return obj
        else:
            raise ValueError(
                "Only 'raster' and 'cuboid' objects currently" + " supports warping!"
            )
    else:
        raise ValueError(
            "Only xarray Dataset and DataArray objects "
            + "currently supported for warping"
        )


def mask(obj, mask, all_touched=False, invert=False, nodata=None, **kwargs):
    """Mask WindKit object with geometric mask.

    Masking an object returns the same object with values outside of the masked
    region filled with NaN.

    Parameters
    ----------
    obj : xarray.Dataset,xarray.DataArray
        WindKit object to mask.
    mask : geopandas.GeoDataFrame or BBox
        Mask to mask object by.
    all_touched : bool
        *raster* or *cuboid* only: Include all pixels touched by the mask? False
        includes only those that pass through the center. Passed to
        rasterio.features.geometry_mask. Defaults to False.
    invert : bool
        *raster* or *cuboid* only: If true values outside of the mask will be nulled,
        if False values inside the mask are nulled. Opposite is passed to
        rio.features.geometry_mask. Defaults to False.
    nodata : float
        *raster* or *cuboid* only: If no data is not None, all masked data will be filled
        with this value. Default, masked data is set to NaN.

    Returns
    -------
    same as obj
        Clipped WindKit object.

    See Also
    --------
    clip

    Note
    ----
    This function behaves the opposite of rasterio.features.geometry_mask by default, in
    that it nulls areas outside of the area of interest rather than inside.
    For rasters, when the mask edges intersects with the cell centers they are not guaranteed to be
    included. It is recommend to use a buffer or all_touched=True to be sure.
    """
    kwargs = {
        **kwargs,
        "all_touched": all_touched,
        "invert": invert,
        "nodata": nodata,
    }
    if isinstance(obj, (xr.Dataset, xr.DataArray)):
        struct = get_spatial_struct(obj)
        if struct in ["raster", "cuboid"]:
            obj = _mask_raster(obj, mask, drop=False, **kwargs)
            if isinstance(obj, xr.Dataset):
                return _update_history(obj)
            else:
                return obj
        elif struct in ["point", "stacked_point"]:
            obj = _mask_point(obj, mask, drop=False, **kwargs)
            if isinstance(obj, xr.Dataset):
                return _update_history(obj)
            else:
                return obj
        else:
            raise ValueError("Spatial structure not supported!")
    else:
        raise ValueError("Object not supported!")


def clip(obj, mask, all_touched=False, invert=False, nodata=None, **kwargs):
    """Clip object to mask.

    Clipping returns an object that has been reduced to the requested shape. Dropping
    data that falls outside of the masked region.

    Parameters
    ----------
    obj : geopandas.GeoDataFrame, xarray.DataArray or xarray.Dataset
        Object with raster-like dimensions to clip with mask.
    mask : geopandas.GeoDataFrame or BBox
        Geometric features to clip out of object.
    all_touched : bool
        *raster* or *cuboid* only: Include all pixels touched by the mask? False
        inclodes only those that pass through the center. Passed to
        rasterio.features.geometry_mask. Defaults to False.
    invert : bool
        *raster* or *cuboid* only: If true values outside of the mask will be nulled,
        if False values inside the mask are nulled. Opposite is passed to
        rio.features.geometry_mask. Defaults to False.
    nodata : float
        *raster* or *cuboid* only: If no data is not None, all masked data will be filled
        with this value. Default, masked data is set to NaN.
    kwargs : dict
        Other keyword-arguments are passed to the underlying function, depending
        on the type of object.

    Returns
    -------
    geopandas.GeoDataFrame, xarray.DataArray,xarray.Dataset
        Object of the same type as obj clipped by geometric features.

    See Also
    --------
    mask

    Notes
    -----
    This function behaves the opposite of rasterio.features.geometry_mask by default, in
    that it nulls areas outside of the area of interest rather than inside.
    For rasters, when the mask edges intersects with the cell centers they are not guaranteed to be
    included. It is recommend to use a buffer or all_touched=True to be sure.
    """
    kwargs = {**kwargs, "all_touched": all_touched, "invert": invert, "nodata": nodata}

    if isinstance(obj, gpd.GeoDataFrame) or isinstance(obj, gpd.GeoSeries):
        return _clip_vector(obj, mask, **kwargs)
    elif isinstance(obj, (xr.Dataset, xr.DataArray)):
        struct = get_spatial_struct(obj)
        if struct in ["raster", "cuboid"]:
            if isinstance(mask, BBox):
                obj = _clip_to_bbox_raster(obj, mask)
            else:
                obj = _mask_raster(obj, mask, drop=True, **kwargs)
            if isinstance(obj, xr.Dataset):
                return _update_history(obj)
            else:
                return obj
        elif struct in ["point", "stacked_point"]:
            obj = _mask_point(obj, mask, drop=True, **kwargs)
            if isinstance(obj, xr.Dataset):
                return _update_history(obj)
            else:
                return obj
        else:
            raise ValueError("Spatial structure not supported!")
    else:
        raise ValueError("Object not supported!")


def _spatial_stack(
    source, target_crs=None, revertable=True, copy=True, remove_height=False
):
    """Returns source in a revertable version of the "point" format

    This routine can be used to ensure a consistent input form to external routines, by
    always returning in "point" format. It can also do reprojection, and remove the
    height field to make the result a 2D spatial object.

    Parameters
    ----------
    source : xarray.DataSet
        WindKit dataset containing spatial dimensions and CRS variable to convert
    target_crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        (Default is to not reproject.)
    revertable : bool
        Should we retain information about the original datastructure so we can revert
        this process? This is typically True, but should be False when interpolating
        the data to a new projection.
    copy : bool
        Should we make a copy of the initial dataset? This is typically true as we don't
        want to manipulate the original object, but work on a new version.
    remove_height : bool
        Is the resulting object always 2D? This is typically false, but can be useful in
        some instances.

    Returns
    -------
    stacked : xarray.DataSet
        WindKit formated xr.DataSet as a point object on the new projection and
        with additional that allow it to be converted back to its original form
        using _spatial_unstack.

    Notes
    -----
    This routine serves two purposes:
    1. Convert source to a point object, storing its former structure.
    2. Reproject to the target_crs if provided, and not already met.
    """
    if copy:
        source = source.copy(deep=True)

    # For some routines, we don't want to pass a height dimesion, so remove it if asked
    if remove_height:
        if has_height_dim(source):
            source = source.isel(height=0, drop=True)
        if has_height_coord(source):
            del source["height"]

    # Remove attributes from previous call if found
    if not is_point(source):
        for attr in _STACK_ATTRS:
            if attr in source.attrs:
                del source.attrs[attr]

    # Label original format and get 2D variables if not "point"
    orig_format = get_spatial_struct(source)
    if revertable and orig_format in ("stacked_point", "cuboid", "raster"):
        logger.debug("Converting from original format %s", orig_format)
        source.attrs[f"_pwio_was_{orig_format}"] = True

        # Identify 2D variables
        if has_height_dim(source):
            hgt_dim = _vertical_dim()
            for var in source.data_vars:
                logger.debug("Flagging variable %s as 2d variable", var)
                source[var].attrs["_pwio_data_is_2d"] = hgt_dim not in source[var].dims

    # Reproject if requested
    source_crs = get_crs(source)
    if target_crs is not None:
        target_crs = pyproj.CRS.from_user_input(target_crs)
        if source_crs != target_crs:
            if revertable:
                source.attrs["_pwio_orig_srs_wkt"] = source_crs.to_wkt()
            return reproject(to_point(source), target_crs)

    ds = to_point(source)
    return _update_history(ds)


def _spatial_unstack(source):
    """Unstacks a point object that was created using _spatial_stack

    Parameters
    ----------
    source : xarray.DataSet
        WindKit dataset containing spatial dimensions and CRS variable to revert

    Returns
    -------
    WindKit dataset
        Source dataset structured as it was originally.

    Notes
    -----
    This is the companion function to _spatial_stack and does 2 things:
    1. Converts 3D-point object to either raster or 2D-point object
    2. Reprojects converted object back to its original projection
    """
    # Check that source was previously reprojected
    if "_pwio_orig_srs_wkt" in source.attrs:
        source = reproject(source, source.attrs["_pwio_orig_srs_wkt"])
        del source.attrs["_pwio_orig_srs_wkt"]

    # Convert back to original format
    if "_pwio_was_raster" in source.attrs:
        source = to_raster(source, True)
        del source.attrs["_pwio_was_raster"]
    elif "_pwio_was_cuboid" in source.attrs:
        source = to_raster(source, True)
        del source.attrs["_pwio_was_cuboid"]
    elif "_pwio_was_stacked_point" in source.attrs:
        source = to_stacked_point(source)
        del source.attrs["_pwio_was_stacked_point"]

    # Transpose the coordinates to match netCDF best practices
    hgt_dim = (_vertical_dim(),) if _is_vertical(source) else ()
    if is_stacked_point(source):
        geo_dims_order = hgt_dim + ("stacked_point",)
    elif is_raster(source):  # also a cuboid is a raster, if it includes a hgt_dim
        geo_dims_order = hgt_dim + ("south_north", "west_east")
    else:
        geo_dims_order = ("point",)

    # Removing _pwio_data_is_2d attr from dataset
    for var in source.data_vars.keys():
        if "_pwio_data_is_2d" in source[var].attrs:
            source[var].attrs.pop("_pwio_data_is_2d", None)

    ds = source.transpose(..., *geo_dims_order)
    return _update_history(ds)


def nearest_points(
    ds_ref: xr.Dataset,
    ds_target: xr.Dataset,
    dims=["west_east", "south_north", "height"],
    n_nearest=1,
    return_rank=False,
    return_distance=False,
    keep_duplicates=True,
):
    """Get nearest points from dataset in windkit spatial structure

    Parameters
    ----------
    ds_ref : xr.Dataset
        Input dataset of which we want to select nearest points
    ds_target : xr.Dataset
        Target dataset of the points we want to obtain from the input
    dims : list of strings
        Dimensions which we want to use for nearest neighbour lookup
    n_nearest: int
        Number of closest points to return for each point in ds_target
    return_rank: bool
        Return the rank of closeness
    return_distance: bool
        Return the distance to closest point
    keep_duplicates: bool, default True
        If True and ds_target is a point structure
        and there is any duplicates created during the nearest
        neighbour mapping, these will be kept in the dataset so that the
        output structure is the same as ds_target. If False, removes them
        from the data.

    Returns
    -------
    xr.Dataset
        The points from ds_ref that are nearest to ds_target (i.e. ds will have the same spatial structure as ds_target)

    Raises
    ------
    RunTimeError
        if the data is not in point format and there is duplicates
        created during the nearest neighbour mapping.
    """
    if get_crs(ds_ref).is_geographic or get_crs(ds_target).is_geographic:
        warnings.warn(
            "You are doing nearest neighbour lookup in non metric coordinate systems!"
        )
    if get_crs(ds_ref) != get_crs(ds_target):
        raise ValueError("Datasets must have the same coordinate system!")

    # stack so that we also work with point structure
    ds_ref = to_point(ds_ref)
    was_point = is_point(ds_target)

    # if we ask for only the nearest 1 point the data structure
    # remains the same as ds_target, so we can recover the original
    # by _spatial_unstack.
    if n_nearest == 1:
        ds_target = _spatial_stack(ds_target)
    else:
        ds_target = to_point(ds_target)

    arrays = np.array([np.atleast_1d(ds_ref[x].values) for x in dims]).T
    arrays_target = np.array([np.atleast_1d(ds_target[x].values) for x in dims]).T
    tree = KDTree(arrays)
    distance, ii = tree.query(arrays_target, k=n_nearest)

    if n_nearest == 1:
        dims = ("point",)
    else:
        dims = ("point", "rank")

    da_distance = xr.DataArray(distance, dims=dims)

    if not keep_duplicates and n_nearest > 1:
        raise ValueError(
            "n_nearest cannot be more than 1 when you want to keep duplicates"
        )

    if ii.size != np.unique(ii).size and n_nearest == 1:
        if not was_point and keep_duplicates:
            raise RuntimeError(
                "You have multiple points in your target dataset mapping to the same point in your source ds. You can use 'to_point' to convert your data to a point dataset to keep them or set keep_duplicates=False"
            )
        elif not keep_duplicates:
            warnings.warn(
                "You have multiple points in your target dataset mapping to the same point in your source ds. The resulting duplicates will be removed from the output! If you want to keep these duplicates, use keep_duplicates=True."
            )
        if not keep_duplicates:
            da_distance = xr.DataArray(distance, coords={"point": ii}, dims=dims)
            da_distance = (
                da_distance.where(
                    ~da_distance.indexes["point"].duplicated(keep="first")
                )
                .dropna("point")
                .drop_vars("point", errors="i")
            )
            ii = np.unique(ii)

    idx = xr.DataArray(ii, dims=dims)
    nearest = ds_ref.isel(point=idx)

    if "rank" in dims and return_rank:
        nearest["rank"] = (("rank",), np.arange(n_nearest))

    if return_distance:
        nearest["distance"] = da_distance

    if n_nearest == 1:
        # make sure that we unstack to the target structure
        nearest = nearest.assign_attrs(
            {k: v for k, v in ds_target.attrs.items() if "_pwio" in k}
        )
        ds = _spatial_unstack(nearest)
        return _update_history(ds)
    else:
        nearest = (
            nearest.rename({"point": "point_tmp"})
            .stack(point=("point_tmp", "rank"))
            .reset_index("point")
            .drop_vars("point_tmp")
        )
        if not return_rank:
            nearest = nearest.drop_vars("rank")
        return _update_history(nearest)


def covers(obj_a, obj_b):
    """
    Checks if obj_a covers obj_b

    Parameters
    ----------
    obj_a : xarray.Dataset, xarray.DataArray
        WindKit xarray dataset or dataarray containing spatial dimensions.
        Only cuboid structure is currently supported for obj_a.
    obj_b : xarray.Dataset, xarray.DataArray
        WindKit xarray dataset or dataarray containing spatial dimensions.

    Returns
    -------
    bool
        True if obj_a covers obj_b
    """

    if not is_cuboid(obj_a):
        raise ValueError(
            "obj_a must be cuboid structure, got:", get_spatial_struct(obj_a)
        )

    x_dim, y_dim = _xy_dims()
    z_dim = _vertical_dim()

    x_min, x_max = obj_a[x_dim].min(), obj_a[x_dim].max()
    y_min, y_max = obj_a[y_dim].min(), obj_a[y_dim].max()
    z_min, z_max = obj_a[z_dim].min(), obj_a[z_dim].max()

    x, y, z = obj_b[x_dim], obj_b[y_dim], obj_b[z_dim]

    return (
        (x_min <= x).all()
        & (x <= x_max).all()
        & (y_min <= y).all()
        & (y <= y_max).all()
        & (z_min <= z).all()
        & (z <= z_max).all()
    )


def clip_with_margin(
    obj_to_clip, obj_clipper, margin_dx_factor=5.0, cap_style=1, join_style=1
):
    """
    Clip a 'raster' or 'cuboid' dataset to the bounding box of another 'raster', 'cuboid', 'stacked_point',
    or 'point' dataset including a margin around that dataset to ensure several points are avaiable around
    the clipper dataset from the clipped one.

    Parameters
    ----------
    obj_to_clip : xarray Dataset or DataArray
        The dataset to clip
    obj_clipper : xarray Dataset or DataArray
        The dataset to clip to
    margin_dx_factor : float, optional
        The margin to add to the bounding box of the clipper dataset, by default 5.0,
        i.e. 5 times the grid spacing of the dataset to clip
    cap_style : int, optional
        The cap style to use for buffering the bounding box of the clipper dataset,
        by default 1 (round buffering)
    join_style : int, optional
        The join style to use for buffering the bounding box of the clipper dataset,
        by default 1 (round buffering)

    Returns
    -------
    xarray Dataset or DataArray
        The clipped dataset

    """
    obj_to_clip = obj_to_clip.copy()

    if not isinstance(obj_to_clip, (xr.Dataset, xr.DataArray)):
        raise TypeError("obj_to_clip must be an xarray Dataset or DataArray")

    if not isinstance(obj_clipper, (xr.Dataset, xr.DataArray)):
        raise TypeError("obj_clipper must be an xarray Dataset or DataArray")

    if not is_raster(obj_to_clip):
        raise ValueError("obj_to_clip must be a cuboid")

    # Get the CRS of the dataset to clip and the grid spacing resolution
    # to use for buffering of the bounding buffer
    # (5 times the resolution of the climate dataset)
    # We will use the bbox to clip the climate dataset before interpolation
    crs_clip = get_crs(obj_to_clip)
    spacing_clip, _ = _raster_resolution(obj_to_clip)
    bbox_buffer = margin_dx_factor * spacing_clip

    # Create a bounding box around the output locations buffered with enough edge points
    # for the interpolation to work¨
    # cap_style=1, join_style=1 is used (round buffering) to avoid issues with
    # spatial datasets of points forming a straigth line (default buffer is square
    # and wont buffer the points in this case)
    bbox = (
        BBox.from_ds(obj_clipper)
        .reproject(crs_clip, use_bounds=False)
        .buffer(bbox_buffer, cap_style=cap_style, join_style=join_style)
        .envelope()
    )

    # check if bbox is outside bounds of the dataset
    bounds_to_clip = _raster_bounds(obj_to_clip)
    bounds_bbox = bbox.bounds()
    x_size = abs(bounds_to_clip[0] - bounds_to_clip[2])
    if (
        bbox.crs.is_geographic
        and x_size >= 360
        and (bounds_bbox[0] < bounds_to_clip[0] or bounds_bbox[2] > bounds_to_clip[2])
    ):
        raise ValueError(
            "Bounding box is crossing the date line, this may result in missing data!"
        )
    elif (
        bounds_bbox[0] < bounds_to_clip[0]
        or bounds_bbox[1] < bounds_to_clip[1]
        or bounds_bbox[2] > bounds_to_clip[2]
        or bounds_bbox[3] > bounds_to_clip[3]
    ):
        warnings.warn(
            "Clipping bbox including marging is outside the bounds of the dataset to clip!"
        )

    # Clip the dataset to the bounding box
    return clip(obj_to_clip, bbox)


def equal_spatial_shape(obj_a, obj_b):
    """Check if two spatial objects have the same shape.

    Parameters
    ----------
    obj_a : xr.Dataset or xr.DataArray
        Spatial object.
    obj_b : xr.Dataset or xr.DataArray
        Spatial object.

    Returns
    -------
    bool
        True if the objects have the same shape, False otherwise.
    """
    struct_a = get_spatial_struct(obj_a)
    struct_b = get_spatial_struct(obj_b)

    if struct_a != struct_b:
        return False

    if struct_a == "point":
        return obj_a.point.size == obj_b.point.size
    elif struct_a == "stacked_point":
        return (
            obj_a.stacked_point.size == obj_b.stacked_point.size
            and obj_a.height.size == obj_b.height.size
        )
    elif struct_a == "cuboid":
        return (
            obj_a.west_east.size == obj_b.west_east.size
            and obj_a.south_north.size == obj_b.south_north.size
            and obj_a.height.size == obj_b.height.size
        )
    elif struct_a == "raster":
        return (
            obj_a.west_east.size == obj_b.west_east.size
            and obj_a.south_north.size == obj_b.south_north.size
        )
    else:
        raise ValueError(f"Unknown spatial structure '{struct_a}'.")


def ds_to_gdf(ds, include_height=False):
    """Convert windkit spatial structure to geopandas dataframe.

    Parameters
    ----------
    ds : xr.Dataset or xr.DataArray
        Spatial object.
    include_height : boolean, optional
        Default False, do not include the height dimension in the geopandas dataframe

    Returns
    -------
    gdf : gpd.GeoDataFrame
        GeoDataFrame with columns ``x``, ``y`` and optionally ``z`` if include_height is True

    Notes
    -----
    If a coordinate ``name`` is present on the dataset, it will be included
    in the geodataframe as well. This can be convenient when you have mast
    locations that have a name/label. Note that if your dataset is in cuboid
    or stacked_point format, it will be flattened to a point structure.
    """

    point_ds = to_point(ds)
    in_crs = get_crs(ds)
    struct = (point_ds.coords["west_east"], point_ds.coords["south_north"])
    if include_height:
        struct = struct + (point_ds.coords["height"],)
    try:
        gdf = gpd.GeoDataFrame(
            {"name": point_ds["name"]}, geometry=gpd.points_from_xy(*struct), crs=in_crs
        )
    except Exception:
        gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(*struct), crs=in_crs)

    return gdf.drop_duplicates()


def _get_coords_from_gdf(gdf, height=None):
    """
    Extracts the x, y, and z coordinates from a GeoDataFrame. If the GeoDataFrame
    does not contain z values, a specified height is used for all points.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame from which to extract the coordinates. The GeoDataFrame
        should contain a 'geometry' column with Point geometries. If the points
        do not have a z coordinate, the 'height' parameter must be provided.
    height : float or None
        The height to use for all points if the GeoDataFrame does not contain
        z values. If the GeoDataFrame does contain z values, this parameter is
        ignored. If the GeoDataFrame does not contain z values and this parameter
        is None, a ValueError is raised.

    Returns
    -------
    x, y, z : ndarray
        The x, y, and z coordinates of the points in the GeoDataFrame. The
        coordinates are returned as separate 1D numpy arrays.

    Raises
    ------
    ValueError
        If the GeoDataFrame does not contain z values and 'height' is None.
    """
    if all(gdf.geometry.has_z):
        df = gdf.geometry.get_coordinates(include_z=True)
    else:
        df = gdf.geometry.get_coordinates(include_z=False)
        if height is None:
            raise ValueError(
                "You must provide a height for the dataset, because the geodataframe only contains x and y!"
            )
        df["z"] = height

    if "name" in gdf.columns:
        df["name"] = gdf["name"]

    return df


def gdf_to_ds(gdf, height=None, struct=None):
    """Convert geopandas dataframe to windkit spatial structure.

    Parameters
    ----------
    gdf : gpd.GeoDataFrame
        Geopandas dataframe with geometry column
    height : float, optional
        The value of the height coordinate if it is not included in the gpd.GeoDataFrame.
    struct : {"point", "stacked_point", "cuboid"}
        Default None, which means detect the best fitting windkit spatial structure.

    Returns
    -------
    ds : xr.Dataset
        dataset with a windkit spatial structure.

    Notes
    -----
    If a column ``name`` is present on the GeoDataFrame and your data is
    in point or stacked_point structure, it will be included in the xr.Dataset as well.
    This can be convenient when you have mast locations that have a name/label.
    """
    df = _get_coords_from_gdf(gdf, height=height)

    if struct is None:
        z = df.set_index("z").index.unique()
        # check if dataset can be a raster
        if _can_be_raster(df.x, df.y):
            struct = "cuboid"
            # in horizontal plane we can have a cuboid, but height dimension is varying, so return point
            if np.mod(gdf.size, z.size) != 0:
                struct = "point"
        elif np.mod(gdf.size, z.size) == 0:
            struct = "stacked_point"
        else:
            struct = "point"

    if struct == "cuboid":
        x = sorted(set(df.x))
        y = sorted(set(df.y))
        z = sorted(set(df.z))
    elif struct == "stacked_point":
        df = df[~df.set_index(["x", "y"]).index.duplicated(keep="first")]
        x, y = df[["x", "y"]].values.T
        z = df.set_index(["z"]).index.unique()

    ds = create_dataset(x, y, z, struct=struct, crs=gdf.crs)

    if "name" in gdf.columns and (struct == "point" or struct == "stacked_point"):
        ds.coords["name"] = (struct, df["name"])

    return ds


def add_projected_wrf_coordinates(ds):
    """Add the west_east, south_north coordinates to a WRF xarray.Dataset output.

    Parameters
    ----------

    ds: xarray.Dataset
       Dataset that is the output of WRF, with TRUELAT1, TRUELAT2, MOAD_CEN_LAT, STAND_LON
       coordinates.

    Returns
    -------
    ds : xr.Dataset
        dataset with the windkit west_east, south_north coordinates.
    """
    if ds.MAP_PROJ == 1:
        wrf_proj = pyproj.Proj(
            proj="lcc",
            lat_1=ds.TRUELAT1,
            lat_2=ds.TRUELAT2,
            lat_0=ds.MOAD_CEN_LAT,
            lon_0=ds.STAND_LON,
            a=6370000,
            b=6370000,
        )
    # I have not verified if this works, easiest way to check is just write out
    # the wrfout and check that you can obtain the given lat/lon after reprojection
    # as described here:
    # https://fabienmaussion.info/2018/01/06/wrf-projection/
    # elif ds.MAP_PROJ == 2:
    #     wrf_proj = pyproj.Proj(proj='stere',
    #         lat_1=ds.TRUELAT1, lat_2=ds.TRUELAT2,
    #         lat_0=ds.MOAD_CEN_LAT, lon_0=ds.STAND_LON,
    #         a=6370000, b=6370000)
    # elif ds.MAP_PROJ == 0:
    #     wrf_proj = pyproj.Proj(proj='eqc',
    #                         lat_1=ds.TRUELAT1, lat_2=ds.TRUELAT2,
    #                         lat_0=ds.MOAD_CEN_LAT, lon_0=ds.STAND_LON,
    #                         a=6370000, b=6370000)
    elif ds.MAP_PROJ == 3:
        # radius earth has to be specified, see here:
        # https://gis.stackexchange.com/questions/203923/using-pyproj-and-mercator-x-0-0-and-y-0-0
        rad_earth = 6370000 * np.cos(np.radians(ds.TRUELAT1))
        wrf_proj = pyproj.Proj(
            proj="merc",
            lat_1=ds.TRUELAT1,
            lat_2=ds.TRUELAT2,
            lat_0=ds.MOAD_CEN_LAT,
            lon_0=ds.STAND_LON,
            a=rad_earth,
            b=rad_earth,
        )
    else:
        raise NotImplementedError(
            "Only llc and mercator (MAP_PROJ=1 or 3) supported at the moment!"
        )

    wgs_proj = pyproj.Proj(proj="latlong", datum="WGS84")
    trans = pyproj.Transformer.from_proj(wgs_proj, wrf_proj)
    e, n = trans.transform(ds.CEN_LON, ds.CEN_LAT)
    dx, dy = ds.DX, ds.DY
    nx, ny = ds.dims["west_east"], ds.dims["south_north"]
    x0 = -(nx - 1) / 2.0 * dx + e
    y0 = -(ny - 1) / 2.0 * dy + n
    x = np.arange(nx) * dx + x0
    y = np.arange(ny) * dy + y0
    ds = ds.assign_coords(
        west_east=(("west_east",), x), south_north=(("south_north"), y)
    )
    ds = set_crs(ds, wrf_proj.crs)

    return ds
