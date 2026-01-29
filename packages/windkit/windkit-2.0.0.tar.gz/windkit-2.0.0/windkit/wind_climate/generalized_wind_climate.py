# (c) 2022 DTU Wind Energy
"""
Generalized wind climate module

This module contains the various functions for working with generalized wind climates.

Currently this only supports creating gwc datasets from .lib files or from
NetCDF files. In the future we will also support the ability to read in .gwc
files.
"""

__all__ = [
    "validate_gwc",
    "is_gwc",
    "create_gwc",
    "read_gwc",
    "gwc_to_file",
]


import re
import warnings
from pathlib import Path

import numpy as np
import xarray as xr
from lxml import etree

from windkit._rvea_xml import (
    _parse_rvea_anemometer_site_details,
    _parse_rvea_generalised_mean_wind_climate,
)
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
    _WEIB_ATTRS,
    _ALL_VARS_META,
    _update_history,
    _update_var_attrs,
    _create_coords,
)
from windkit.xarray_structures.sector import create_sector_coords
from windkit.spatial import (
    create_dataset,
    crs_are_equal,
    reproject,
    to_point,
)
from windkit.utils import _infer_file_format

SUPPORTED_GWC_FILE_FORMATS_READ = ["lib", "gwc", "nc"]
SUPPORTED_GWC_FILE_FORMATS_WRITE = ["lib"]

_GEN_COORDS_META = {
    "gen_height": _ALL_VARS_META["gen_height"],
    "gen_roughness": _ALL_VARS_META["gen_roughness"],
    "sector": _ALL_VARS_META["sector"],
}

DATA_VAR_DICT_GWC = {
    "A": ["sector", "gen_height", "gen_roughness"],
    "wdfreq": ["sector", "gen_height", "gen_roughness"],
    "k": ["sector", "gen_height", "gen_roughness"],
}

REQ_DIMS_GWC = ["sector", "gen_height", "gen_roughness"]

REQ_COORDS_GWC = [
    "gen_height",
    "gen_roughness",
    "sector_ceil",
    "sector_floor",
    "sector",
]


def _validate_height_and_roughness(genwc):
    """Helper function to validate generalized_height and generalized_roughness"""
    response_list = []

    if "gen_height" in genwc.dims:
        if genwc.sizes["gen_height"] < 2:
            response_list.append("gen_height needs at least 2 entries")

    if "gen_roughness" in genwc.dims:
        if genwc.sizes["gen_roughness"] < 2:
            response_list.append("gen_roughness needs at least 2 entries")
        if genwc["gen_roughness"].min() != 0.0:
            response_list.append("The first entry of gen_roughness must be 0.0")

    return response_list


def _validate_greater_than_zero(genwc):
    """Helper function to validate generalized heights and roughness are positive"""
    response_list = []

    if "gen_roughness" in genwc.dims and any(
        xr.where(genwc.gen_roughness.values < 0.0, True, False)
    ):
        response_list.append("'gen_roughness' has negative values")

    if "gen_height" in genwc.dims and any(
        xr.where(genwc.gen_height.values < 0.0, True, False)
    ):
        response_list.append("'gen_height' has negative values")

    return response_list


validate_gwc = _create_validator(
    variables=DATA_VAR_DICT_GWC,
    dims=REQ_DIMS_GWC,
    coords=REQ_COORDS_GWC,
    extra_checks=[_validate_height_and_roughness, _validate_greater_than_zero],
)

_validate_gwc_wrapper_factory = _create_validation_wrapper_factory(validate_gwc)

is_gwc = _create_is_obj_function(validate_gwc)


def create_gwc(
    output_locs,
    n_sectors=12,
    not_empty=True,
    seed=9876538,
    gen_heights=(10.0, 50.0, 100.0),
    gen_roughnesses=(0.0, 0.03, 0.1, 0.4, 1.5),
    wdfreq_constant=False,
    **kwargs,
):
    """Create empty generalized wind climate dataset.

    If not_empty=True, the data variables are filled with meaninful random numbers, e.g.
    the values from A are generated from a uniform function between 5
    and 10 and the values for k from a uniform function between 1.5 and 2.5.

    Parameters
    ----------
    output_locs : xarray.Dataset
        Output geospatial information.
    n_sectors : int
        Number of sectors, defaults to 12.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data. Defaults to True.
    seed : int
        Seed for the random data, defaults to 9876538.
    gen_heights : list
        List of generalized heights to use for coordinates
    gen_roughnesses : list
        List of generalized roughnesses to use for coordinates
    wdfreq_constant: bool
        If True, the values of wdfreq do not change with along the dimension
        gen_heights. This is used when writing lib files. Defaults to False.
    kwargs : dict
        Additional arguments.
    Returns
    -------
    ds : xarray.Dataset
        Generalized wind climate dataset either empty or filled with
        random numbers.

    """
    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)

    ds = xr.Dataset(
        {"A": da_dict["da_4d"], "k": da_dict["da_4d"], "wdfreq": da_dict["da_4d"]},
        attrs=unstack_attrs,
    )
    gen_rou_coords = np.array(gen_roughnesses, dtype=float)
    gen_h_coords = np.array(gen_heights, dtype=float)
    n_gen_rou = len(gen_rou_coords)
    n_gen_h = len(gen_h_coords)
    ds = ds.expand_dims(
        {
            "gen_roughness": gen_rou_coords,
        }
    )
    ds["A"] = ds["A"].expand_dims({"gen_height": gen_h_coords})
    ds["k"] = ds["k"].expand_dims({"gen_height": gen_h_coords})
    ds["wdfreq"] = ds["wdfreq"].expand_dims({"gen_height": gen_h_coords})

    n_pt = len(ds["point"])
    if not_empty:
        rng = np.random.default_rng(seed)
        k = rng.uniform(1.5, 2.5, [n_gen_h, n_gen_rou, n_sectors, n_pt])
        A = rng.uniform(5, 10, [n_gen_h, n_gen_rou, n_sectors, n_pt])
        ds["A"] = xr.DataArray(A, ds["A"].coords, ds["A"].dims)
        ds["k"] = xr.DataArray(k, ds["k"].coords, ds["k"].dims)
        ds["wdfreq"] = xr.DataArray(
            rng.dirichlet(np.ones(n_sectors), (n_gen_h, n_gen_rou, n_pt)),
            dims=("gen_height", "gen_roughness", "point", "sector"),
        )
    ds["gen_roughness"].attrs = {**_GEN_COORDS_META["gen_roughness"]}
    ds["gen_height"].attrs = {**_GEN_COORDS_META["gen_height"]}
    ds["sector"].attrs = {**_GEN_COORDS_META["sector"]}

    ustack_ds = _empty_unstack(ds, is_scalar)

    if wdfreq_constant:
        da_wdfreq_constant = ustack_ds.wdfreq.isel(gen_height=0).expand_dims(
            dim={"gen_height": ustack_ds.gen_height.values}
        )
        ustack_ds["wdfreq"] = da_wdfreq_constant

    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _WEIB_ATTRS)
    return _update_history(ds)


@_validate_gwc_wrapper_factory(run_extra_checks=False)
def _lib_string(gwc, /, gen_height=None):
    """Generates string representation of gwc dataset.

    Parameters
    ----------
    gwc: xarray.Dataset
        Dataset containing A, k, and wdfreq.
        Dimensions should be ('gen_height', 'gen_roughness', 'sector')
    gen_height: float
        Value of gen_height to use for saving to libfile. Since libfiles only allow a
        single set of wdfreq values, when your data has varying wdfreq values, you need
        to set this value. It is selected using the .sel selector from xarray.

    Returns
    -------
    str
        String representation of gwc dataset.

    """

    def _fmt_floats(dat, prec=3, extra=False):
        """
        Format a list of floats into a common format

        Parameters
        ----------
        dat: list
            List of floats to be formatted
        prec: int
            Precision of output string
            Default set to 3
        extra: bool
            Extra space between characters
            Default set to False (i.e., no extra space)

        Returns
        -------
        str
            String containing space separated floats
        """

        sep = " " if extra else ""
        fmt = "{0:9.%df}" % prec
        return sep.join([fmt.format(i) for i in dat])

    def _to_string(node):
        """Generates string representation of gwc dataset

        Parameters
        ----------
        node : xarray.Dataset
            Dataset containing A, k, and wdfreq.
            Dimesions should be ('height', 'roughness', 'sector')

        Returns
        -------
        str
            String representation of xarray dataset
        """
        if "height" not in node.coords:
            node = node.expand_dims({"height": [0.0]}).isel(height=0)
        nrough = node.sizes["gen_roughness"]
        nhgt = node.sizes["gen_height"]
        n_sectors = node.sizes["sector"]
        node = reproject(node, 4326).squeeze()
        # Extract numpy arrays to speed up the processing
        A = node.A.values
        k = node.k.values
        wdfreq = node.wdfreq.values
        string = ""
        newline = "\n"

        height = node.height

        # Write the description
        description_without_coord = re.sub(
            "<coordinates>(.*)</coordinates>", "", node.attrs["description"]
        )
        string += (
            description_without_coord
            + f"<coordinates>{float(node.west_east)},{float(node.south_north)},{float(height)}</coordinates>{newline}"
        )

        # Write the dimensions nz0,nz,n_sectors
        string += " ".join([str(i) for i in (nrough, nhgt, n_sectors)]) + newline

        # Write the roughness classes
        string += _fmt_floats(node.gen_roughness.values, 3, True) + newline

        # Write the heights
        string += _fmt_floats(node.gen_height.values, 1, True) + newline

        # Write the data arrays
        for i in range(nrough):
            # sectorwise frequency in percent
            string += _fmt_floats(100.0 * wdfreq[i, ...], 2) + newline
            for j in range(nhgt):
                # Sectorwise A's
                string += _fmt_floats(A[j, i, ...], 2) + newline
                # Sectorwise k's
                string += _fmt_floats(k[j, i, ...]) + newline

        return string

    dims_order = ["gen_height", "gen_roughness", "sector"]

    gwc = gwc.copy()
    gwc = gwc.transpose(*dims_order, ...)

    # if wdfreq varues with height we require users to choose the height
    if _wdfreq_constant_with_gen_height(gwc):
        gwc["wdfreq"] = gwc["wdfreq"].isel(gen_height=0)
    else:
        if gen_height is None:
            raise ValueError(
                "Lib files do not support different 'wdfreq' values for different heights. Please specify the 'gen_height' for the 'wdfreq' values that you wish to use for all levels."
            )
        else:
            gwc["wdfreq"] = gwc["wdfreq"].sel(gen_height=gen_height, method="nearest")

    if gwc.squeeze().A.ndim == 3:
        return _to_string(gwc.squeeze())

    dims_extra = [d for d in gwc.A.dims if d not in dims_order]
    stacked = gwc.stack(point=dims_extra).transpose(*dims_order, "point")
    # Get numbers of sectors, roughness classes and
    strings = []
    for ipt in range(stacked.sizes["point"]):
        # Need the slice to keep the point dimension as multi-index
        node = stacked.isel(point=slice(ipt, ipt + 1)).reset_index("point").squeeze()
        strings.append(_to_string(node))

    return strings


def _wdfreq_constant_with_gen_height(gwc):
    """Check if 'wdfreq' is constant with 'gen_height' dimension.

    Parameters
    ----------
    gwc : xarray.Dataset
        Generalized wind climate dataset.

    Returns
    -------
    bool
        True if 'wdfreq' is constant with 'gen_height' dimension across whole dataset.
    """
    return np.isclose(gwc["wdfreq"].diff(dim="gen_height").max(), 0.0).all()


@_validate_gwc_wrapper_factory(run_extra_checks=False)
def _to_libfile(gwc, /, path=None, gen_height=None):
    """Creates lib-style ascii file from gwc dataset

    Parameters
    ----------
    gwc : xarray.Dataset
        Generalized wind climate dataset.
    path : str
        dir or file path for storing lib file
        Default value set to the current working directory.
    gen_height: float
        Value of gen_height to use for saving to libfile. Since libfiles only allow a
        single set of wdfreq values, when your data has varying wdfreq values, you need
        to set this value. It is selected using the .sel selector from xarray.

    """

    gwc = gwc.copy()

    def _write(node, fpath):
        # Set newline explicitly in string not in open.
        with open(fpath, "w", newline="\r\n") as fobj:
            fobj.write(_lib_string(node, gen_height=gen_height))

    def _fmt_single_point_filename(ds):
        single_point_coords = ["height", "south_north", "west_east"]
        vals = []
        for coord in single_point_coords:
            vals.append(ds[coord].values.flatten()[0])
        filename = f"gwc_height{vals[0]}_south_north{vals[1]}_west_east{vals[2]}.lib"
        return filename

    if path is None:
        path = Path.cwd()
    path = Path(path)

    if path.suffix == "":  # it is a directory
        path.mkdir(parents=True, exist_ok=True)

    if gwc.squeeze().A.ndim == 3:
        if path.is_dir():
            # fpath = path / "gwc.lib"
            fpath = path / _fmt_single_point_filename(gwc)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            fpath = path
        _write(gwc.squeeze(), fpath)
        return

    # If dataset has extra dimensions (of size > 1):
    # Stack extra dimensions, loop over them, and write to tab files
    # Using file_name that contains coordinate information.
    dims_extra = [
        d for d in gwc.A.dims if d not in ["gen_height", "gen_roughness", "sector"]
    ]
    stacked = gwc.stack(point=dims_extra)

    # Create file_name format string
    if Path(path).is_dir():
        file_name_fmt = (
            "_".join(["gwc"] + [f"{d}" + "{" + f"{d}" + "}" for d in dims_extra])
            + ".lib"
        )
    else:
        raise ValueError(
            "'path' argument is a filename, but the dataset has more than one point."
            " Try giving a directory as an argument."
        )

    # Loop and write to tab files
    for ipt in range(stacked.sizes["point"]):
        node = stacked.isel(point=slice(ipt, ipt + 1)).reset_index("point").squeeze()
        kwds = {d: node[d].values for d in dims_extra}
        fpath = path / file_name_fmt.format(**kwds)
        _write(node, fpath)

    return


def gwc_to_file(gwc, filename, *, file_format="infer", **kwargs):
    """
    Write generalized wind climate to file.

    Parameters
    ----------
    gwc : xarray.Dataset
        Generalized wind climate dataset.
    filename : str or Path
        File path to write to.
    file_format : str
        File format to write to. Supported formats are 'lib'.
        Default value is 'infer' which will infer the file format from the file extension.
    kwargs : dict
        Additional arguments to pass to the file writer.

    """
    if file_format == "infer":
        file_format = _infer_file_format(filename)

    if file_format == "lib":
        _to_libfile(gwc, filename, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


def read_gwc(
    filename,
    *,
    crs=None,
    west_east=None,
    south_north=None,
    height=None,
    description=None,
    file_format="infer",
    **kwargs,
):
    """Create gwc xarray.Dataset from file.

    Parameters
    ----------
    file : str or Path
        Path to a file that can be opened a gwc. This includes .lib, and .gwc
        files that were created as gwc files. The script will use the file
        extension to determine the file type and then parse it into a gwc object.
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon on the WGS84 geodetic datum). for .lib and .gwc.
    west_east : float or None, optional
        West-East coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    south_north : float or None, optional
        South-North coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    height : float or None, optional
        Height coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    description : str or None, optional
        Header string to use for .lib and .gwc files, by default None, which will
        attempt to read from the file.
    file_format : str
        File format to read. Supported formats are 'lib', 'gwc', and 'nc'.
        Default value is 'infer' which will infer the file format from the file extension.
    **kwargs : dict

    Returns
    -------
    xarray.Dataset
        Generalized wind climate dataset.

    Raises
    ------
    ValueError
        If the file extension is not recognized.
    ValueError
        If the requested crs does not match the dataset crs.

    """
    if file_format == "infer":
        file_format = _infer_file_format(filename)

    if file_format == "lib":
        ds = _read_lib_file(
            filename,
            crs=crs,
            west_east=west_east,
            south_north=south_north,
            height=height,
            description=description,
        )
    elif file_format in ["gwc"]:
        ds = _read_gwc_file(
            filename,
            crs=crs,
            west_east=west_east,
            south_north=south_north,
            height=height,
            description=description,
        )
    elif file_format in ["nc"]:
        ds = xr.open_dataset(filename, **kwargs)
    else:
        raise ValueError(
            f"Unable to detect type of gwc file {filename} with extension {file_format}."
        )
    validate_gwc(ds)  # Validate for all file types
    ds = _update_var_attrs(ds, _WEIB_ATTRS)
    return _update_history(ds)


def _read_lib_file(
    lib_file, crs=None, west_east=None, south_north=None, height=None, description=None
):
    r"""
    Create GenWindClimate object from WAsP .lib file

    Parameters
    ----------
    lib_file : str, pathlib.Path
        Path to lib file
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon on the WGS84 geodetic datum)
    west_east : float or None, optional
        West-East coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    south_north : float or None, optional
        South-North coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    height : float or None, optional
        Height coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    description : str or None, optional
        Header string to use for .lib and .gwc files, by default None, which will
        attempt to read from the file.

    Returns
    -------
    xr.DataSet
        xarray DataSet that is formatted to match the gwc description

    Raises
    ------
    ValueError
        If coordinates are not present in the file and are not provided as
        arguments.

    Notes
    -----
    Automatically adds lat, lon coords if present inside
    <coordinates>lon,lat,height<\coordinates> brackets
    """

    def _read_float_(f):
        """Reads a line of space separated data and splits it into floats

        Parameters
        ----------
        f : file
            Object with method readline

        Returns
        -------
        list
            List of floats
        """
        return [np.float32(i) for i in f.readline().strip().split()]

    def _read_int_(f):
        """Reads a line of space-separated data and splits it into integers

        Parameters
        ----------
        f : file
            Object with method readline

        Returns
        -------
        list
            List of integers
        """
        return [np.int32(i) for i in f.readline().strip().split()]

    # Open libfile
    with open(lib_file) as f:
        # Read description information one line at a time
        desc = f.readline().strip()  # File Description
        nrough, nhgt, n_sectors = _read_int_(f)  # dimensions
        gen_roughness = _read_float_(f)  # Roughness classes
        gen_height = _read_float_(f)  # heights

        # Initialize arrays
        wdfreq = np.zeros([n_sectors, nrough], dtype="f4", order="F")
        k = np.zeros([n_sectors, nhgt, nrough], dtype="f4", order="F")
        A = np.zeros([n_sectors, nhgt, nrough], dtype="f4")

        ##################################################################
        # The remainder of the file is made up of rows with n_sectors columns.
        # For each height there is first a frequency row, then pairs of
        # A & k rows for each height.
        ##################################################################
        # Loop over roughness classes to read frequency line
        for i, dummy in enumerate(gen_roughness):
            wdfreq[:, i] = _read_float_(f)
            # Loop over heights to read in all A & k values
            for j, dummy in enumerate(gen_height):
                A[:, j, i] = _read_float_(f)
                k[:, j, i] = _read_float_(f)

    if crs is None:
        crs = "EPSG:4326"

    # Find the coordinates if they aren't provided
    if all(c is None for c in [west_east, south_north, height]):
        # Find the coordinates
        latlons = re.search("<coordinates>(.*)</coordinates>", desc)
        if latlons:
            west_east, south_north, height = map(
                np.float32, latlons.group(1).split(",")
            )
        else:
            raise ValueError(
                f"Coordinates not found in {lib_file}, "
                + "please set 'west_east', 'south_north', and 'height' explicitly. "
                + "These values should ge in the projection given by the 'crs' argument,"
                + " which defaults to the WGS84 projection."
            )

    if description is None:
        if len(desc) > 0:
            description = desc
        else:
            description = ""

    # Add height to wdfreq
    wdfreq = np.tile(wdfreq[:, np.newaxis, :], (1, nhgt, 1))

    return _weibull_to_dataset(
        wdfreq,
        A,
        k,
        gen_roughness,
        gen_height,
        south_north,
        west_east,
        height,
        crs,
        description=description,
    )


def _weibull_to_dataset(
    wdfreq,
    A,
    k,
    gen_roughness,
    gen_height,
    south_north,
    west_east,
    height,
    crs,
    **kwargs,
):
    """
    Converts parsed xml gwc object to WindKit gwc xarray dataset

    Parameters
    ----------
    wdfreq : 1-D sequence of floats
        Wind direction frequencies. Dimensions=[sector, gen_height, gen_roughnness]
    A : numpy
        Weibull A parameters.  Dimensions=[sector, gen_height, gen_roughnness]
    k : numpy
        Weibull k parameters.  Dimensions=[sector, gen_height, gen_roughnness]
    gen_roughness : numpy
        Array of generalized roughnesses
    gen_height : numpy
        Array of generalized heights
    west_east : float or None, optional
        West-East coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    south_north : float or None, optional
        South-North coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    height : float or None, optional
        Height coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon on the WGS84 geodetic datum)

    kwargs : dict, optional
        Other key-word arguments are added as attributes to the dataset.

    Returns
    -------
    xarray.Dataset
        WindKit GWC dataset
    """

    n_sectors, _, _ = wdfreq.shape

    na = np.newaxis

    # Create dataset
    ds = create_dataset(west_east, south_north, height, crs).drop_vars("output")
    ds.attrs = kwargs

    # Add variables
    dims = ("sector", "gen_height", "gen_roughness", "point")
    ds["A"] = (dims, A[..., na])
    ds["k"] = (dims, k[..., na])
    ds["wdfreq"] = (dims, wdfreq[..., na])

    # Add coordinates
    ds = ds.assign_coords(
        {
            **_create_coords(gen_height, "gen_height", _GEN_COORDS_META).coords,
            **_create_coords(gen_roughness, "gen_roughness", _GEN_COORDS_META).coords,
            **create_sector_coords(n_sectors).coords,
        }
    )

    ds["wdfreq"] = ds["wdfreq"] / ds["wdfreq"].sum(dim="sector")

    return ds.transpose("gen_height", "gen_roughness", "sector", "point")


def _read_gwc_file(
    gwc_file,
    crs=None,
    west_east=None,
    south_north=None,
    height=None,
    description=None,
):
    """Read Generalized Wind Climate from XML-based .gwc file.

    Parameters
    ----------
    gwc_file : str, pathlib.Path
        input file
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon on the WGS84 geodetic datum)
    west_east : float or None, optional
        West-East coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    south_north : float or None, optional
        South-North coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    height : float or None, optional
        Height coordinate of the GWC grid, by default None, which will attempt to
        read from the file.
    description : str or None, optional
        Header string to use for .lib and .gwc files, by default None, which will
        attempt to read from the file.

    Returns
    -------
    xarray.Dataset
        WindKit GWC dataset

    Raises
    ------
    ValueError
        If no RveaGeneralisedMeanWindClimate is found in the file.
    ValueError
        If coordinates are not found in the file and are not provided explicitly.

    Warns
    -----
    UserWarning
        If 'height' is not found in the file and are not provided explicitly.
        It will be set to 0.0

    """

    if crs is None:
        crs = "EPSG:4326"

    tree = etree.parse(str(gwc_file))
    root = tree.getroot()

    descendants = list(e.tag for e in root.getiterator())

    if root.tag == "RveaGeneralisedMeanWindClimate":
        gwc_tree = root
    elif "RveaGeneralisedMeanWindClimate" in descendants:
        gwc_tree = tree.find(".//RveaGeneralisedMeanWindClimate")
    else:
        raise ValueError(f"No RveaGeneralisedMeanWindClimate found in '{gwc_file}'")

    gwc_data = _parse_rvea_generalised_mean_wind_climate(gwc_tree)

    if "RveaAnemometerSiteDetails" in descendants:
        site_data = _parse_rvea_anemometer_site_details(
            tree.find(".//RveaAnemometerSiteDetails")
        )
    else:
        site_data = {}

    if west_east is None:
        west_east = gwc_data.get("longitude", site_data.get("longitude", None))

    if south_north is None:
        south_north = gwc_data.get("latitude", site_data.get("latitude", None))

    if height is None:
        height = gwc_data.get("height", site_data.get("height", None))

    if description is None:
        description = gwc_data.get("description", site_data.get("description", ""))

    if west_east is None or south_north is None:
        raise ValueError(
            "'west_east' or 'south_north' coordinate not found in file or provided as argument. "
            + "Please set 'west_east' and 'south_north' explicitly."
        )

    if height is None:
        height = 0.0
        warnings.warn(
            "No height found in file or provided as argument, using 0 m. Set 'height' explicitly to avoid this warning.",
        )

    return _weibull_to_dataset(
        wdfreq=gwc_data["wdfreq"],
        A=gwc_data["A"],
        k=gwc_data["k"],
        gen_roughness=gwc_data["gen_roughness"],
        gen_height=gwc_data["gen_height"],
        west_east=west_east,
        south_north=south_north,
        height=height,
        crs=crs,
        description=description,
    )


@_validate_gwc_wrapper_factory(run_extra_checks=False)
def _reproject_gwc(gwc, /, to_crs):
    """Reprojects Generalized wind climate dataset.

    Parameters
    ----------
    gwc: xarray.Dataset
        Valid GWC dataset.
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`

    Returns
    -------
    xarray.Dataset
        Point based generalized wind climate dataset in new projection.
    """
    if not crs_are_equal(gwc, to_crs):
        return reproject(gwc, to_crs)

    # Return point based dataset even if not reprojected
    ds = to_point(gwc)
    return _update_history(ds)


def _mean_ws_moment(gwc, moment=1, **kwargs):
    """Calculates mean wind speed moment from generalized wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")


def _ws_cdf(gwc, **kwargs):
    """Calculates wind speed cumulative distribution function from generalized wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")


def _ws_freq_gt_mean(gwc, **kwargs):
    """Calculates wind speed frequency greater than mean from generalized wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")


def _mean_wind_speed(gwc, **kwargs):
    """Calculates mean wind speed from generalized wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")


def _mean_power_density(gwc, **kwargs):
    """Calculates mean power density from generalized wind climate dataset."""
    raise NotImplementedError("This function is not yet implemented.")
