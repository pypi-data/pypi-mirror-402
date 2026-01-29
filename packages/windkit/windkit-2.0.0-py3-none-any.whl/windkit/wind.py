# (c) 2022 DTU Wind Energy
"""
Utility functions for working with wind data
"""

__all__ = [
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
]

import numbers
import numpy as np
import pandas as pd
import xarray as xr
from scipy.integrate import trapezoid

from windkit.xarray_structures.sector import create_sector_coords
from windkit.spatial import get_spatial_struct, to_point, to_stacked_point, to_cuboid


def wind_speed(u, v):
    """
    Calculate wind speed from wind vectors.

    Parameters
    ----------
    u, v : numpy.ndarray, xarray.DataArray
        U and V wind vectors.

    Returns
    -------
    ws : numpy.ndarray, xarray.DataArray
        Wind speed.

    """
    return np.sqrt(u * u + v * v)


def wind_direction(u, v):
    """
    Calculate wind directions from wind vectors.

    Parameters
    ----------
    u, v : np.ndarray, xr.DataArray
        U and V wind vectors.

    Returns
    -------
    wd : np.ndarray, xr.DataArray
        Wind direction

    """
    return 180.0 + np.arctan2(u, v) * 180.0 / np.pi


def wind_speed_and_direction(u, v):
    """
    Calculate wind speed and wind direction from wind vectors.

    Parameters
    ----------
    u, v : numpy.ndarray, xarray.DataArray
        U and V wind vectors.

    Returns
    -------
    speed : numpy.ndarray, xarray.DataArray
        Wind speed.
    direction : numpy.ndarray, xarray.DataArray
        Wind direction.

    """
    return wind_speed(u, v), wind_direction(u, v)


def wind_vectors(ws, wd):
    """
    Calculate wind vectors u,v from the speed and direction.

    Parameters
    ----------
    speed : numpy.ndarray, xarray.DataArray
        Wind speed
    direction : numpy.ndarray, xarray.DataArray
        Wind direction

    Returns
    -------
    u, v : numpy.ndarray, xarray.DataArray
        Wind vectors u and v

    """
    return (
        -np.abs(ws) * np.sin(np.pi / 180.0 * wd),
        -np.abs(ws) * np.cos(np.pi / 180.0 * wd),
    )


def wind_direction_difference(wd_obs, wd_mod):
    """
    Calculate the circular (minimum) distance between
    two directions (observed and modelled).

    Parameters
    ----------
    wd_obs : xarray.DataArray
        observed direction arrays.
    wd_mod: xarray.DataArray
        modelled direction arrays.

    Returns
    -------
    xarray.DataArray: circular (minimum) differences.

    Examples
    --------
    >>> wd_obs = xr.DataArray([15.0, 345.0, 355.0], dims=('time',))
    >>> wd_mod = xr.DataArray([345.0, 300.0, 5.0], dims=('time',))
    >>> wind_direction_difference(wd_obs, wd_mod)
    <xarray.DataArray (time: 3)>
    array([-30., -45.,  10.])
    Dimensions without coordinates: time

    """
    wd_diff = wd_mod - wd_obs
    wd_diff = wd_diff.where(wd_diff < 180.0, wd_diff - 360.0)
    wd_diff = wd_diff.where(wd_diff > -180.0, wd_diff + 360.0)
    return wd_diff


def wd_to_sector(wd, sectors=12, output_type="centers", quantiles=False):
    """
    Convert wind directions to 0-based sector indices.

    Parameters
    ----------
    wd : xarray.DataArray, numpy.array
        Wind directions. The function uses xarray.apply_ufunc, so the return value
        will keep the shape of the input value.
    sectors : int
        Number of sectors. Defaults to 12.
    output_type : str
        If set to 'centers' the values in 'wd' are the sector centers. If set to
        'indices', the values in 'wd' are the sector indices. Defaults to 'centers'.
    quantiles : bool
        Allows to use equal probability sectors (quantiles=True) instead of fixed
        width sectors. Note that this is an experimental feature to be used only
        together with the :py:mod:`windkit.ltc` module for now. Other :py:mod:`windkit` modules may
        not be compatible with non fixed width sectors. Defaults to False.
    Returns
    -------
    sector_centers :  xarray.DataArray,np.array
        wind speed sector centers.
    sector_coords : xarray.DataArray
        data array with sector coordinates incling center, ceiling and floor.

    Examples
    --------
    >>> wd = xr.DataArray([355.0, 14.0, 25.0, 270.0,], dims=('time',))
    >>> wd_to_sector(wd)
    (<xarray.DataArray (time: 4)>
    array([  0.,   0.,  30., 270.])
    Dimensions without coordinates: time,
    <xarray.DataArray (sector: 12)>
    array([  0.,  30.,  60.,  90., 120., 150., 180., 210., 240., 270., 300.,
        330.])
    Coordinates:
      * sector        (sector) float64 0.0 30.0 60.0 90.0 ... 270.0 300.0 330.0
        sector_ceil   (sector) float64 15.0 45.0 75.0 105.0 ... 285.0 315.0 345.0
        sector_floor  (sector) float64 345.0 15.0 45.0 75.0 ... 255.0 285.0 315.0)
    """

    def _wd_to_sector_constant(wd, n_sectors=12):
        width = 360.0 / n_sectors
        edges = np.linspace(0.0, 360.0, n_sectors + 1)
        edges[0] = -0.1
        edges[-1] = 360.1
        sector = np.digitize(np.mod(wd + width / 2.0, 360.0), edges) - 1
        sector = sector.astype(np.float64)
        sector[sector >= n_sectors] = np.nan
        return sector

    def _wd_to_sector_quantiles(wd, n_sectors=12):
        # TODO move this to xarray nor numpy so we can use apply_ufunc
        sector_da = wd.copy()
        sector_cat, edges = pd.qcut(wd.values.flatten(), n_sectors, retbins=True)
        edges[0] = 0.0
        edges[-1] = 360.0
        sector_da.data = sector_cat.codes.reshape(wd.shape)
        sector_coords_da = create_sector_coords(edges)
        return sector_da, sector_coords_da

    if output_type not in ["centers", "indices"]:
        raise ValueError("unkown output type. Possible values are 'centers','indices'")

    if not quantiles:
        sector_indices = xr.apply_ufunc(
            _wd_to_sector_constant, wd, kwargs={"n_sectors": sectors}
        )
        sector_coords = create_sector_coords(sectors)
        sector_centers = sector_indices * 360.0 / sectors

    else:
        if (
            type(wd) is not xr.DataArray
            or ("point" not in wd.dims)
            or (len(wd["point"]) > 1)
        ):
            raise ValueError(
                "For quantiles=True, only xarray.DataArray with point dimensions of length 1 are supported"
            )
        sector_indices, sector_coords = _wd_to_sector_quantiles(wd, sectors)
        centers_values = sector_coords.isel(
            sector=sector_indices.values.flatten()
        ).values
        sector_centers = wd.copy()
        sector_centers.values = centers_values.reshape(-1, 1)

    if output_type == "indices":
        return sector_indices, sector_coords
    else:
        return sector_centers, sector_coords


def vinterp_wind_direction(wind_direction, height, **kwargs):
    """
    Interpolate wind direction to a given height.

    Parameters
    ----------
    wind_direction : xarray.DataArray
        Wind direction.
    height : float
        Height to interpolate wind direction to.
    **kwargs : dict, optional
        Additional keyword arguments passed to xarray.interp.

    Returns
    -------
    wind_direction : xarray.DataArray
        Interpolated wind direction.

    """
    if not isinstance(wind_direction, xr.DataArray):
        raise TypeError("wind_direction must be a xarray.DataArray")

    if "height" not in wind_direction.dims:
        raise ValueError("wind_direction must have a height dimension")

    if not isinstance(height, (np.ScalarType, xr.DataArray)):
        raise TypeError("height must be a scalar or xarray.DataArray")

    wd_ref = wind_direction.isel(height=0)
    wd_diff = wind_direction_difference(wind_direction, wd_ref)
    wd_new = wd_ref - wd_diff.interp(height=height, **kwargs)
    return np.mod(wd_new, 360.0)


def vinterp_wind_speed(wind_speed, height, log_height=True, **kwargs):
    """
    Vertically interpolate wind speed to a given height from other height levels.

    Parameters
    ----------
    wind_speed : xarray.DataArray
        Wind speed. Must have a height dimension.
    height : float, xarray.DataArray
        Height to interpolate wind speed to.
    log_height : bool, optional
        If True, interpolate in log-height space. Defaults to True.
    **kwargs : dict, optional
        Additional keyword arguments passed to xarray.interp.

    Returns
    -------
    wind_speed : xarray.DataArray
        Interpolated wind speed.

    """

    if not isinstance(wind_speed, xr.DataArray):
        raise TypeError("wind_speed must be a xarray.DataArray")

    if "height" not in wind_speed.dims:
        raise ValueError("wind_speed must have a height dimension")

    if not isinstance(height, (np.ScalarType, xr.DataArray)):
        raise TypeError("height must be a scalar or xarray.DataArray")

    wind_speed = wind_speed.copy()

    if log_height:
        wind_speed = wind_speed.assign_coords(height=np.log1p(wind_speed.height))
        if isinstance(height, xr.DataArray):
            height_ = height.copy()
        height = np.log1p(height)

    wind_speed = wind_speed.interp(height=height, **kwargs)

    if log_height and isinstance(height_, xr.DataArray):
        wind_speed = wind_speed.assign_coords(height=height_)

    return wind_speed


def rotor_equivalent_wind_speed(
    wind_speed,
    wind_direction,
    hub_height,
    rotor_diameter,
    delta_z=1.0,
    n_integrate=1001,
):
    """
    Calculate the rotor equivalent wind speed (REWS) from given wind speed and directions
    on height levels.

    The procedure is as follows:
        1. Find the area of each segment of the rotor spanned area.
        2. Calculate the wind speed at the center of each segment by linearly interpolating
           the wind speed to the height of the segment center in log-height.
        3. Calculate the wind direction at the center of each segment by linearly interpolating
           the wind direction to the height of the segment center. Circularity is
           taken into account here.
        4. Calculate the wind direction at hub height by linearly interpolating the wind
           direction to the hub height.
        5. Calculate the REWS as the cube root of the sum of the wind speed at each segment
           center multiplied by the area-weight (area/total) of the segment and the cosine
           of the difference between the wind direction at the segment center and the wind
           direction at hub height.

    Parameters
    ----------
    wind_speed : xarray.DataArray
        Wind speed on height levels.
    wind_direction : xarray.DataArray
        Wind direction on height levels.
    hub_height : float
        Turbine Hub height.
    rotor_diameter : float
        Turbine rotor diameter.
    delta_z : float, optional
        Height difference between segments of turbine spanned rotor area
        (default: 1.0).
    n_integrate : int, optional
        Number of points to use for integration (default: 1001) of the area
        of each segment.

    Returns
    -------
    rews : xarray.DataArray
        Rotor equivalent wind speed.

    """

    if not isinstance(wind_speed, xr.DataArray):
        raise TypeError("wind_speed must be a xarray.DataArray")

    if not isinstance(wind_direction, xr.DataArray):
        raise TypeError("wind_direction must be a xarray.DataArray")

    if "height" not in wind_speed.dims:
        raise ValueError("wind_speed must have a height dimension")

    if "height" not in wind_direction.dims:
        raise ValueError("wind_direction must have a height dimension")

    hub_height = float(hub_height)
    rotor_diameter = float(rotor_diameter)
    delta_z = float(delta_z)
    n_integrate = int(n_integrate)

    rotor_radius = rotor_diameter / 2.0

    zi = np.linspace(
        hub_height - rotor_radius,
        hub_height + rotor_radius,
        int(np.round(rotor_diameter / delta_z)) + 1,
    )
    zc = (zi[1:] + zi[:-1]) / 2
    zc = xr.DataArray(zc, dims=("height",), coords={"height": zc})

    Ai = np.zeros_like(zc)

    for i in range(len(zi) - 1):
        zs = np.linspace(zi[i], zi[i + 1], n_integrate)
        Ai[i] = trapezoid(2 * np.sqrt(rotor_radius**2 - (zs - hub_height) ** 2), zs)

    # Area of rotor
    A = np.pi * rotor_radius**2

    # Area of rotor segment
    Ai = xr.DataArray(Ai, dims=("height",), coords={"height": zc})

    # wind speed and direction at segment center
    ui = vinterp_wind_speed(
        wind_speed, zc, method="linear", kwargs={"fill_value": "extrapolate"}
    )
    di = vinterp_wind_direction(
        wind_direction, zc, method="linear", kwargs={"fill_value": "extrapolate"}
    )

    # wind direction at hub height
    dh = vinterp_wind_direction(
        wind_direction,
        hub_height,
        method="linear",
        kwargs={"fill_value": "extrapolate"},
    )

    rews = ((1 / A) * Ai * (ui**3) * np.cos(np.deg2rad(di - dh))).sum(dim="height")

    rews = xr.where(rews < 0, 0, rews)

    rews = np.power(rews, 1.0 / 3.0)

    rews = rews.expand_dims(height=[hub_height])

    return rews


def tswc_resample(
    ds,
    freq,
    var_ws="wind_speed",
    var_wd="wind_direction",
    min_availability=0.5,
    **kwargs,
):
    """Resample wind speed and direction to a given frequency.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset with wind speed and direction.
    freq : str
        Resampling frequency.
    var_ws : str, optional
        Name of wind speed variable, by default "wind_speed".
    var_wd : str, optional
        Name of wind direction variable, by default "wind_direction".

    Returns
    -------
    xarray.Dataset
        Resampled dataset.

    """
    ds = ds.copy()

    def nan_mean(da):
        return da.mean(dim="time").where(
            da.notnull().sum(dim="time") >= len(da.time) * min_availability
        )

    ds["__U__"], ds["__V__"] = wind_vectors(ds[var_ws], ds[var_wd])
    ds = ds.drop_vars([var_ws, var_wd])
    ds = ds.resample(time=freq, **kwargs).map(nan_mean)

    ds[var_ws], ds[var_wd] = wind_speed_and_direction(ds["__U__"], ds["__V__"])
    ds = ds.drop_vars(["__U__", "__V__"])
    return ds


def shear_extrapolate(wind_speed, height, shear_exponent=0.143, coord_height="height"):
    r"""Shear extrapolate wind speeds to new heights using the power law.

    Notes
    -----

    Power-law shear extrapolation:

    .. math::

        u_2 &= u_1 * (h_2/h_1)^{\alpha}

    where:

    .. math::
        h_1 &= \mathrm{ known\, height}

        h_2 &= \mathrm{ new\, height}

        u_1 &= \mathrm{ wind\, speed\, at\, height\,} h_1

        u_2 &= \mathrm{ wind\, speed\, at\, height\,} h_2

        \alpha &= \mathrm{ shear\, exponent}

    Parameters
    ----------
    wind_speed : xarray.DataArray
        Wind speed DataArray with wind speeds at known heights. A height coordinate
        must be present. If the height coordinate is also a dimension with more than one
        known height, the nearest height to each target height will be used.
        If wind speeds are at unstructured heights (i.e., height is a coordinate but not a dimension),
        only one target height can be used, or varying heights that match the dimensions of wind_speed.
    height : number, collection of numbers, or xarray.DataArray
        New heights to which wind speeds will be extrapolated.
    shear_exponent : number, xarray.DataArray, optional
        Shear exponent for the power law, by default 0.143.
        A DataArray can be provided to have varying shear exponents over other dimensions (e.g., time).
        If the shear exponent also varies with height, the height nearest to the target height
        will be used.
    coord_height : str, optional
        Name of the height coordinate in wind_speeds and new_heights, by default "height".

    Returns
    -------
    xarray.Dataset
        New time-series wind climate dataset with wind speeds at the specified heights.

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> import xarray as xr
    >>> import windkit as wk
    >>> wind_speed = xr.DataArray(
            np.array([[10.0, 12.0, 14.0], [10.5, 12.5, 14.5], [11.0, 13.0, 15.0]]).T,
            dims=["time", "height"],
            coords={
                "time": pd.date_range("2023-01-01", periods=3, freq="h"),
                "height": [10.0, 30.0, 40.0],
            },
        )
    >>> wind_speed_new = wk.shear_extrapolate(wind_speed, 100, shear_exponent=0.143)
    >>> print(wind_speed_new)
    <xarray.DataArray (time: 3, height: 1)> Size: 24B
    array([[12.54001646],
           [14.82001945],
           [17.10002244]])
    Coordinates:
    * time     (time) datetime64[ns] 24B 2023-01-01 ... 2023-01-01T02:00:00
    * height   (height) int64 8B 100
    """

    if not isinstance(wind_speed, xr.DataArray):
        raise ValueError("wind_speeds must be an xarray.DataArray.")

    dim_height = wind_speed.coords[coord_height].dims[0]
    height_is_dim = (
        coord_height in wind_speed.coords and coord_height in wind_speed.dims
    )

    if not height_is_dim:
        if isinstance(height, numbers.Number):
            height = (
                wind_speed[coord_height]
                .assign_coords(
                    **{
                        coord_height: (
                            wind_speed[coord_height].dims,
                            wind_speed[coord_height].values * 0 + height,
                        )
                    }
                )
                .copy(data=wind_speed[coord_height].values * 0 + height)
            )

        elif isinstance(height, (list, tuple, np.ndarray)):
            height = np.atleast_1d(height)
            if height.ndim > 1:
                raise ValueError("height cannot be multi-dimensional.")
            if height.size > 1:
                if dim_height in wind_speed.dims:
                    raise ValueError(
                        f"Multiple target heights are only supported when {coord_height} is a dimension in wind_speed."
                    )
            height = xr.DataArray(
                height,
                dims=(coord_height,),
                coords={coord_height: height},
            )
        elif isinstance(height, xr.DataArray):
            if not all(c in wind_speed.coords for c in height.coords):
                raise ValueError(
                    "When height is a DataArray, all its coordinates must be present in wind_speed."
                )
    else:
        if isinstance(height, (numbers.Number, list, tuple, np.ndarray)):
            height = np.atleast_1d(height)
            if height.ndim > 1:
                raise ValueError("height cannot be multi-dimensional.")
            height = xr.DataArray(
                height,
                dims=(coord_height,),
                coords={coord_height: height},
            )

    if isinstance(shear_exponent, numbers.Number):
        shear_exponent = xr.DataArray(shear_exponent)

    if wind_speed[coord_height].ndim > 1:
        raise ValueError(f"Dimension: {coord_height} cannot be multi-dimensional.")

    if not isinstance(coord_height, str):
        raise ValueError("coord_height must be a string.")

    if coord_height not in wind_speed.coords:
        raise ValueError(f"{coord_height} must be a coord in 'wind_speed'")

    if np.any(height <= 0):
        raise ValueError("All height must be positive values.")

    if np.any(wind_speed[coord_height] <= 0):
        raise ValueError("All wind_speed heights must be positive values.")

    def _extrapolate_1d(u1, h1, h2, alpha):
        """Shear extrapolate according to power law."""
        return u1 * (h2 / h1) ** alpha

    if coord_height in wind_speed.coords and wind_speed[coord_height].ndim == 0:
        wind_speed = wind_speed.expand_dims(coord_height)

    if coord_height in shear_exponent.coords and shear_exponent[coord_height].ndim == 0:
        shear_exponent = shear_exponent.expand_dims(coord_height)

    if coord_height in wind_speed.dims and wind_speed[coord_height].size > 1:
        wind_speed = wind_speed.sel(**{coord_height: height}, method="nearest")

    if coord_height in shear_exponent.dims and shear_exponent[coord_height].size > 1:
        shear_exponent = shear_exponent.sel(**{coord_height: height}, method="nearest")

    # if dim in wind_speed.dims:
    input_core_dims = []

    for da in [wind_speed, wind_speed[coord_height], height, shear_exponent]:
        if dim_height in da.dims and height_is_dim:
            input_core_dims.append([dim_height])
        else:
            input_core_dims.append([])

    if height_is_dim:
        output_core_dims = [[dim_height]]
        exclude_dims = set([dim_height])
    else:
        output_core_dims = [[]]
        exclude_dims = set()

    result = xr.apply_ufunc(
        _extrapolate_1d,
        wind_speed,
        wind_speed[coord_height],
        height,
        shear_exponent,
        input_core_dims=input_core_dims,
        output_core_dims=output_core_dims,
        exclude_dims=exclude_dims,
        dask="parallelized",
        keep_attrs=True,
        output_dtypes=[wind_speed.dtype],
    )
    # if dim in wind_speed.dims:
    result = result.assign_coords({coord_height: height})

    return result


def shear_exponent(da):
    """
    Compute the shear exponent from vertical wind speed profiles using finite
    differences in log-space.

    Parameters
    ----------
    da : xarray.DataArray
        Wind speed DataArray. The DataArray must contain
        a height coordinate and horizontal coordinates ('west_east', 'south_north')
        or be convertible to that structure. Wind speeds must be positive.

    Returns
    -------
    xarray.DataArray
        The shear exponent computed as (d ln u) / (d ln z) at log-space midpoints between input heights.
        The returned DataArray has the same spatial structure as the input
        and only contains the points where valid shear calculations could be made.

    Raises
    ------
    ValueError
        If the input cannot be converted to a point/vertical structure by
        windkit.spatial.to_point.

    Notes
    -----
    - The function sorts profiles by (west_east, south_north, height) and
      computes backward finite differences along the "point" axis.
    - Midpoint heights are computed in log-space and assigned to the output
      shear DataArray.

    Examples
    --------
    >>> shear = shear_exponent(da)
    """
    # get input structure
    struct_in = get_spatial_struct(da)

    # convert to point structure
    da = to_point(da)

    # sort by x,y,height so that we can calculate forward differences between all points
    da = da.sortby(["west_east", "south_north", "height"])

    ln_u = np.log(da).diff("point", label="lower")
    ln_z = (np.log(da["height"])).diff("point", label="lower")

    shear = ln_u / ln_z
    shear.name = "shear_exponent"

    # find all points that are belonging to the same vertical profile with same x,y
    same_xy = (da["west_east"].diff("point") == 0) & (
        da["south_north"].diff("point") == 0
    )
    shear = shear.where(same_xy)

    # calculate heights at mid-points in log space
    logz = np.log(da["height"])[:-1] + 0.5 * ln_z
    shear.coords["height"] = np.exp(logz)
    shear = shear.assign_coords(same_xy["point"].drop_vars("height").coords)

    # drop invalid height that results from non-matching vertical profiles
    shear = shear.where(same_xy.drop_vars("height"), drop=True)

    # convert back to original structure
    if struct_in == "stacked_point":
        shear = to_stacked_point(shear)
    elif struct_in == "raster" or struct_in == "cuboid":
        shear = to_cuboid(shear)

    return shear


def wind_veer(da):
    """
    Calculate wind veer (change in wind direction with height).

    Parameters
    ----------
    da : xarray.DataArray
        DataArray containing wind direction data. Must have coordinates for
        'west_east', 'south_north', and 'height'.

    Returns
    -------
    xarray.DataArray
        DataArray containing the wind veer values in degrees per meter.
        The structure matches the input structure (point, stacked_point,
        raster, or cuboid).
    """
    # get input structure
    struct_in = get_spatial_struct(da)

    # convert to point structure
    da = to_point(da)

    # sort by x,y,height so that we can calculate forward differences between all points
    da = da.sortby(["west_east", "south_north", "height"])

    wd_diff = da.diff("point", label="lower")
    # Adjust for circular nature of wind direction
    wd_diff = (wd_diff + 180) % 360 - 180
    z_diff = da["height"].diff("point", label="lower")

    veer = wd_diff / z_diff
    veer.name = "wind_veer"

    # find all points that are belonging to the same vertical profile with same x,y
    same_xy = (da["west_east"].diff("point") == 0) & (
        da["south_north"].diff("point") == 0
    )
    veer = veer.where(same_xy)

    # calculate heights at mid-points
    new_z = da["height"][:-1] + 0.5 * z_diff
    veer.coords["height"] = new_z
    veer = veer.assign_coords(same_xy["point"].drop_vars("height").coords)

    # drop invalid height that results from non-matching vertical profiles
    veer = veer.where(same_xy.drop_vars("height"), drop=True)

    # convert back to original structure
    if struct_in == "stacked_point":
        veer = to_stacked_point(veer)
    elif struct_in == "raster" or struct_in == "cuboid":
        veer = to_cuboid(veer)

    return veer


def veer_extrapolate(wind_direction, height, veer=0.0, coord_height="height"):
    r"""Extrapolate wind direction to new heights using linear veer.

    Notes
    -----

    Linear veer extrapolation:

    .. math::

        wd_2 &= (wd_1 + v \cdot (h_2 - h_1)) \pmod{360}

    where:

    .. math::
        h_1 &= \mathrm{ known\, height}

        h_2 &= \mathrm{ new\, height}

        wd_1 &= \mathrm{ wind\, direction\, at\, height\,} h_1

        wd_2 &= \mathrm{ wind\, direction\, at\, height\,} h_2

        v &= \mathrm{ wind\, veer\, (deg/m)}

    Parameters
    ----------
    wind_direction : xarray.DataArray
        Wind direction DataArray with wind directions at known heights. A height coordinate
        must be present. If the height coordinate is also a dimension with more than one
        known height, the nearest height to each target height will be used.
        If wind directions are at unstructured heights (i.e., height is a coordinate but not a dimension),
        only one target height can be used, or varying heights that match the dimensions of wind_direction.
    height : number, collection of numbers, or xarray.DataArray
        New heights to which wind directions will be extrapolated.
    veer : number, xarray.DataArray, optional
        Wind veer in degrees per meter, by default 0.0.
        A DataArray can be provided to have varying veer over other dimensions (e.g., time).
        If the veer also varies with height, the height nearest to the target height
        will be used.
    coord_height : str, optional
        Name of the height coordinate in wind_direction and new_heights, by default "height".

    Returns
    -------
    xarray.DataArray
        New time-series wind climate data array with wind directions at the specified heights.
    """

    if not isinstance(wind_direction, xr.DataArray):
        raise ValueError("wind_direction must be an xarray.DataArray.")

    dim_height = wind_direction.coords[coord_height].dims[0]
    height_is_dim = (
        coord_height in wind_direction.coords and coord_height in wind_direction.dims
    )

    if not height_is_dim:
        if isinstance(height, numbers.Number):
            height = (
                wind_direction[coord_height]
                .assign_coords(
                    **{
                        coord_height: (
                            wind_direction[coord_height].dims,
                            wind_direction[coord_height].values * 0 + height,
                        )
                    }
                )
                .copy(data=wind_direction[coord_height].values * 0 + height)
            )

        elif isinstance(height, (list, tuple, np.ndarray)):
            height = np.atleast_1d(height)
            if height.ndim > 1:
                raise ValueError("height cannot be multi-dimensional.")
            if height.size > 1:
                if dim_height in wind_direction.dims:
                    raise ValueError(
                        f"Multiple target heights are only supported when {coord_height} is a dimension in wind_direction."
                    )
            height = xr.DataArray(
                height,
                dims=(coord_height,),
                coords={coord_height: height},
            )
        elif isinstance(height, xr.DataArray):
            if not all(c in wind_direction.coords for c in height.coords):
                raise ValueError(
                    "When height is a DataArray, all its coordinates must be present in wind_direction."
                )
    else:
        if isinstance(height, (numbers.Number, list, tuple, np.ndarray)):
            height = np.atleast_1d(height)
            if height.ndim > 1:
                raise ValueError("height cannot be multi-dimensional.")
            height = xr.DataArray(
                height,
                dims=(coord_height,),
                coords={coord_height: height},
            )

    if isinstance(veer, numbers.Number):
        veer = xr.DataArray(veer)

    if wind_direction[coord_height].ndim > 1:
        raise ValueError(f"Dimension: {coord_height} cannot be multi-dimensional.")

    if not isinstance(coord_height, str):
        raise ValueError("coord_height must be a string.")

    if coord_height not in wind_direction.coords:
        raise ValueError(f"{coord_height} must be a coord in 'wind_direction'")

    if np.any(height <= 0):
        raise ValueError("All height must be positive values.")

    if np.any(wind_direction[coord_height] <= 0):
        raise ValueError("All wind_direction heights must be positive values.")

    def _extrapolate_1d(wd1, h1, h2, v):
        """Veer extrapolate linearly."""
        return np.mod(wd1 + v * (h2 - h1), 360.0)

    if coord_height in wind_direction.coords and wind_direction[coord_height].ndim == 0:
        wind_direction = wind_direction.expand_dims(coord_height)

    if coord_height in veer.coords and veer[coord_height].ndim == 0:
        veer = veer.expand_dims(coord_height)

    if coord_height in wind_direction.dims and wind_direction[coord_height].size > 1:
        wind_direction = wind_direction.sel(**{coord_height: height}, method="nearest")

    if coord_height in veer.dims and veer[coord_height].size > 1:
        veer = veer.sel(**{coord_height: height}, method="nearest")

    # if dim in wind_direction.dims:
    input_core_dims = []

    for da in [wind_direction, wind_direction[coord_height], height, veer]:
        if dim_height in da.dims and height_is_dim:
            input_core_dims.append([dim_height])
        else:
            input_core_dims.append([])

    if height_is_dim:
        output_core_dims = [[dim_height]]
        exclude_dims = set([dim_height])
    else:
        output_core_dims = [[]]
        exclude_dims = set()

    result = xr.apply_ufunc(
        _extrapolate_1d,
        wind_direction,
        wind_direction[coord_height],
        height,
        veer,
        input_core_dims=input_core_dims,
        output_core_dims=output_core_dims,
        exclude_dims=exclude_dims,
        dask="parallelized",
        keep_attrs=True,
        output_dtypes=[wind_direction.dtype],
    )
    # if dim in wind_direction.dims:
    result = result.assign_coords({coord_height: height})

    return result
