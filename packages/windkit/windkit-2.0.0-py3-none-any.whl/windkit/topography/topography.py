# (c) 2022 DTU Wind Energy
"""
Module to handle elevation maps.
"""

__all__ = [
    "read_elevation_map",
    "read_roughness_map",
    "read_landcover_map",
    "elevation_map_to_file",
    "roughness_map_to_file",
    "landcover_map_to_file",
    "create_wasp_site_effects",
    "landcover_to_roughness",
    "roughness_to_landcover",
]
from pathlib import Path

import geopandas as gpd
import numpy as np
import xarray as xr

import windkit.topography.raster_map as _raster_map
import windkit.topography.vector_map as _vector_map

from .._errors import UnsupportedFileTypeError
from ..xarray_structures.empty import _copy_chunks, _define_std_arrays, _empty_unstack
from ..xarray_structures.metadata import (
    _TOPO_EFFECTS_ATTRS,
    _update_history,
    _update_var_attrs,
)


def create_wasp_site_effects(
    output_locs,
    n_sectors=12,
    not_empty=True,
    site_effects="all",
    seed=9876538,
    **kwargs,
):
    """Create empty site-factors dataset.

    Parameters
    ----------
    output_locs : xarray.Dataset
        Output geospatial information
    n_sectors : int
        Number of sectors. Defaults to 12.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data.
    site_Factors : list of strings, or string
        List of variables to include in the output, or a string "all" that
        includes all variables. Defaults to ["z0meso", "displ"]
    seed : int
        Seed for the random data, defaults to 9876538.

    kwargs : dict
        Additional arguments.

    Returns
    -------
    ds : xarray.Dataset
        Empty site factors dataset.
    """
    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)

    _site_effects_vars_2d = ["site_elev", "rix"]
    _site_effects_vars_3d_nohgt = ["z0meso", "slfmeso", "displ", "dirrix"]
    _site_effects_vars_4d = [
        "user_def_speedups",
        "orographic_speedups",
        "obstacle_speedups",
        "roughness_speedups",
        "user_def_turnings",
        "orographic_turnings",
        "obstacle_turnings",
        "roughness_turnings",
    ]
    if site_effects == "all":
        site_effects = (
            _site_effects_vars_2d + _site_effects_vars_3d_nohgt + _site_effects_vars_4d
        )
    random_param_dict = {
        "z0meso": (0, 1.2),
        "slfmeso": (0, 1),
        "displ": (0, 10),
        "user_def_speedups": 1,
        "orographic_speedups": (0.6, 1.5),
        "obstacle_speedups": 1,
        "roughness_speedups": (0.6, 1.5),
        "user_def_turnings": 0,
        "orographic_turnings": (-20, 20),
        "obstacle_turnings": 0,
        "roughness_turnings": 0,
        "dirrix": (0, 0.5),
        "site_elev": (0, 100),
        "rix": (0, 0.5),
    }
    out_vars = {}
    for var in site_effects:
        if var in _site_effects_vars_2d:
            out_vars[var] = da_dict["da_2d"]
        elif var in _site_effects_vars_3d_nohgt:
            out_vars[var] = da_dict["da_3d_nohgt"]
        elif var in _site_effects_vars_4d:
            out_vars[var] = da_dict["da_4d"]
        else:
            raise ValueError(f"Unknown  {var}, cannot add to result")
    ds = xr.Dataset(
        out_vars,
        attrs=unstack_attrs,
    )

    if not_empty:
        rng = np.random.default_rng(seed)
        for val in site_effects:
            rand_param = random_param_dict[val]
            if isinstance(rand_param, tuple):
                ds[val].values = rng.uniform(*rand_param, ds[val].shape)
            else:
                ds[val].values = np.zeros(ds[val].shape)

    ustack_ds = _empty_unstack(ds, is_scalar)

    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _TOPO_EFFECTS_ATTRS)

    return _update_history(ds)


def _create_z0meso(output_locs, n_sectors=12, **kwargs):
    """Empty site_effects with only z0meso and slfmeso.

    Parameters
    ----------
    out_grid : xarray.Dataset
        Output geospatial information.
    n_sectors : int
        Number of sectors, defaults to 12.
    kwargs : dict
        Additional arguments.

    Returns
    -------
    ds : xarray.Dataset
        Empty dataset.
    """

    empty_z0 = create_wasp_site_effects(output_locs, n_sectors)[["z0meso", "slfmeso"]]

    return _update_history(empty_z0)


def _infer_spatial_format(filename):
    """Derive if file is vector or raster."""
    if not isinstance(filename, (str, Path)):
        raise TypeError(f"Filename must be a string or Path, not {type(filename)}.")

    filename = Path(filename)
    if filename.suffix[1:] in _raster_map.SUPPORTED_RASTER_FILE_FORMATS_READ:
        return "raster"
    elif filename.suffix[1:] in _vector_map.SUPPORTED_VECTOR_FILE_FORMATS_READ:
        return "vector"
    else:
        raise UnsupportedFileTypeError(
            f"Filetype {filename.suffix[1:]} not supported for reading."
        )


def _read_topo_map(
    filename, map_type="elevation", crs=None, spatial_format="infer", **kwargs
):
    """Reads file into an elevation map.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to file
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    **kwargs : dict
        Additonal keyword arguments passed to reader.
    Returns
    -------
    xarray.DataArray
        elevation_map object
    """
    kwargs = {**kwargs, **{"map_type": map_type}}

    if spatial_format == "infer":
        spatial_format = _infer_spatial_format(filename)
    elif spatial_format not in ["raster", "vector"]:
        raise ValueError(
            f"Invalid spatial format: {spatial_format}. Must be 'raster' or 'vector'."
        )

    if spatial_format == "raster":
        return _raster_map._read_raster_map(filename, crs=crs, **kwargs)
    elif spatial_format == "vector":
        return _vector_map._read_vector_map(filename, crs=crs, **kwargs)
    else:
        err_msg = f"Filetype {filename.suffix[1:]} not supported for reading."
        err_msg += " Supported filetypes are: Raster: "
        err_msg += ", ".join(_raster_map.SUPPORTED_RASTER_FILE_FORMATS_READ)
        err_msg += ", Vector: "
        err_msg += ", ".join(_vector_map.SUPPORTED_VECTOR_FILE_FORMATS_READ)
        raise UnsupportedFileTypeError(err_msg)


def read_elevation_map(filename, crs=None, **kwargs):
    """
    Read elevation map from file.

    The file can be either a raster file or a vector file.

    If the file is a raster file, the following formats are supported:
       "grd" and "tif" (geoTIFF).

    If the file is a vector file, the following formats are supported:
        "gpkg", "gml", "map", "tmp", "zip", "ZipExtFile"

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to file
    crs : int, dict, str or pyproj.crs.CRS, optional
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    **kwargs : dict
        Additonal keyword arguments passed to reader.

    Returns
    -------
    xarray.DataArray, gpd.GeoDataFrame
        elevation_map object

    """
    kwargs = {**kwargs, **{"map_type": "elevation"}}
    return _read_topo_map(filename, crs=crs, **kwargs)


def read_roughness_map(filename, crs=None, convert_to_landcover=False, **kwargs):
    """
    Read roughness map from file.

    The file can be either a raster file or a vector file.

    If the file is a raster file, the following formats are supported:
       "grd" and "tif" (geoTIFF).

    If the file is a vector file, the following formats are supported:
        "gpkg", "gml", "map", "tmp", "zip", "ZipExtFile"

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to file
    crs : int, dict, str or pyproj.crs.CRS, optional
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    convert_to_landcover : bool
        Whether to convert the roughness map to a landcover map. Default is False.
    polygons: bool
        Whether to convert the opened file to polygons, default True. If False,
        opens the file as old fashioned change lines. You can try this if your
        file is not being opened correctly, but you are responsible for checking
        it's correctness, because there is less error checking for these types
        of files.
    check_errors: bool
        Whether to check for errors in the map, default True.
    **kwargs : dict
        Additonal keyword arguments passed to reader.

    Returns
    -------
    xarray.DataArray, gpd.GeoDataFrame
        roughness_map object

    """
    kwargs = {
        **kwargs,
        **{"map_type": "roughness", "convert_to_landcover": convert_to_landcover},
    }
    return _read_topo_map(filename, crs=crs, **kwargs)


def read_landcover_map(filename, crs=None, return_lctable=False, **kwargs):
    """
    Read landcover map from file.

    The file can be either a raster file or a vector file.

    If the file is a raster file, the following formats are supported:
       "grd" and "tif" (geoTIFF).

    If the file is a vector file, the following formats are supported:
        "gpkg", "gml", "map", "tmp", "zip", "ZipExtFile"

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to file
    crs : int, dict, str or pyproj.crs.CRS, optional
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    return_lctable : bool
        Whether to return the landcover table. Default is False.
    polygons: bool
        Whether to convert the opened file to polygons, default True. If False,
        opens the file as old fashioned change lines. You can try this if your
        file is not being opened correctly, but you are responsible for checking
        it's correctness, because there is less error checking for these types of files.
    check_errors: bool
        Whether to check for errors in the map, default True.
    **kwargs : dict
        Additonal keyword arguments passed to reader.

    Returns
    -------
    xarray.DataArray, gpd.GeoDataFrame
        landcover_map object

    """
    kwargs = {**kwargs, **{"map_type": "landcover", "return_lctable": return_lctable}}
    return _read_topo_map(filename, crs=crs, **kwargs)


def _map_to_file(obj, filename, spatial_format="infer", **kwargs):
    """Write elevation map to file.

    Parameters
    ----------
    obj : xarray.DataArray or gpd.GeoDataFrame
        Map to write
    filename : str or pathlib.Path
        Path to file
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    **kwargs : dict
        Additonal keyword arguments passed to writer.
    """

    if spatial_format == "infer":
        spatial_format = _infer_spatial_format(filename)
    elif spatial_format not in ["raster", "vector"]:
        raise ValueError(
            f"Invalid spatial format: {spatial_format}. Must be 'raster' or 'vector'."
        )

    if spatial_format == "raster":
        return _raster_map._raster_map_to_file(obj, filename, **kwargs)
    elif spatial_format == "vector":
        return _vector_map._vector_map_to_file(obj, filename, **kwargs)
    else:
        err_msg = f"Filetype {filename.suffix[1:]} not supported for writing."
        err_msg += " Supported filetypes are: Raster: "
        err_msg += ", ".join(_raster_map.SUPPORTED_RASTER_FILE_FORMATS_WRITE)
        err_msg += ", Vector: "
        err_msg += ", ".join(_vector_map.SUPPORTED_VECTOR_FILE_FORMATS_WRITE)
        raise UnsupportedFileTypeError(err_msg)


def elevation_map_to_file(elevation_map, filename, **kwargs):
    """
    Write elevation map to file.

    The file can be either a raster file or a vector file.

    If the file is a raster file, the following formats are supported:
       "grd" and "tif" (geoTIFF).

    If the file is a vector file, the following formats are supported:
        "gpkg", "gml", "map", "tmp", "zip", "ZipExtFile"

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to file
    elevation_map : xarray.DataArray
        Elevation map
    crs : int, dict, str or pyproj.crs.CRS, optional
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    **kwargs : dict
        Additonal keyword arguments passed to writer.
    """
    return _map_to_file(elevation_map, filename, **kwargs)


def roughness_map_to_file(roughness_map, filename, **kwargs):
    """
    Write roughness map to file.

    The file can be either a raster file or a vector file.

    If the file is a raster file, the following formats are supported:
       "grd" and "tif" (geoTIFF).

    If the file is a vector file, the following formats are supported:
        "gpkg", "gml", "map", "tmp", "zip", "ZipExtFile"

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to file
    roughness_map : xarray.DataArray
        Roughness map
    crs : int, dict, str or pyproj.crs.CRS, optional
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    **kwargs : dict
        Additonal keyword arguments passed to writer.
    """
    return _map_to_file(roughness_map, filename, **kwargs)


def landcover_map_to_file(landcover_map, filename, **kwargs):
    """
    Write landcover map to file.

    The file can be either a raster file or a vector file.

    If the file is a raster file, the following formats are supported:
       "grd" and "tif" (geoTIFF).

    If the file is a vector file, the following formats are supported:
        "gpkg", "gml", "map", "tmp", "zip", "ZipExtFile"

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to file
    landcover_map : xarray.DataArray
        Landcover map
    crs : int, dict, str or pyproj.crs.CRS, optional
        Value to initialize `pyproj.crs.CRS` (Default: read from file)
    **kwargs : dict
        Additonal keyword arguments passed to writer.
    """
    return _map_to_file(landcover_map, filename, **kwargs)


def _is_raster_map(map):
    """Check if map is a raster map."""
    return isinstance(map, xr.DataArray)


def _is_vector_map(map):
    """Check if map is a vector map."""
    return isinstance(map, gpd.GeoDataFrame)


def _obj_is_raster_or_vector_map(map):
    """Check if map is a raster or vector map."""
    if _is_raster_map(map):
        return "raster"
    elif _is_vector_map(map):
        return "vector"
    else:
        raise ValueError("Map is not a raster or vector map.")


def roughness_to_landcover(rgh):
    """Converts a roughness map to landcover map."""
    spatial_data_type = _obj_is_raster_or_vector_map(rgh)
    if spatial_data_type == "raster":
        return _raster_map._roughness_to_landcover(rgh)
    elif spatial_data_type == "vector":
        if not _vector_map._is_z0(rgh):
            raise ValueError("Vector map is not a roughness map.")
        return _vector_map._roughness_to_landcover(rgh)
    else:
        raise UnsupportedFileTypeError("Obj must be a roughness vector or raster map.")


def landcover_to_roughness(lc, lctable):
    """Converts a landcover map to roughness map."""
    spatial_data_type = _obj_is_raster_or_vector_map(lc)
    if spatial_data_type == "raster":
        return _raster_map._landcover_to_roughness(lc, lctable)
    elif spatial_data_type == "vector":
        return _vector_map._landcover_to_roughness(lc, lctable)
    else:
        raise UnsupportedFileTypeError("Obj must be a landcover vector or raster map.")
