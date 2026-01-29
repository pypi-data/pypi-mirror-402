# (c) 2022 DTU Wind Energy
"""
Create empty datasets for various WindKit structures.

The datasets have the correct shape, dimensions, coordinates and data variables and
can also be filled with meaningful random data.
"""

import numpy as np
import xarray as xr

from windkit.xarray_structures.sector import create_sector_coords
from windkit.spatial import is_point, _spatial_stack, _spatial_unstack


def _empty_unstack(ds, is_scalar):
    """
    Allow user to retain scalar structure when using _spatial_unstack"
    """
    if is_scalar:
        return ds.isel(point=0)
    else:
        return _spatial_unstack(ds)


def _define_std_arrays(output_locs, n_sectors=12):
    """Return standard 2D, 3D, and 4D arrays in point format"""
    output_is_point = is_point(output_locs)
    out_std = _spatial_stack(output_locs).drop_vars(output_locs.data_vars)
    # check if it is a scalar
    is_scalar = not output_is_point and out_std.sizes["point"] == 1

    # Setup sector
    sector_coords = create_sector_coords(n_sectors).coords
    dims = ("sector", "point")
    out_sec_std = out_std.assign_coords(sector_coords)
    values = np.full((n_sectors, out_std.sizes["point"]), np.nan, np.float32)

    out_das = {}
    # x, y
    out_das["da_2d"] = xr.DataArray(
        values[0,],
        out_std.coords,
        dims[1:],
        attrs={"_pwio_data_is_2d": True},
    )

    # sector, x, y
    out_das["da_3d_nohgt"] = xr.DataArray(
        values, out_sec_std.coords, dims, attrs={"_pwio_data_is_2d": True}
    )

    # height, x, y
    out_das["da_3d_nosec"] = xr.DataArray(
        values[0,],
        out_std.coords,
        dims[1:],
        attrs={"_pwio_data_is_2d": False},
    )

    # Sector, height, x, y
    out_das["da_4d"] = xr.DataArray(values, out_sec_std.coords, dims, attrs={})

    return out_das, out_std.attrs, is_scalar


def _copy_chunks(in_ds, out_ds):
    """copy chunks from in_ds to out_ds"""
    # If input is not chunked it will have an emtpy chunks dict, so we need to build a
    # custom chunk_map based on the chunked dimensions of the original data.
    chunk_map = {}
    for i in in_ds.chunks:
        chunk_map[i] = in_ds.chunks[i][0]

    # Remember in Python empty dictionaries are False
    if chunk_map:
        return out_ds.chunk(chunk_map)
    else:
        return out_ds
