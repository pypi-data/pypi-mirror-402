# (c) 2022 DTU Wind Energy
"""Weibull wind climate module

When measuring over a long period the frequency of occurence of wind speed usually follows a
`Weibull distribution <https://en.wikipedia.org/wiki/Weibull_distribution>`_. It is therefore common
practice in the wind energy industry to use the Weibull *A* and *k*
parameters to denote the wind resource at a certain location.

Because there can be large differences in the wind climate when the wind is
coming from different wind directions, the Weibull distributions are usually specified
per sector.

A valid Weibull wind climate therefore has a dimension ``sector`` and the variables
``A``, ``k`` and ``wdfreq``. Also it must have a valid spatial structure. This module contains
functions that operate on and create weibull wind climates.
"""

__all__ = [
    "validate_wwc",
    "is_wwc",
    "create_wwc",
    "read_wwc",
    "read_mfwwc",
    "wwc_to_file",
    "wwc_to_bwc",
    "weibull_combined",
]

import io
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.special import gamma

from windkit.xarray_structures._validate import (
    _create_is_obj_function,
    _create_validation_wrapper_factory,
    _create_validator,
)
from windkit.xarray_structures.empty import (
    _copy_chunks,
    _define_std_arrays,
    _empty_unstack,
)
from windkit.xarray_structures.metadata import (
    _BWC_ATTRS,
    _WEIB_ATTRS,
    _update_history,
    _update_var_attrs,
)
from windkit.xarray_structures.sector import create_sector_coords
from windkit.xarray_structures.wsbin import create_wsbin_coords
from windkit.spatial import (
    _raster,
    count_spatial_points,
    is_cuboid,
    set_crs,
    to_raster,
)
from windkit.utils import _infer_file_format
from windkit.weibull import fit_weibull_k_sumlogm, weibull_cdf, weibull_moment

SUPPORTED_WWC_FILE_FORMATS_READ = ["rsf", "wrg", "pwc", "nc"]
SUPPORTED_WWC_FILE_FORMATS_WRITE = ["rsf", "wrg"]

VAR_WEIBULL_A = "A"
VAR_WEIBULL_k = "k"
VAR_WDFREQ = "wdfreq"
DIM_SECTOR = "sector"


WRG_HEADER_PATTERN = re.compile(
    r"\s*(\d+)\s+(\d+)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*",
    re.IGNORECASE,
)

DATA_VAR_DICT_WWC = {"A": ["sector"], "k": ["sector"], "wdfreq": ["sector"]}

REQ_DIMS_WWC = ["sector"]

REQ_COORDS_WWC = [
    "sector",
    "sector_ceil",
    "sector_floor",
]


def _validate_values_range(wwc):
    """Helper function to validate data variables are within range"""
    response_list = []

    if "A" in wwc.data_vars and any(
        xr.where(wwc.A.sum(dim="sector") <= 0.0, True, False).values.flatten()
    ):
        response_list.append("Sum of A values not positive.")

    if "k" in wwc.data_vars and any(
        xr.where(wwc.k == 0.0, True, False).values.flatten()
    ):
        response_list.append("At least one of the k values is zero.")

    if "wdfreq" in wwc.data_vars and "sector" in wwc.wdfreq.dims:
        sum_s = wwc["wdfreq"].sum(dim="sector")
        if not np.allclose(sum_s, 1.0):
            response_list.append("Wind direction frequency must sum to 1")

    return response_list


validate_wwc = _create_validator(
    variables=DATA_VAR_DICT_WWC,
    dims=REQ_DIMS_WWC,
    coords=REQ_COORDS_WWC,
    extra_checks=[_validate_values_range],
)

_validate_wwc_wrapper_factory = _create_validation_wrapper_factory(validate_wwc)

is_wwc = _create_is_obj_function(validate_wwc)


def create_wwc(output_locs, n_sectors=12, not_empty=True, seed=9876538, **kwargs):
    """Create empty weibull wind climate dataset.

    If not_empty=True,the data variables are filled with meaninful random numbers, e.g.
    the values from A are generated from a uniform function between 5
    and 10 and the values for k from a uniform function between 1.5 and 2.5.

    Parameters
    ----------
    output_locs : xarray.Dataset
        Output geospatial information
    n_sectors : int
        Number of sectors, defaults to 12.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data. Defaults to True.
    seed : int
        Seed for the random data, defaults to 9876538.
    kwargs : dict
        Additional arguments.

    Returns
    -------
    ds : xarray.Dataset
        Weibull wind climate dataset either empty or filled with
        random numbers.

    """
    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)

    ds = xr.Dataset(
        {"A": da_dict["da_4d"], "k": da_dict["da_4d"], "wdfreq": da_dict["da_4d"]},
        attrs=unstack_attrs,
    )
    n_pt = len(ds["point"])
    if not_empty:
        rng = np.random.default_rng(seed)
        k = rng.uniform(1.5, 2.5, [n_sectors, n_pt])
        A = rng.uniform(5, 10, [n_sectors, n_pt])
        ds["A"] = xr.DataArray(A, ds["A"].coords, ds["A"].dims)
        ds["k"] = xr.DataArray(k, ds["k"].coords, ds["k"].dims)
        ds["wdfreq"] = xr.DataArray(
            rng.dirichlet(np.ones(n_sectors), n_pt).T,
            ds["wdfreq"].coords,
            ds["wdfreq"].dims,
        )

    ustack_ds = _empty_unstack(ds, is_scalar)
    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _WEIB_ATTRS)

    return _update_history(ds)


def _has_wrg_header(infile, parse_header=False):
    """Check if a resource file has a WRG-style header
    and optionally parse the params.

    Parameters
    ----------
    infile : str, pathlib.Path, io.StringIO
        Input file to check
    parse_header : bool, optional
        If True, will attemp to parse the header params, by default False

    Returns
    -------
    bool:
        Whether the file has a wrg header
    GridParams, optional:
        Grid parameters parsed from the header, if parse_header=True

    """
    if isinstance(infile, io.StringIO):
        fobj = infile
    else:
        fobj = open(infile)

    line = fobj.readline().strip()

    if not isinstance(infile, io.StringIO):
        fobj.close()

    match = WRG_HEADER_PATTERN.match(line)

    return bool(match)


def _infer_resource_file_nsec(infile, skip_first=True):
    """Infer the number of sectors in resource file by reading
    column 70-72 and converting it to an integer.

    Parameters
    ----------
    infile : str, pathlib.Path, io.StringIO
        Resource file to infer sectors from.

    Returns
    -------
    int
        Number of sectors
    """
    if isinstance(infile, io.StringIO):
        fobj = infile
    else:
        fobj = open(infile)

    # Skip the first line
    if skip_first:
        fobj.readline()

    # Read the second line
    line = fobj.readline()

    if not isinstance(infile, io.StringIO):
        fobj.close()

    return int(line[69:72])  # column 70-72 using python indexing


def _read_resource_file(
    resource_file, crs, n_sectors=12, to_cuboid=False, use_production=False, **kwargs
):
    """Reads .wrg or .rsf file into a weibull wind climate dataset.

    Parameters
    ----------
    resource_file : str, pathlib.Path, io.StringIO
        Path to resource file
    crs : int, dict, str or CRS
        Value to create CRS object or an existing CRS object
    n_sectors : int
        Number of sectors in file. Defaults to 12.
    to_cuboid: boolean
        If true, the dataset will be converted to the cuboid spatial
        structure (dimensions south_north, west_east, height).
    use_production: bool
        If True, the column with power in the file is interpreted as power production,
        i.e. stored as 'gross_aep' in the dataset. If False, it is stored as 'power_density'.
        If the values in the file are power production, they are originally storedin Wh/y,
        but they are saved with units GWh/y in the dataset.  Defaults to False.

    Returns
    -------
    wwc: xarray.Dataset
        Weibull wind climate dataset.
    """
    if crs is None:
        raise ValueError("crs must be specified")

    has_wrg_header = _has_wrg_header(resource_file)
    n_sectors = _infer_resource_file_nsec(resource_file, skip_first=has_wrg_header)

    df = pd.read_fwf(
        resource_file,
        widths=tuple([10, 10, 10, 8, 5, 5, 6, 15, 3] + [4, 4, 5] * n_sectors),
        header=None,
        skiprows=int(has_wrg_header),
    )
    power_col = "gross_aep" if use_production else "power_density"
    header = [
        "name",
        "west_east",
        "south_north",
        "site_elev",
        "height",
        "A_combined",
        "k_combined",
        power_col,
        "n_sectors",
    ]

    for i in range(1, n_sectors + 1):
        header += f"f_{i} A_{i} k_{i}".split()

    df.columns = header

    can_be_raster = _raster._can_be_raster(df["west_east"], df["south_north"])

    df = df.set_index(["name"])

    wwc = df.to_xarray()

    wwc = wwc.assign_coords(point=(("name",), np.arange(len(df.index))))
    wwc = wwc.swap_dims({"name": "point"})
    wwc = wwc.drop_vars("point")
    wwc = wwc.assign_coords(
        west_east=(("point",), wwc.west_east.values),
        south_north=(("point",), wwc.south_north.values),
        height=(("point",), wwc.height.values),
    )

    knames = [f"k_{sec}" for sec in range(1, n_sectors + 1)]
    Anames = [f"A_{sec}" for sec in range(1, n_sectors + 1)]
    fnames = [f"f_{sec}" for sec in range(1, n_sectors + 1)]

    wwc["k"] = xr.concat([wwc[n] for n in knames], dim="sector")
    wwc["A"] = xr.concat([wwc[n] for n in Anames], dim="sector")
    wwc["wdfreq"] = xr.concat([wwc[n] for n in fnames], dim="sector")

    wwc["site_elev"] = wwc["site_elev"].astype(np.float64)
    wwc["k"] = wwc["k"] / 100.0
    wwc["A"] = wwc["A"] / 10.0
    wwc["wdfreq"] = wwc["wdfreq"] / wwc["wdfreq"].sum(dim="sector", skipna=False)

    wwc = wwc.drop_vars(
        ["n_sectors"]
        + [f"f_{sec}" for sec in range(1, n_sectors + 1)]
        + [f"A_{sec}" for sec in range(1, n_sectors + 1)]
        + [f"k_{sec}" for sec in range(1, n_sectors + 1)]
    )

    if use_production:
        wwc["gross_aep"] = wwc["gross_aep"] / 1e9  # Wh/y -> GWh/y
    wwc = set_crs(wwc, crs)
    wdcenters = create_sector_coords(n_sectors)
    wwc = wwc.assign_coords(**wdcenters.coords)

    n_spatial = count_spatial_points(wwc)

    if (not can_be_raster) and to_cuboid and (n_spatial > 1):
        logging.warning(
            "_read_resource_file: Data cannot be converted to raster, returning point."
        )
    if can_be_raster and to_cuboid or n_spatial == 1 and to_cuboid:
        wwc = to_raster(wwc, ignore_raster_check=True)
        if "elevation" in wwc.data_vars:
            wwc["elevation"] = wwc["elevation"].isel(height=0)

    wwc = _update_var_attrs(wwc, _WEIB_ATTRS)
    return _update_history(wwc)


def _read_rsffile(
    rsffile, crs=None, *, to_cuboid=False, use_production=False, **kwargs
):
    """Reads .rsf file into a weibull wind climate dataset.

    Parameters
    ----------
    rsffile : str, pathlib.Path, io.StringIO
        Path to .rsf file
    crs : int, dict, str or CRS
        Value to create CRS object or an existing CRS object
    to_cuboid: boolean
        If true, the dataset will be converted to the cuboid spatial
        structure (dimensions south_north, west_east, height).
    use_production: bool
        If True, the column with power in the file is interpreted as power production,
        i.e. stored as 'gross_aep' in the dataset. If False, it is stored as 'power_density'.
        If the values in the file are power production, they are originally storedin Wh/y,
        but they are saved with units GWh/y in the dataset.  Defaults to False.

    Returns
    -------
    wwc: xarray.Dataset
        Weibull wind climate dataset.
    """
    return _read_resource_file(
        rsffile, crs=crs, to_cuboid=to_cuboid, use_production=use_production, **kwargs
    )


def _read_wrgfile(wrgfile, crs=None, *, to_cuboid=True, use_production=False, **kwargs):
    """Reads .wrg file into a weibull wind climate dataset.

    Parameters
    ----------
    wrgfile : str, pathlib.Path, io.StringIO
        Path to .wrg file
    crs : int, dict, str or CRS
        Value to create CRS object or an existing CRS object
    to_cuboid: boolean
        If true, the dataset will be converted to the cuboid spatial
        structure (dimensions south_north, west_east, height).
    use_production: bool
        If True, the column with power in the file is interpreted as power production,
        i.e. stored as 'gross_aep' in the dataset. If False, it is stored as 'power_density'.
        If the values in the file are power production, they are originally storedin Wh/y,
        but they are saved with units GWh/y in the dataset.  Defaults to False.

    Returns
    -------
    wwc: xarray.Dataset
        Weibull wind climate dataset.
    """
    return _read_resource_file(
        wrgfile, crs=crs, to_cuboid=to_cuboid, use_production=use_production, **kwargs
    )


def _read_pwcfile(pwcfile, spatial_dataset):
    """Reads .pwc predicted wind climate file from WAsP in XML format.
       The .pwc file does not include spatial information, so it must
       be passed as a parameter.

    Parameters
    ----------
    pwcfile: str,pathlib.Path, io.StringIO
        Path to .pwc file
    spatial_dataset: xarray.Dataset
        xarray dataset with the spatial info
    """
    ds = pd.read_xml(
        pwcfile, names=["index", "sector", "sector_width", "wdfreq", "A", "k"]
    )
    ds = ds.set_index("sector")[["A", "k", "wdfreq"]].to_xarray()
    ds = ds.assign_coords(create_sector_coords(ds.sector.size).coords)
    ds = ds.expand_dims(spatial_dataset.sizes)
    ds = ds.assign_coords(spatial_dataset.coords)
    wwc = _update_var_attrs(ds, _WEIB_ATTRS)
    return _update_history(wwc)


def _can_be_int(x):
    """Check if x can be converted to int."""
    try:
        int(x)
        return True
    except ValueError:
        return False


def _convert_to_int_or_fixed_decimals(x, decimals=1):
    if _can_be_int(x):
        return int(x)
    else:
        return np.round(x, decimals=decimals)


def _wrg_header(wwc):
    """Write WWC grid dimensions to WRG header with the format:
          nx ny xmin ymin cell_size

    Parameters
    ----------
    wwc : xarray.Dataset
        Weibull wind climate xarray dataset.

    Returns
    -------
    str
        WRG header.

    """
    nx, ny = _raster._shape(wwc)
    xmin = _convert_to_int_or_fixed_decimals(wwc.west_east.values.min(), decimals=1)
    ymin = _convert_to_int_or_fixed_decimals(wwc.south_north.values.min(), decimals=1)
    size = _convert_to_int_or_fixed_decimals(_raster._spacing(wwc), decimals=1)
    return f" {nx:<13} {ny:<13} {xmin:>9} {ymin:>13} {size:>8}"


def _get_rsf_formatters(df, n_sectors=12, use_production=False, formatters=None):
    """Returns a list of functions to format the data in the RSF/WRG file.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe with the data to be formatted.

    var_power : str
        Name of the variable to be used as power/aep.

    n_sectors : int
        Number of sectors.

    use_production : bool
        If true, the gross_aep variable will be used instead of power_density.

    formatters : dict
        Dictionary with the variable names as keys and the functions to format
        the data as values.

    Returns
    -------
    list
        List of functions to format the data in the RSF/WRG file.
    """

    var_power = "gross_aep" if use_production else "power_density"

    fixed_columns = [
        "name",
        "west_east",
        "south_north",
        "elevation",
        "height",
        "A_combined",
        "k_combined",
        var_power,
        "n_sectors",
    ]

    _formatters_default = {
        "name": lambda x: f"{x:<10}",  # 10
        "west_east": lambda x: f"{x:>9.1f}",  # 10
        "south_north": lambda x: f"{x:>9.1f}",  # 10
        "elevation": lambda x: f"{x:>7.0f}",  # 8
        "height": lambda x: f"{x:>4.1f}",  # 5
        "A_combined": lambda x: f"{x:>4.2f}",  # 5
        "k_combined": lambda x: f"{x:>5.3f}",  # 6
        "power_density": lambda x: f"{x:>14.4f}",  # 15
        "gross_aep": lambda x: f"{x:>14.0f}",  # 15
        "n_sectors": lambda x: f"{x:>2}",  # 3
        "A": lambda x: f"{x:>3.0f}",  # 4
        "k": lambda x: f"{x:>4.0f}",  # 4
        "wdfreq": lambda x: f"{x:>3.0f}",  # 5
    }
    if formatters is None:
        formatters = _formatters_default
    else:
        formatters = {**_formatters_default, **formatters}

    #
    #  INDIVIDUAL CHECKS AND FORMATTER ADJUSTMENTS
    #

    def _check_max(df, var, maxval):
        vmax = np.abs(df[var]).max()
        if vmax > maxval:
            raise ValueError(
                f"The {var} of one or more points is larger than {maxval}. "
                f"Please check the {var}."
            )

    # name: 10(10)
    if df["name"].str.len().max() > 10:
        raise ValueError(
            "The name of one or more points is longer than 10 characters. "
            "Please shorten the names."
        )

    # west_east: 10(9)
    _check_max(df, "west_east", 99999999)

    if np.abs(df["west_east"]).max() > 999999:
        formatters["west_east"] = lambda x: f"{x:>9.0f}"

    # south_north: 10(9)
    _check_max(df, "south_north", 99999999)

    if np.abs(df["south_north"]).max() > 999999:
        formatters["south_north"] = lambda x: f"{x:>9.0f}"

    # elevation: 8(7)
    _check_max(df, "site_elev", 999999)

    if np.abs(df["site_elev"]).max() > 9999:
        formatters["elevation"] = lambda x: f"{x:>7.0f}"

    # height: 5(4)
    _check_max(df, "height", 9999)

    # When heights are > 100m, the height needs to be written as an integer
    if df["height"].max() > 100.0:
        formatters["height"] = lambda x: f"{x:>4.0f}"

    # A_combined: 5(4)
    _check_max(df, "A_combined", 9999)

    if df["A_combined"].max() >= 10.0:
        formatters["A_combined"] = lambda x: f"{x:>4.1f}"
    elif df["A_combined"].max() >= 100.0:
        formatters["A_combined"] = lambda x: f"{x:>4.0f}"

    # k_combined: 6(5)
    _check_max(df, "k_combined", 99999)

    if df["k_combined"].max() >= 10.0:
        formatters["k_combined"] = lambda x: f"{x:>5.2f}"
    elif df["k_combined"].max() >= 100.0:
        formatters["k_combined"] = lambda x: f"{x:>5.1f}"
    elif df["k_combined"].max() >= 1000.0:
        formatters["k_combined"] = lambda x: f"{x:>5.0f}"

    # power_density / gross_aep: 15(14)
    _check_max(df, var_power, 99999999999999)

    # When all values are missing for power/aep, i.e. valued as -9999,
    # the value needs to be written as an integer
    if all(df[var_power] == -9999):
        formatters[var_power] = lambda x: f"{x:>14.0f}"

    if df[var_power].max() >= 10000000000:
        formatters[var_power] = lambda x: f"{x:>14.1f}"
    elif df[var_power].max() >= 100000000000:
        formatters[var_power] = lambda x: f"{x:>14.0f}"

    # n_sectors: 3(2)
    _check_max(df, "n_sectors", 99)

    for isec in range(n_sectors):
        # A: 4(3)
        _check_max(df, str(("A", isec)), 999)

        # k: 4(3)
        _check_max(df, str(("k", isec)), 999)

        # wdfreq: 5(3)
        _check_max(df, str(("wdfreq", isec)), 9999)

    formatters_list = []
    for col in fixed_columns:
        formatters_list.append(formatters[col])

    for isec in range(n_sectors):
        formatters_list.append(formatters["wdfreq"])
        formatters_list.append(formatters["A"])
        formatters_list.append(formatters["k"])

    return formatters_list


def _to_resource_file(
    wwc,
    /,
    rsffile,
    wrg_header=False,
    use_production=False,
    formatters=None,
    **kwargs,
):
    """Write weibull wind climate dataset to a resource file (.rsf or .wrg).

    Parameters
    ----------
    wwc : xarray.Dataset
        Weibull wind climate xarray dataset.
    rsffile : str
        Path to resource file
    wrg_header : bool
        If True, the WRG header will be added to the file.
        Requires a cuboid dataset.
    use_production : bool
        If true, the "gross_aep" variable will be used instead of "power_density".
    formatters : dict
        Dictionary with the variable names as keys and the functions to format
        the data as values.

        For each variable the expected widths in the formatter are:
            name: 10
            west_east: 9
            south_north: 9
            elevation: 7
            height: 4
            A_combined: 4
            k_combined: 5
            power_density: 14
            gross_aep: 14
            n_sectors: 2
            A: 3
            k: 4
            wdfreq: 3

        A space is added after each variable. Meaning the effective
        width of the string representation of the variable is the
        width in the formatter plus one (except for the first variable)

        A formatter can look like:
            formatters  = {
                "west_east": lambda x: f"{x:<9.2f}",
            }

        In this case the width of the string representation of the
        west_east variable will be 10 (9+1). And the number of decimals
        will be 2 instead of the default 1. If a int representation
        is desired, "{x:<9.0f}" can be used.

    """

    # Check if wwc has unsupported dimensions
    approved_dims = [
        "sector",
        "point",
        "stacked_point",
        "south_north",
        "west_east",
        "height",
    ]
    if any([dim not in approved_dims for dim in wwc.dims]):
        raise ValueError(
            f"Unsupported dimensions in wwc: {wwc.dims}. "
            f"Supported dimensions: {approved_dims}"
        )

    if use_production and "gross_aep" not in wwc.data_vars:
        raise ValueError(
            "The gross_aep variable is required to write a resource file with "
            "use_production=True."
        )

    if use_production:
        var_power = "gross_aep"
    else:
        var_power = "power_density"

    wwc_cp = wwc.copy()

    if wrg_header:
        if not is_cuboid(wwc):
            raise ValueError("WWC must be a 'cuboid' to add WRG header!")
        header = _wrg_header(wwc)

    # I feel like it would be cleaner to throw a key error or we always
    # return the parameters required from `downscale()`. But adding the vars
    # as needed works as well.
    if "A_combined" not in wwc_cp.data_vars:
        wwc_cp[["A_combined", "k_combined"]] = weibull_combined(wwc_cp)
    if "wspd" not in wwc_cp.data_vars:
        wwc_cp["wspd"] = _mean_wind_speed(wwc_cp)
    if "power_density" not in wwc_cp.data_vars:
        try:
            air_dens = wwc_cp["air_density"]
        except KeyError:
            air_dens = 1.225
        wwc_cp["power_density"] = _mean_power_density(
            wwc_cp, air_density=air_dens, bysector=False
        )

    # remove unneeded vars
    wwc_cp = wwc_cp.drop_vars(
        ["sector", "sector_ceil", "sector_floor", "crs"], errors="ignore"
    )

    n_sectors = wwc_cp.sizes["sector"]

    # round values in the order that fits best with WAsP values
    wwc_cp["A"] = wwc_cp["A"].round(decimals=1) * 10.0
    wwc_cp["k"] = wwc_cp["k"].round(decimals=2) * 100.0
    wwc_cp["wdfreq"] = wwc_cp["wdfreq"].round(decimals=3) * 1000.0

    wwc_cp["site_elev"] = wwc_cp["site_elev"].astype(np.int16)
    wwc_cp["n_sectors"] = xr.full_like(wwc_cp["site_elev"], n_sectors, dtype=np.int16)

    if use_production:
        wwc_cp["gross_aep"] = wwc_cp["gross_aep"] * 1e9  # GWh/y -> Wh/y

    # select variables that do not depend on wind direction sector
    vars = [
        "name",
        "west_east",
        "south_north",
        "site_elev",
        "height",
        "A_combined",
        "k_combined",
        var_power,
        "n_sectors",
    ]

    df = wwc_cp[
        ["site_elev", "A_combined", "k_combined", var_power, "n_sectors"]
    ].to_dataframe()

    if "name" not in df.columns:
        df["name"] = "GridPoint"  # insert text column at first position

    # select variables that depend on wind direction sector
    sec_vars = [
        str((var, sec)) for sec in range(n_sectors) for var in ["wdfreq", "A", "k"]
    ]
    df_sec = wwc_cp[["wdfreq", "A", "k"]].to_dataframe()
    df_sec = df_sec.pivot_table(
        index=df.index.names, columns="sector", values=["wdfreq", "A", "k"]
    )

    # merge all-sector and sectorwise values
    df_total = (
        pd.concat([df, df_sec], axis=1)
        .reset_index()
        .drop(["point", "stacked_point"], axis=1, errors="ignore")
    )  # concat combined and sectorwise values
    # transform all column names to string to make it compatible with pandas 1.4
    df_total.columns = [str(x) for x in df_total.columns]
    df_total = df_total[vars + sec_vars]  # select vars in correct order

    formatters_list = _get_rsf_formatters(
        df_total,
        n_sectors=n_sectors,
        use_production=use_production,
        formatters=formatters,
    )

    str_list = df_total.to_string(
        header=False,
        index=False,
        index_names=False,
        formatters=formatters_list,
    )

    def _is_char_21_blank(s):
        """Check that character 21 is blank."""
        if s[20] != " ":
            return False
        else:
            return True

    def _remove_initial_blank_space(s):
        """Remove initial blank space from each line of the string to be written.
        This is required for the .rsf/.wrg format to get the correct widths written to file.
        """
        sout = ""
        for line in s.split("\n"):
            if line[0] == " ":
                sout += line[1:] + "\n"
        return sout

    def _check_row_widths(s, n_sectors=12):
        """Check that the row widths are correct for the number of sectors."""
        width_expected = 72 + n_sectors * 13
        for line in s.split("\n")[:-1]:
            width = len(line)
            if width != width_expected:
                raise ValueError(
                    f".rsf/.wrg row width is {width} Expected {width_expected} for {n_sectors} sectors!\nare the formatters correct?"
                )

    def _check_ncols(s, n_sectors=12):
        """Check that the number of columns is correct read back in for the number of sectors."""
        ncols_expected = 9 + n_sectors * 3
        df = pd.read_fwf(
            io.StringIO(s),
            widths=tuple([10, 10, 10, 8, 5, 5, 6, 15, 3] + [4, 4, 5] * n_sectors),
            header=None,
        )
        ncols = df.shape[1]
        if ncols != ncols_expected:
            raise ValueError(
                f".rsf/.wrg has {ncols} columns. Expected {ncols_expected} for {n_sectors} sectors!"
            )

    # check that character 21 is blank and remove initial blank space if not
    # This problem is related to the pandas version (or a dependency of pandas)
    if not _is_char_21_blank(str_list):
        str_list = _remove_initial_blank_space(str_list)

    _check_row_widths(str_list, n_sectors=n_sectors)
    _check_ncols(str_list, n_sectors=n_sectors)

    with open(rsffile, "w", newline="\r\n") as text_file:
        if wrg_header:
            text_file.write(header + "\n")
        text_file.write(str_list)


def _to_rsffile(
    wwc, rsffile, wrg_header=False, use_production=False, formatters=None, **kwargs
):
    """Write weibull wind climate dataset to .rsf file.

    Parameters
    ----------
    wwc : xarray.Dataset
        Weibull wind climate xarray dataset.
    rsffile: str
        Path to .rsf file
    """
    return _to_resource_file(
        wwc,
        rsffile,
        wrg_header=wrg_header,
        use_production=False,
        formatters=formatters,
        **kwargs,
    )


def _to_wrgfile(wwc, wrgfile, use_production=False, formatters=None):
    """Write weibull wind climate dataset to .wrg file.

    Parameters
    ----------
    wwc : xarray.Dataset
        Weibull wind climate xarray dataset.
    wrgfile: str
        Path to .wrg file
    """
    return _to_resource_file(
        wwc, wrgfile, wrg_header=True, use_production=False, formatters=formatters
    )


def _read_grdfiles(grdfiles, *, regex_pattern=None, regex_var_order=None):
    """Reads a .grd file into a weibull wind climate dataset.

    Parameters
    ----------
    grdfiles: str or list
        path of .grd file or list of .grd files.

    regex_pattern: re str
        Filename regex pattern to extract height, sector, and variable name.
        Defaults to None.

    regex_var_order: list or tuple
        Order of 'height', 'sector', and 'var' in regex_pattern. Defaults to None.

    Returns
    -------
    wwc: xarray.Dataset
        Weibull wind climate dataset.
    """

    def _rename_var(var):
        """
        Function to rename WAsP variable names to short hand name
        """
        _rename = {
            "Flow inclination": "flow_inclination",
            "Mean speed": "wspd",
            "Meso roughness": "z0meso",
            "Obstacles speed": "obstacle_speedups",
            "Orographic speed": "orographic_speedups",
            "Orographic turn": "orographic_turnings",
            "Power density": "power_density",
            "RIX": "rix",
            "Roughness changes": "nrch",
            "Roughness speed": "roughness_speedups",
            "Sector frequency": "wdfreq",
            "Turbulence intensity": "turbulence_intensity",
            "Weibull-A": "A",
            "Weibull-k": "k",
            "Elevation": "site_elev",
        }

        return _rename[var]

    def _read_grd_data(filename):
        def _parse_line_floats(f):
            return [float(i) for i in f.readline().strip().split()]

        def _parse_line_ints(f):
            return [int(i) for i in f.readline().strip().split()]

        with open(filename, "rb") as f:
            _ = f.readline().strip().decode()  # file_id
            nx, ny = _parse_line_ints(f)
            xl, xu = _parse_line_floats(f)
            yl, yu = _parse_line_floats(f)
            zl, zu = _parse_line_floats(f)
            values = np.genfromtxt(f)

        xarr = np.linspace(xl, xu, nx)
        yarr = np.linspace(yl, yu, ny)

        # note that the indexing of WAsP grd file is 'xy' type, i.e.,
        # values.shape == (xarr.shape[0], yarr.shape[0])
        # we need to transpose values to match the 'ij' indexing
        values = values.T

        return xarr, yarr, values

    def _parse_grdfile(grdfile, regex_pattern=None, regex_var_order=None):
        match = re.findall(regex_pattern, grdfile.name)[0]
        meta = {k: v for k, v in zip(regex_var_order, match)}
        meta["var"] = _rename_var(meta["var"])

        xarr, yarr, values = _read_grd_data(grdfile)

        dims = ["west_east", "south_north", "height"]
        coords = {
            "height": [float(meta["height"])],
            "x": (("west_east",), xarr),
            "y": (("south_north",), yarr),
            "west_east": (("west_east",), xarr),
            "south_north": (("south_north",), yarr),
        }
        values = values[..., np.newaxis]

        if not meta["sector"].lower() == "all":
            dims += ["sector"]
            coords["sector"] = [int(meta["sector"])]
            values = values[..., np.newaxis]
        else:
            if meta["var"] != "site_elev":
                meta["var"] = meta["var"] + "_combined"

        da = xr.DataArray(values, dims=dims, coords=coords, name=meta["var"])

        if da.name == "site_elev":
            da = da.isel(height=0, drop=True)

        return da

    if not isinstance(grdfiles, list):
        grdfiles = [grdfiles]

    grdfiles = list(Path(f) for f in grdfiles)

    if regex_pattern is None:
        regex_pattern = r"Sector (\w+|\d+) \s+ Height (\d+)m \s+ ([a-zA-Z0-9- ]+)"

    if regex_var_order is None:
        regex_var_order = ("sector", "height", "var")

    wwc = xr.merge(
        [
            _parse_grdfile(
                grdfile, regex_pattern=regex_pattern, regex_var_order=regex_var_order
            )
            for grdfile in grdfiles
        ]
    )

    ds = _update_var_attrs(wwc, _WEIB_ATTRS)
    return _update_history(ds)


def read_wwc(filename, *, file_format="infer", **kwargs):
    """Read a weibull wind climate dataset from a file.

    Parameters
    ----------
    filename : str or pathlib.Path
        Path to the file to read the dataset from.
    file_format : str
        File format of the file. If "infer", the file format is inferred from the file extension.
        Supported file formats are "rsf", "wrg", "grd", and "nc". Defaults to "infer".
    **kwargs
        Additional keyword arguments passed to the read function

    Returns
    -------
    xarray.Dataset
        Weibull wind climate dataset.
    """
    if file_format == "infer":
        file_format = _infer_file_format(filename)

    if file_format == "rsf":
        ds = _read_rsffile(filename, **kwargs)
    elif file_format == "wrg":
        ds = _read_wrgfile(filename, **kwargs)
    elif file_format == "grd":
        ds = _read_grdfiles(filename, **kwargs)
    elif file_format == "nc":
        ds = xr.open_dataset(filename, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    validate_wwc(ds, run_extra_checks=False)
    ds = _update_var_attrs(ds, _WEIB_ATTRS)
    return _update_history(ds)


def read_mfwwc(files, file_format="infer", **kwargs):
    """Read multiple weibull wind climate datasets from files.

    Parameters
    ----------
    files : list of str or pathlib.Path
        Paths to the files to read the datasets from.
    file_format : str
        File format of the files. If "infer", the file format is inferred from the file extension.
        Supported file formats are "rsf", "wrg", and "grd". Defaults to "infer".
    **kwargs
        Additional keyword arguments passed to the read function

    Returns
    -------
    xarray.Dataset
        Weibull wind climate dataset.
    """
    if file_format == "infer":
        file_format = _infer_file_format(files[0])

    if file_format == "grd":
        ds = _read_grdfiles(files, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    validate_wwc(ds, run_extra_checks=False)
    ds = _update_var_attrs(ds, _WEIB_ATTRS)
    return _update_history(ds)


@_validate_wwc_wrapper_factory(run_extra_checks=False)
def wwc_to_file(wwc, filename, *, file_format="infer", **kwargs):
    """Write a weibull wind climate dataset to a file.

    Parameters
    ----------
    wwc : xarray.Dataset
        Weibull wind climate dataset.
    filename : str or pathlib.Path
        Path to the file to write the dataset to.
    file_format : str
        File format of the file. If "infer", the file format is inferred from the file extension.
        Supported file formats are "rsf", "wrg", and "nc". Defaults to "infer".
    **kwargs
        Additional keyword arguments passed to the write function
    """

    if file_format == "infer":
        file_format = _infer_file_format(filename)

    if file_format == "rsf":
        _to_rsffile(wwc, filename, **kwargs)
    elif file_format == "wrg":
        _to_wrgfile(wwc, filename, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


@_validate_wwc_wrapper_factory(run_extra_checks=False)
def weibull_combined(wwc, atol=0.000001):
    """Return the all sector A & k.

    This is known as the combined weibull A and k in the
    WAsP GUI. For more information, see here:
    https://www.wasp.dk/support/frequently-asked-questions/wasp-faq/emergent-and-combined-all-sector-weibull-distributions
    Using the combined weibull A and k are calculated
    using first and third moment conservation rules.

    Parameters
    ----------
    wwc: xarray.Dataset
        Weibull Wind Climate dataset.

    Returns
    -------
    tuple of xr.DataArray
        All sector A & k DataArrays
    """
    sum1 = (wwc["wdfreq"] * weibull_moment(wwc["A"], wwc["k"], 1)).sum(
        dim="sector", skipna=False
    )
    sum3 = (wwc["wdfreq"] * weibull_moment(wwc["A"], wwc["k"], 3)).sum(
        dim="sector", skipna=False
    )
    sum1 = sum1 / wwc["wdfreq"].sum(dim="sector", skipna=False)
    sum3 = sum3 / wwc["wdfreq"].sum(dim="sector", skipna=False)

    sum_logm = np.log(sum3) / 3.0 - np.log(sum1)
    k_combined = fit_weibull_k_sumlogm(
        sum_logm, order_m_first=1, order_m_higher=3, atol=atol
    )
    A_combined = sum1 / gamma(1.0 + 1.0 / k_combined)

    return A_combined, k_combined


def _mean_ws_moment(wwc, moment=1, *, bysector=False):
    """Calculate the mean wind speed from a weibull wind climate dataset.

    Parameters
    ----------
    wwc: xarray.Dataset
        Weibull Wind Climate dataset.
    moment: int
        Moment to calculate. Defaults to 1.
    bysector: bool
        Return results by sector or as an all-sector value. Defaults to False.

    Returns
    -------
    xarray.DataArray
        DataArray with the mean wind speed.
    """

    moment = weibull_moment(wwc[VAR_WEIBULL_A], wwc[VAR_WEIBULL_k], moment)

    if not bysector:
        moment = (moment * wwc[VAR_WDFREQ]).sum(dim=DIM_SECTOR, skipna=False)

    return moment


def _mean_wind_speed(wwc, *, bysector=False):
    """Calculate the mean wind speed from a weibull wind climate dataset.

    Parameters
    ----------
    wwc: xarray.Dataset
        Weibull Wind Climate dataset.
    bysector: bool
        Return results by sector or as an all-sector value. Defaults to False.

    Returns
    -------
    xarray.DataArray
        DataArray with the mean wind speed.
    """
    return _mean_ws_moment(wwc, moment=1, bysector=bysector)


def _mean_power_density(wwc, *, air_density=1.225, bysector=False):
    """Calculate the power density

    Parameters
    ----------
    wwc: xarray.Dataset
        Weibull wind climate dataset.
    air_density :  float
        Air density.
    bysector: bool
        Return sectorwise mean wind speed if True. defaults to False.

    Returns
    pd : xarray.DataArray
        Data array with power density.
    """
    return 0.5 * air_density * _mean_ws_moment(wwc, moment=3, bysector=bysector)


@_validate_wwc_wrapper_factory(run_extra_checks=False)
def wwc_to_bwc(wwc, ws_bins):
    """Creates object from directional A's and k's.

    Parameters
    ----------
    wwc: xarray.Dataset
        Weibull wind climate xr.Dataset object
    ws_bins: np.array
        Wind speed bin edges

    Returns
    -------
    bwc : xarray.Dataset
        binned wind climate from a Weibull distribution.
    """
    wwc = wwc.copy()  # make a copy to avoid modifications leaving scope

    ws_bins = xr.DataArray(ws_bins, dims=("wsbin",))
    cdfs = weibull_cdf(wwc.A, wwc.k, ws_bins)
    ws_freq = cdfs.isel(wsbin=slice(1, None)) - cdfs.isel(wsbin=slice(None, -1))
    ws_freq = ws_freq / ws_freq.sum(dim="wsbin")
    ws_freq = ws_freq.fillna(0.0)

    bwc = wwc[
        [v for v in wwc.data_vars if v not in ["A", "k"]]
    ]  # pass through other variables
    bwc["wsfreq"] = ws_freq

    wscenters = create_wsbin_coords(ws_bins)
    bwc = bwc.assign_coords(
        {
            **wscenters.coords,
        }
    )
    bwc = _update_var_attrs(bwc, _BWC_ATTRS)
    return _update_history(bwc)


def _ws_cdf(wwc, **kwargs):
    """Calculates wind speed cumulative distribution function from weibull wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")


def _ws_freq_gt_mean(wwc, **kwargs):
    """Calculates wind speed frequency greater than mean from weibull wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")
