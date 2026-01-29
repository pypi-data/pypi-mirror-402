# (c) 2022 DTU Wind Energy
"""
Module for raster functions.
"""

import logging

import geopandas as gpd
import numpy as np
import pyproj
import rasterio as rio
import rasterio.features  # nopycln: import used as rio.features
import shapely
import xarray as xr
from affine import Affine

from ..import_manager import _import_optional_dependency
from ..xarray_structures.metadata import (
    _MAP_TYPE_ATTRS,
    _update_history,
    _update_var_attrs,
)
from ._crs import get_crs, set_crs
from ._dimensions import _point_dim, _stacked_point_dim, _vertical_dim, _xy_dims
from ._struct import is_cuboid, is_point, is_raster, is_stacked_point
from ._vertical import has_height_coord


def _shape(obj):
    """
    Get shape of raster part of xarray.Dataset or xarray.DataArray.

    Parameters
    ----------
    obj : xarray.DataSet, xarray.DataArray
        object to calcuate raster shape from.

    Returns
    -------
    tuple: shape
        (nx, ny)

    """
    x_dim, y_dim = _xy_dims()
    return obj[x_dim].values.size, obj[y_dim].values.size


def _internal_bounds(obj):
    """
    Get internal coordinate bounds (left, bottom, right, top)
    of raster part of xarray.Dataset or xarray.DataArray

    Parameters
    ----------
    obj : xarray.DataSet, xarray.DataArray
        xarray object with raster-like dimensions.

    Returns
    -------
    tuple: bounds
        (left, bottom, right, top)

    """
    x_dim, y_dim = _xy_dims()
    left, right = obj[x_dim].values[0], obj[x_dim].values[-1]
    bottom, top = obj[y_dim].values[0], obj[y_dim].values[-1]
    return left, bottom, right, top


def _resolution(obj):
    """
    Get resolution of raster part of xarray.Dataset
    or xarray.DataArray.

    Parameters
    ----------
    da : xarray.DataSet, xarray.DataArray
        Raster

    Returns
    -------
    tuple: (res_we, res_sn)
        Resolution in west_east and south_north directions.

    """
    left, bottom, right, top = _internal_bounds(obj)
    nx, ny = _shape(obj)
    res_x = (right - left) / (nx - 1)
    res_y = (top - bottom) / (ny - 1)
    return res_x, res_y


def _bounds(obj):
    """
    Get bounds of raster at cell edges.

    Parameters
    ----------
    da : xarray.DataArray
        Raster

    Returns
    -------
    bounds: tuple of floats
        (left, bottom, right, top)

    """
    left, bottom, right, top = _internal_bounds(obj)
    res_x, res_y = _resolution(obj)
    left -= res_x / 2.0
    bottom -= res_y / 2.0
    right += res_x / 2.0
    top += res_y / 2.0
    return left, bottom, right, top


def _spacing(obj):
    """
    Get spacing of raster.
    Assumes that dx and dy are the same. Fails if not.

    Parameters
    ----------
    da : xarray.DataArray
        Raster

    Returns
    -------
    spacing: float
        spacing of raster

    """
    dx, dy = map(abs, _resolution(obj))
    if not np.isclose(dx, dy):
        raise ValueError("DX and DY are not equal.")
    return dx


def _transform(obj):
    """
    Caculate transform from xarray.Dataset or xarray.DataArray
    with raster-like dimensions.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Raster

    Returns
    -------
    affine.Affine: transform
        Affine transform from the objects raster-like dimensions

    """
    left, bottom, right, top = _bounds(obj)
    res_x, res_y = _resolution(obj)
    return Affine.translation(left, bottom) * Affine.scale(res_x, res_y)


def _warp_raster(
    obj, to_crs, resolution=None, method="nearest", nodata=None, coerce_to_float=True
):  # pragma: no cover covered_in_public_method
    """
    Warp xarray.Dataset or xarray.DataArray raster-like part to
    new raster-like object in new projection.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object with raster-like part to warp to new projection.
    to_crs : int, str, dict, tuple, CRS
        Coordinate Reference System to warp raster-like part to.
    resolution : float, optional
        Resolution of the target raster. Derived from input by default.
    method : str, optional
        Interpolation method, "nearest" method used by default.
        Options are: "nearest", "bilinear", "cubic", "cubic_spline",
        "lanczos", "average", "mode", and "gauss"
    nodata : float, int, optional
        Value to use for cells outside the input space.
        By default, -9999 is used for integer data and np.nan for float data.
    coerce_to_float: boolean, optional
        By default True, allow output to have nan values by coercing to float.

    Returns
    -------
    xarray.Dataset, xarray.DataArray: warped_object
        Warped object in new projection.

    """

    def _warp(
        raster,
        dst_shape=None,
        src_transform=None,
        src_crs=None,
        dst_transform=None,
        dst_crs=None,
        dst_nodata=None,
        resampling=None,
        coerce_to_float=True,
    ):
        if nodata is None:
            nodata_ = (
                np.iinfo(raster.dtype).min if raster.dtype.kind in "ui" else np.nan
            )
        else:
            nodata_ = nodata

        dst_data = np.zeros(dst_shape, dtype=raster.dtype.type)
        dst_nodata = raster.dtype.type(nodata_)

        rio.warp.reproject(
            source=np.copy(raster.data),
            destination=dst_data,
            src_transform=src_affine,
            src_crs=src_crs,
            dst_transform=dst_affine,
            dst_crs=dst_crs,
            dst_nodata=dst_nodata,
            resampling=resampling,
        )

        if coerce_to_float:
            dst_data = np.where(dst_data != nodata_, dst_data, np.nan)

        return dst_data

    obj = obj.copy()
    x_dim, y_dim = _xy_dims()

    resampling = getattr(rio.enums.Resampling, method)

    src_crs = rio.crs.CRS.from_user_input(get_crs(obj))
    dst_crs = rio.crs.CRS.from_user_input(to_crs)

    src_affine = _transform(obj)
    src_bounds = _bounds(obj)
    src_nx, src_ny = _shape(obj)
    src_res_x, src_res_y = _resolution(obj)

    dst_affine, dst_nx, dst_ny = rio.warp.calculate_default_transform(
        src_crs, dst_crs, src_nx, src_ny, *src_bounds, resolution=resolution
    )

    dst_x, _ = dst_affine * (np.arange(dst_nx) + 0.5, np.zeros(dst_nx) + 0.5)
    _, dst_y = dst_affine * (np.zeros(dst_ny) + 0.5, np.arange(dst_ny) + 0.5)

    coords_new = {y_dim: dst_y, x_dim: dst_x}

    kwargs = dict(
        dst_shape=(dst_ny, dst_nx),
        src_transform=src_affine,
        src_crs=src_crs,
        dst_transform=dst_affine,
        dst_crs=dst_crs,
        resampling=resampling,
        coerce_to_float=coerce_to_float,
    )

    obj_new = xr.apply_ufunc(
        _warp,
        obj,
        input_core_dims=[[y_dim, x_dim]],
        output_core_dims=[[y_dim + "_tmp_new", x_dim + "_tmp_new"]],
        kwargs=kwargs,
        vectorize=True,
        keep_attrs=True,
        on_missing_core_dim="copy",
    )

    if coerce_to_float:

        def _delete_fillvalue_from_attrs(da):
            if "_FillValue" in da.attrs:
                del da.attrs["_FillValue"]
            return da

        if isinstance(obj_new, xr.Dataset):
            for var in obj_new.data_vars:
                obj_new[var] = _delete_fillvalue_from_attrs(obj_new[var])
        else:
            obj_new = _delete_fillvalue_from_attrs(obj_new)
    else:

        def _update_fillvalue(da):
            if da.dtype.kind in "ui":
                da.attrs["_FillValue"] = (
                    np.iinfo(da.data.dtype).min if nodata is None else nodata
                )
            return da

        if isinstance(obj_new, xr.Dataset):
            for var in obj_new.data_vars:
                obj_new[var] = _update_fillvalue(obj_new[var])
        else:
            obj_new = _update_fillvalue(obj_new)

    obj_new = obj_new.rename({y_dim + "_tmp_new": y_dim, x_dim + "_tmp_new": x_dim})
    obj_new = obj_new.assign_coords(**coords_new)
    obj_new = set_crs(obj_new, to_crs)

    if isinstance(obj, xr.Dataset):
        obj_new = _update_history(obj_new)

    return obj_new


def _trim_missing_on_edges(obj):
    """
    Trim raster-like object to remove missing pixels on the edges.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object with raster-like part to trim.

    Returns
    -------
    xarray.Dataset, xarray.DataArray: trimmed_obj
        Object with missing pixels on the edges removed.

    """
    x_dim, y_dim = _xy_dims()

    def _count_missing_pixels(da):
        """
        Count the number of missing pixels in a raster-like object.

        Parameters
        ----------
        da : xarray.DataArray
            Object with raster-like part to count missing pixels.

        Returns
        -------
        int: n_missing
            Number of missing pixels in the object.

        """
        return da.isnull().sum().data

    def _find_optimal_shrinkage_for_no_missing(da):
        """
        Find the optimal shrinkage to remove missing pixels on the edges.

        Shrinks uniformly on all sides until no missing pixels are left.
        # TODO: This could be optimized to only check the edges where missing pixels are found.

        Parameters
        ----------
        da : xarray.DataArray
            Object with raster-like part to find optimal shrinkage for.

        Returns
        -------
        int: n_shrink
            Number of pixels to remove on the edges to remove missing pixels.

        """

        da = da.copy()
        n_shrink = 0
        n_missing = _count_missing_pixels(da)
        while n_missing > 0:
            n_shrink += 1
            n_missing = _count_missing_pixels(
                da.isel(
                    {
                        x_dim: slice(n_shrink, -n_shrink),
                        y_dim: slice(n_shrink, -n_shrink),
                    }
                )
            )

        return n_shrink

    obj = obj.copy()

    # Start by dropping coordinates where everything is missing on the edges
    obj = obj.dropna(dim=x_dim, how="all").dropna(dim=y_dim, how="all")

    # Second, find the optimal shrinkage to remove missing pixels on the edges
    # The shrinkage is found by removing pixels on edges on all sides until no missing pixels are left
    # TODO: This could be optimized to only check the edges where missing pixels are found
    if isinstance(obj, xr.DataArray):
        # For DataArray, we find the optimal shrinkage considering only x, y dims
        # by only looking at the first x,y slice
        extra_dims = set(obj.dims) - {x_dim, y_dim}
        n_shrink = _find_optimal_shrinkage_for_no_missing(
            obj.isel({dim: 0 for dim in extra_dims})
        )
    elif isinstance(obj, xr.Dataset):
        # For Dataset, we find the optimal shrinkage considering only x, y dims of the first raster
        # Variable in the dataset
        raster_vars = [
            v for v in obj.data_vars if all(d in obj[v].dims for d in [x_dim, y_dim])
        ]
        da = obj[raster_vars[0]]
        extra_dims = set(da.dims) - {x_dim, y_dim}
        n_shrink = _find_optimal_shrinkage_for_no_missing(
            da.isel({dim: 0 for dim in extra_dims})
        )
    else:
        raise ValueError("obj must be an xarray.DataArray or xarray.Dataset")
    return obj.isel(
        **{x_dim: slice(n_shrink, -n_shrink), y_dim: slice(n_shrink, -n_shrink)}
    )


def _get_raster_mask(
    obj,
    mask,
    /,
    *,
    all_touched=False,
    drop=False,
    invert=False,
    pad=True,
    pad_width=0.001,
):  # pragma: no cover covered_in_public_method
    """
    Get mask of raster-like part of xarray.Dataset or xarray.DataArray.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object with raster-like part to get mask for.
    mask : geopandas.GeoDataFrame, geopandas.GeoSeries
        Geometric features to clip out of object.
    all_touched : bool, optional
        If True, all cells touched by the mask is included. Otherwise,
        only the cells with the center point inside the mask or cells included
        by "Bresenhams line algorithm" will be included. False by default.
    drop : bool, optional
        If True, coordinates with all missing values will be dropped. False by default.
    invert : bool, optional
        If True, instead of keeping cells inside the mask, the cells outside will be kept.
        False by default.
    pad : bool, optional
        If True, the mask will be bufferred  by "pad_width" size before masking the array.
        This can help e.g. to ensure that raster points on the edge of the mask is included.
    pad_width : float, optional
        Width used to pad/buffer the mask in units of raster pixel/cell widths. So a
        pad_width of 1 will mean that the mask is buffered by the size of the raster pixel/cell.

    Returns
    -------
    xarray.Dataset, xarray.DataArray: clipped_obj
        Object clipped by geometric features.

    Notes
    -----
    When the mask edges intersects with the cell centers they are not guaranteed to be
    included. It is recommend to use a buffer or all_touched=True to be sure.

    """
    from .spatial import BBox

    gpd = _import_optional_dependency("geopandas")

    obj = obj.copy()
    crs_obj = get_crs(obj)

    # windkit.spatial.bbox.BBox objects are converted to gpd.GeoSeries
    # where the LinearRing is converted to Polygon
    if isinstance(mask, (BBox)):
        poly = shapely.geometry.Polygon(mask.ring.coords)
        mask = gpd.GeoSeries(poly, crs=mask.crs)

    if isinstance(mask, (shapely.geometry.Polygon)):
        mask = gpd.GeoSeries(mask, crs=crs_obj)

    # If mask is tuple or list we assume bounds (minx, miny, maxx, maxy)
    # With same CRS as obj
    if isinstance(mask, (tuple, list)):
        if len(mask) != 4:
            raise ValueError(
                "Got tuple/list of size {len(mask)}. "
                + "Bounds (minx, miny, maxx, maxy)"
                + " should be size 4!"
            )
        minx, miny, maxx, maxy = mask
        poly = shapely.geometry.Polygon(
            ((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy))
        )
        mask = gpd.GeoSeries(poly, crs=crs_obj)

    # Ensure mask is gpd.GeoSeries or gpd.GeoDataFrame
    if not isinstance(mask, (gpd.GeoDataFrame, gpd.GeoSeries)):
        raise ValueError(
            f"mask type {type(mask)} not supported!"
            + " must be tuple of bounds (minx, miny, maxx, maxy), "
            + " windkit.BBox, geopandas.GeoDataFrame, "
            + " geopandas.GeoSeries or shapely.geometry.Polygon"
        )

    x_dim, y_dim = _xy_dims()
    nx, ny = _shape(obj)
    transform_ = _transform(obj)
    crs_mask = pyproj.CRS.from_user_input(mask.crs)

    if not crs_obj.equals(crs_mask):
        raise ValueError(
            "Raster CRS and mask CRS are not identical!" + " please reproject first!"
        )

    if pad:
        res_x, res_y = _resolution(obj)
        mask = mask.buffer(pad_width * res_x, cap_style=3)

    features = mask.__geo_interface__["features"]
    geometries = list(f["geometry"] for f in features)

    mask_arr = rio.features.geometry_mask(
        geometries=geometries,
        out_shape=(ny, nx),
        transform=transform_,
        invert=not invert,
        all_touched=all_touched,
    )

    mask_xray = xr.DataArray(
        mask_arr,
        coords={x_dim: obj.coords[x_dim], y_dim: obj.coords[y_dim]},
        dims=(y_dim, x_dim),
    )

    return mask_xray


def _mask_raster(
    obj,
    mask,
    /,
    *,
    all_touched=False,
    drop=False,
    invert=False,
    nodata=None,
    pad=True,
    pad_width=0.001,
):  # pragma: no cover covered_in_public_method
    """
    Mask WindKit xarray raster-like object based on
    geometric features. Data outside the features are masked out.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object with raster-like dimensions to clip with mask.
    mask : geopandas.GeoDataFrame, geopandas.GeoSeries
        Geometric features to clip out of object.
    all_touched : bool, optional
        If True, all cells touched by the mask is included. Otherwise,
        only the cells with the center point inside the mask or cells included
        by "Bresenhams line algorithm" will be included. False by default.
    drop : bool, optional
        If True, coordinates with all missing values will be dropped. False by default.
    invert : bool, optional
        If True, instead of keeping cells inside the mask, the cells outside will be kept.
        False by default.
    nodata : int, float, optional
        Value to use for missing data. nan by default.
    pad : bool, optional
        If True, the mask will be bufferred  by "pad_width" size before masking the array.
        This can help e.g. to ensure that raster points on the edge of the mask is included.
    pad_width : float, optional
        Width used to pad/buffer the mask in units of raster pixel/cell widths. So a
        pad_width of 1 will mean that the mask is buffered by the size of the raster pixel/cell.

    Returns
    -------
    xarray.Dataset, xarray.DataArray: clipped_obj
        Object clipped by geometric features.

    Notes
    -----
    When the mask edges intersects with the cell centers they are not guaranteed to be
    included. It is recommend to use a buffer or all_touched=True to be sure.

    """
    mask_xray = _get_raster_mask(
        obj,
        mask,
        all_touched=all_touched,
        drop=drop,
        invert=invert,
        pad=pad,
        pad_width=pad_width,
    )

    cropped_obj = obj.where(mask_xray, drop=drop)

    if nodata is not None:
        cropped_obj = cropped_obj.fillna(nodata)

    if isinstance(cropped_obj, xr.Dataset):
        cropped_obj = _update_history(cropped_obj)
    return cropped_obj


def _clip_to_bbox_raster(obj, bbox):  # pragma: no cover covered_in_public_method
    """
    Clip WindKit xarray raster-like object to
    the bounds of a bounding box or geometry.

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        Object with raster-like dimensions to clip with bounding box.
    bbox : tuple, BBox, geopandas.GeoDataFrame, geopandas.GeoSeries, LinearRing
        Geometric features or bounding box to clip out of object.
        If bbox is a geometric feature, it's bounds method is used
        to obtain the bounding box bounds.

    Returns
    -------
    xarray.Dataset, xarray.DataArray: clipped_obj
        Object clipped by geometric features.

    """
    from .spatial import BBox

    obj = obj.copy()

    x_dim, y_dim = _xy_dims()

    crs_raster = get_crs(obj)

    if (
        isinstance(bbox, (BBox))
        or isinstance(bbox, gpd.GeoDataFrame)
        or isinstance(bbox, gpd.GeoSeries)
    ):
        crs_mask = pyproj.CRS.from_user_input(bbox.crs)
        if not crs_raster.equals(crs_mask):
            raise ValueError(
                "Raster CRS and mask CRS are not identical!"
                + " please reproject first!"
            )
        if isinstance(bbox, BBox):
            bounds = bbox.bounds()
        elif isinstance(bbox, gpd.GeoDataFrame) or isinstance(bbox, gpd.GeoSeries):
            bounds = bbox.total_bounds
    elif isinstance(bbox, shapely.geometry.LinearRing):
        bounds = bbox.bounds
    elif len(bbox) == 4:
        bounds = bbox
    else:
        raise ValueError(
            f"bbox type {type(bbox)} not supported!"
            + " must be tuple of bounds (minx, miny, maxx, maxy), "
            + " windkit.BBox, geopandas.GeoDataFrame, "
            + " geopandas.GeoSeries or shapely.geometry.LinearRing!"
        )

    minx, miny, maxx, maxy = bounds

    res_x, res_y = _resolution(obj)

    clip_minx = minx  # - abs(res_x) / 2.0
    clip_miny = miny  # - abs(res_y) / 2.0
    clip_maxx = maxx  # + abs(res_x) / 2.0
    clip_maxy = maxy  # + abs(res_y) / 2.0

    if res_x < 0:
        x_slice = slice(clip_maxx, clip_minx)
    else:
        x_slice = slice(clip_minx, clip_maxx)

    if res_y < 0:
        y_slice = slice(clip_maxy, clip_miny)
    else:
        y_slice = slice(clip_miny, clip_maxy)

    select = {y_dim: y_slice, x_dim: x_slice}

    obj_new = obj.sel(indexers=select)
    if isinstance(obj, xr.Dataset):
        obj_new = _update_history(obj_new)
    return obj_new


def _can_be_raster(west_east, south_north, thresh=1e-9):
    """Test if an array of coordinate values could
    possibly be converted into a raster

    Parameters
    ----------
    west_east : (N,) array_like
        A 1-D array containing west_east coordinates
    south_north : (N,) array_like
        A 1-D array containing south_north coordinates
    thresh : float
        Threshold value for checking spatial separation between coordinates
        Default set to 1e-9 m

    Returns
    -------
    bool
        True if it is a raster or can be converted to one. False otherwise.

    Notes
    -----
    Check that the south_north and west_east dimensions are such that
    the data could be converted into a raster object rather than a
    point object.
    """

    # We should only be looking at unique values of the coordinates
    we = np.sort(np.unique(west_east))
    sn = np.sort(np.unique(south_north))

    # More than one point
    if we.size == 1 or sn.size == 1:
        logging.debug("FAIL: One of the dimensions contains only 1 value.")
        return False

    # Difference between each point is approximately equal
    diff_we = np.diff(we)
    diff_we = np.where(diff_we <= thresh, diff_we.max(), diff_we)
    diff_sn = np.diff(sn)
    diff_sn = np.where(diff_sn <= thresh, diff_sn.max(), diff_sn)

    space_equal = ((diff_we.max() - diff_we.min()) <= thresh) and (
        (diff_sn.max() - diff_sn.min()) <= thresh
    )

    if not space_equal:
        logging.debug(
            "FAIL: Distance between points is not " + "the same for all points."
        )
        return False

    # Pixel is square
    is_square = abs(diff_sn.max() - diff_we.max()) <= thresh
    if not is_square:
        logging.debug("FAIL: Pixels are not square.")
        return False

    # logging.info("Done checking if dataset could be a raster.")
    return True


def _has_raster_dims(west_east, south_north):
    """Test if an array of coordinate values can be a raster and do not
    have duplicates.
    """
    if (west_east.size != np.unique(west_east).size) or (
        south_north.size != np.unique(south_north).size
    ):
        return False
    else:
        return _can_be_raster(west_east, south_north)


def to_raster(obj, ignore_raster_check=False):
    """Converts a point based object to a raster based object

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        WindKit xarray dataset or dataarray containing spatial
        dimensions and CRS variable
    ignore_raster_check : bool
        Check if the object satisfy the requirements to become a raster
        Default set to False (i.e., not to check)

    Returns
    -------
    xarray.Dataset, xarray.DataArray
        Raster version of WindKit xarray dataset or dataarray

    Raises
    ------
    ValueError
        If dataset cannot be converted to raster
    """
    x_dim, y_dim = _xy_dims()
    point_dim = _point_dim()
    stacked_point_dim = _stacked_point_dim()
    vertical_dim = _vertical_dim()

    # If object is already raster-like, return early.
    if (is_raster(obj) or is_cuboid(obj)) and _can_be_raster(obj[x_dim], obj[y_dim]):
        return obj

    # Only structures that need conversion
    if _can_be_raster(obj[x_dim], obj[y_dim]) or ignore_raster_check:
        stack_dims = (y_dim, x_dim)

        if is_stacked_point(obj):
            if isinstance(obj, xr.Dataset):
                if all(var in obj.data_vars for var in stack_dims):
                    out_obj = obj.copy().set_index(**{stacked_point_dim: stack_dims})

            if all(coord in obj.coords for coord in stack_dims):
                out_obj = obj.copy().set_index(**{stacked_point_dim: stack_dims})

            out_obj = out_obj.unstack(stacked_point_dim)

        elif is_point(obj):
            hgt_dim = (vertical_dim,) if has_height_coord(obj) else ()
            stack_dims = hgt_dim + stack_dims
            if isinstance(obj, xr.Dataset):
                if all(dim in obj.data_vars for dim in stack_dims):
                    out_obj = obj.copy().set_index(**{point_dim: stack_dims})

            if all(coord in obj.coords for coord in stack_dims):
                out_obj = obj.copy().set_index(**{point_dim: stack_dims})

            out_obj = out_obj.unstack(point_dim)

            # Correct 2d variables if necessary
            if len(hgt_dim) == 1:
                if isinstance(out_obj, xr.Dataset):
                    for var in out_obj.data_vars:
                        if "_pwio_data_is_2d" in out_obj[var].attrs:
                            if out_obj[var].attrs["_pwio_data_is_2d"]:
                                out_obj[var] = out_obj[var].isel(
                                    **{hgt_dim[0]: 0}, drop=True
                                )
                            del out_obj[var].attrs["_pwio_data_is_2d"]

                elif isinstance(out_obj, xr.DataArray):
                    if "_pwio_data_is_2d" in out_obj.attrs:
                        if out_obj.attrs["_pwio_data_is_2d"]:
                            out_obj = out_obj.isel(**{hgt_dim[0]: 0}, drop=True)
                        del out_obj.attrs["_pwio_data_is_2d"]

        # Add spatial metadata back to object
        for coord in stack_dims:
            out_obj[coord].attrs = obj[coord].attrs

        out_obj = _update_var_attrs(out_obj, _MAP_TYPE_ATTRS)
        if isinstance(out_obj, xr.Dataset):
            out_obj = _update_history(out_obj)

        return out_obj

    raise ValueError(f"Cannot convert {type(obj)} to raster.")
