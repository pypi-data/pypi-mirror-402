# (c) 2022 DTU Wind Energy
"""Binned wind climate module

When measuring the wind speed and wind direction over a time period, one can
create a histogram by counting the frequency of occurence for each
wind speed and direction bin.

Because there can be large differences in the wind climate when the wind is
coming from different wind directions, a binned wind distribution is usually
specified per wind direction sector.

A valid Weibull wind climate therefore has a dimension ``sector`` and the variables
``wsbin`` and ``wdfreq``. Also it must have a valid spatial structure. This module contains
functions that operate on and create binned wind climates.
This includes the ability to create bwc datasets both from files and from
existing data, the ability to calculate common parameters from the bwc object,
and the ability to write them to the legacy *.tab* format.
"""

__all__ = [
    "validate_bwc",
    "is_bwc",
    "create_bwc",
    "read_bwc",
    "bwc_from_tswc",
    "bwc_to_file",
    "combine_bwcs",
    "weibull_fit",
]

import logging
import warnings
from functools import wraps
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from lxml import etree

from windkit import weibull
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
    _HIS_ATTRS,
    _WEIB_ATTRS,
    _WSBIN_COORD_ATTRS,
    _update_history,
    _update_var_attrs,
)
from windkit.xarray_structures.sector import (
    create_sector_coords,
)
from windkit.xarray_structures.wsbin import (
    create_wsbin_coords,
)
from windkit.spatial import (
    create_dataset,
    get_crs,
    is_point,
    _spatial_stack,
    _spatial_unstack,
    to_point,
)
from windkit.utils import _infer_file_format
from windkit.wind import wd_to_sector
from windkit.wind_climate.time_series_wind_climate import _validate_tswc_wrapper_factory

logger = logging.getLogger(__name__)

SUPPORTED_BWC_FILE_FORMATS_READ = ["tab", "owc", "omwc", "nc"]
SUPPORTED_BWC_FILE_FORMATS_WRITE = ["tab"]

WS = "wind_speed"
WD = "wind_direction"
VAR_WS_FREQ = "ws_freq"
VAR_WD_FREQ = "wdfreq"
VAR_WS_FREQ_BY_SECTOR = "wsfreq"
DIM_TIME = "time"
DIM_WS = "wsbin"
DIM_WD = "sector"
WV_COUNT = "wv_count"
DATA_VAR_DICT_BWC = {"wsfreq": ["wsbin", "sector"], "wdfreq": ["sector"]}
REQ_DIMS_BWC = ["wsbin", "sector"]
REQ_COORDS_BWC = [
    "sector",
]


def _validate_freqs_greater_than_zero(wwc):
    """Helper function to validate wdfreq and wsfreq are positive"""
    response_list = []

    if "wsfreq" in wwc.data_vars and any(
        xr.where(wwc.wsfreq.values < 0.0, True, False).flatten()
    ):
        response_list.append("'wsfreq' has negative values")

    if "wdfreq" in wwc.data_vars and any(
        xr.where(wwc.wdfreq.values < 0.0, True, False).flatten()
    ):
        response_list.append("'wdfreq' has negative values")

    return response_list


validate_bwc = _create_validator(
    variables=DATA_VAR_DICT_BWC,
    dims=REQ_DIMS_BWC,
    coords=REQ_COORDS_BWC,
    extra_checks=[_validate_freqs_greater_than_zero],
)

_validate_bwc_wrapper_factory = _create_validation_wrapper_factory(validate_bwc)

is_bwc = _create_is_obj_function(validate_bwc)


def _wv_count_wrapper(func):
    """
    Decorator to handle wind vector count format.

    Handles the case where the parameter is an xarray.DataArray with a wv_count
    format or a xarray.Dataset with a 'wv_count' data variable, i.e. has wind
    counts by bin and sector. If so, returns a binned wind climate xarray.Dataset.
    If it is not the case, it does nothing.
    """

    @wraps(func)
    def wv_count_to_bwc(*args, **kwargs):
        obj = args[0]
        try:
            # handles the case of a xarray.Dataset
            obj = obj["wv_count"]
        except KeyError:
            pass
        if isinstance(obj, xr.DataArray) and obj.name == "wv_count":
            bwc = _bwc_from_counts(obj)
            result = func(bwc, *args[1:], **kwargs)
        else:
            result = func(*args, **kwargs)
        return result

    return wv_count_to_bwc


def _freqs_to_dataset(
    wsfreq,
    wdfreq,
    wsbins,
    south_north,
    west_east,
    height,
    crs,
    **kwargs,
):
    """
    Makes data variables, coordinates, and attributes ready for
    xarray.Dataset construction from a histogram of wind speeds and directions

    Parameters
    ----------
    wsfreq: np.array([n_wsbins, n_sectors]): float64
        Wind speed frequency by wind speed and sector
    wdfreq: np.array([n_sectors]): float64
        Wind direction frequency by sector
    wsbins: np.array([n_wsbins + 1]): float64
        Edges of wind speed bins
    south_north: float64
        Coordinate value in y-direction
    west_east: float64
        Coordinate value in x-direction
    height: float64
        Height above ground
    crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`
    kwargs : dict
        Other kwargs are added as attributes to the dataset

    Returns
    -------
    xarray.Dataset
    """

    wsbins = np.asarray(wsbins, dtype=np.float64)

    _, n_sectors = wsfreq.shape

    wscenters = create_wsbin_coords(wsbins)
    wdcenters = create_sector_coords(n_sectors)

    na = np.newaxis

    wdfreq /= np.sum(wdfreq)
    with np.errstate(all="ignore"):
        wsfreq = wsfreq / np.sum(wsfreq, axis=0)[na, :]
    if np.isnan(wsfreq).any():
        logging.debug(
            "There are sectors with no wind observations (nan), which will be set to 0.0."
        )
        wsfreq = np.nan_to_num(wsfreq)

    # Build dataset
    ds = create_dataset(west_east, south_north, height, crs).drop_vars("output")
    ds["wdfreq"] = (("sector", "point"), wdfreq[:, na])
    ds["wsfreq"] = (("wsbin", "sector", "point"), wsfreq[:, :, na])

    ds = ds.assign_coords(
        {
            **wscenters.coords,
            **wdcenters.coords,
        }
    )

    ds = ds.assign_attrs(kwargs)

    ds = _update_var_attrs(ds, _BWC_ATTRS)
    return _update_history(ds)


def create_bwc(output_locs, n_sectors=12, n_wsbins=30, not_empty=True, seed=9876538):
    """
    Create empty binned wind climate dataset.

    If not_empty=True, the data variables are filled with meaninful random numbers,
    e.g. the sum of wdfreq is 1.

    Parameters
    ----------
    output_loc : xarray.Dataset
        Output geospatial information.
    n_sectors : int
        Number of sectors, defaults to 12.
    n_wsbins: int
        Number of histogram bins, defaults to 30.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data.
    seed : int
        Seed for the random data, defaults to 9876538.

    Returns
    -------
    ds : xarray.Dataset
        Binned wind climate dataset either empty or filled with
        random numbers.
    """

    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)
    ds = xr.Dataset(
        {"wdfreq": da_dict["da_4d"], "wsfreq": da_dict["da_4d"]}, attrs=unstack_attrs
    )
    wsbin_coords = create_wsbin_coords(n_wsbins, width=1.0)

    ds["wsfreq"] = ds["wsfreq"].expand_dims({"wsbin": wsbin_coords.values})
    ds = ds.assign_coords({**wsbin_coords.coords})
    n_pt = len(ds["point"])

    if not_empty:
        import scipy.stats

        wsbin_n = np.linspace(1, n_wsbins, n_wsbins)
        rng = np.random.default_rng(seed)
        wsbin_full = wsbin_n.repeat(n_sectors * n_pt).reshape(
            (n_wsbins, n_sectors, n_pt)
        )
        k = rng.uniform(1.5, 2.5, [n_sectors, n_pt])
        A = rng.uniform(5, 10, [n_sectors, n_pt])
        wsbin_freq_not1 = scipy.stats.weibull_min.pdf(wsbin_full, k, scale=A)
        wsbin_freq = wsbin_freq_not1 / wsbin_freq_not1.sum(0)

        ds["wsfreq"] = xr.DataArray(wsbin_freq, ds["wsfreq"].coords, ds["wsfreq"].sizes)
        ds["wdfreq"] = xr.DataArray(
            rng.dirichlet(np.ones(n_sectors), n_pt).T,
            ds["wdfreq"].coords,
            ds["wdfreq"].sizes,
        )

    ustack_ds = _empty_unstack(ds, is_scalar)
    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _BWC_ATTRS)

    return _update_history(ds)


def _create_wv_count(
    output_locs, n_sectors=12, n_wsbins=30, not_empty=True, seed=9876538
):
    """
    Create empty wind vector count dataset.
    If not_empty=True, the data variables are filled with meaninful random numbers.

    Parameters
    ----------
    output_loc : xarray.Dataset
        Output geospatial information
    n_sectors : int
        Number of sectors, defaults to 12.
    not_empty : bool
        If true, the empty dataset is filled with random
        meaningful data, defaults to True.
    seed : int
        Seed for the random data, defaults to 9876538.

    Returns
    -------
    ds : xarray.Dataset
        Wind vector count dataset either empty or filled with
        random numbers.
    """
    da_dict, unstack_attrs, is_scalar = _define_std_arrays(output_locs, n_sectors)
    ds = xr.Dataset({"wv_count": da_dict["da_4d"]}, attrs=unstack_attrs)
    wsbin_coords = create_wsbin_coords(n_wsbins, width=1.0)

    ds["wv_count"] = ds["wv_count"].expand_dims({"wsbin": wsbin_coords.values})
    ds = ds.assign_coords({**wsbin_coords.coords})
    n_pt = len(ds["point"])

    if not_empty:
        import scipy.stats

        rng = np.random.default_rng(seed)
        k = rng.uniform(1.5, 2.5, [n_sectors, n_pt])
        A = rng.uniform(5, 10, [n_sectors, n_pt])
        wsbin_n = np.linspace(1, n_wsbins, n_wsbins)
        wsbin_full = wsbin_n.repeat(n_sectors * n_pt).reshape(
            (n_wsbins, n_sectors, n_pt)
        )
        scaling_fact = rng.uniform(500, 1000, [n_sectors, n_pt])
        wv_count_array = np.rint(
            np.multiply(
                scipy.stats.weibull_min.pdf(wsbin_full, k, scale=A),
                scaling_fact[np.newaxis, :, :],
            )
        )
        ds["wv_count"].values = wv_count_array

    ustack_ds = _empty_unstack(ds, is_scalar)
    ds = _update_var_attrs(_copy_chunks(output_locs, ustack_ds), _HIS_ATTRS)

    return _update_history(ds)


def read_bwc(filename, *, crs=None, file_format="infer", **kwargs):
    """Creates binned wind climate xarray.Dataset from file.

    Parameters
    ----------
    filename : str or Path
        Path to a file that can be opened as a bwc. This includes .tab, .owc,
        .omwc, and .nc that were created as bwc files. The script will
        use the file extension to determine the file type and then parse it
        into a bwc DataSet object.
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon/WGS84 geodetic datum) for .tab, .owc and .omwc files.
    file_format : str
        The file format of the input file. If 'infer', the file format will be inferred from the file extension.
        Supported formats are 'tab', 'owc', and 'omwc'. Defaults to 'infer'.
    **kwargs : dict
        Additional arguments to be passed to the file reader.

    Returns
    -------
    ds : xarray.Dataset
        binned wind climate dataset that is formatted to match the bwc description.

    Raises
    ------
    ValueError
        If crs does not match dataset crs.
    ValueError
        If type of bwc is undetectable.
    """
    if file_format == "infer":
        file_format = _infer_file_format(filename)

    if file_format == "tab":
        if crs is None:
            crs = 4326
        bwc = _open_tabfile(filename, crs, **kwargs)
    elif file_format in ["owc", "omwc"]:
        if crs is None:
            crs = 4326
        bwc = _open_owcfile(str(filename), crs, **kwargs)
    elif file_format == "nc":
        bwc = xr.open_dataset(filename, **kwargs)
    else:
        raise ValueError(
            f"Unable to detect type of bwc file {filename} with extension {file_format}"
        )
    validate_bwc(bwc, run_extra_checks=False)
    bwc = _update_var_attrs(bwc, _BWC_ATTRS)
    return _update_history(bwc)


def combine_bwcs(bwc_list):
    """Combines a list of bwc's into one binned wind climate.

    .. note:: The output is always an object with a point structure

    Parameters
    ----------
    bwc_list: list
        List of binned wind climate xarray.Dataset.

    Returns
    -------
    bwcs: xarray.Dataset
        xarray Dataset with merged binned wind climates.
    """
    max_bins = max([bwc.sizes["wsbin"] for bwc in bwc_list])
    filled_bwcs = []
    for bwc in bwc_list:
        if not is_point(bwc):
            bwc = to_point(bwc)
        filled_bwcs.append(_fill_wsbin(bwc, max_bins))

    bwcs = xr.concat(filled_bwcs, "point")
    return _update_history(bwcs)


def _open_tabfile(tab_file, crs=4326):
    """Creates bwc object from a "tab" ascii file

    Parameters
    ----------
    tab_file: str
        Path to file tab file
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon/WGS84 geodetic datum)

    Returns
    -------
    xr.DataSet
        xarray DataSet that is formatted to match the bwc description

    Raises
    ------
    ValueError
        If .tab file does not have appropriate string formatting
    """

    def _read_floats(fobj):
        return map(float, fobj.readline().split())

    def _load_tabfile(tab_file, encode):
        with open(tab_file, encoding=encode) as fobj:
            header = fobj.readline().strip()
            south_north, west_east, height = _read_floats(fobj)
            tuple_header = tuple(_read_floats(fobj))
            if len(tuple_header) == 4:
                n_sectors, _, _, tabfile_type = tuple_header
                if tabfile_type != 0:
                    raise ValueError(
                        "Tabfiles of type {0} are not supported".format(tabfile_type)
                    )
            else:
                n_sectors, _, _ = tuple_header
            n_sectors = int(n_sectors)

            wd_freq = np.array(list(_read_floats(fobj)))
            wsdata = np.genfromtxt(fobj)

        kwargs = {
            "south_north": south_north,
            "west_east": west_east,
            "height": height,
            "description": header,
            "crs": crs,
        }

        return kwargs, wd_freq, wsdata

    try:
        kwargs, wd_freq, wsdata = _load_tabfile(tab_file, "ascii")
    except (UnicodeDecodeError, UnicodeError):
        try:
            kwargs, wd_freq, wsdata = _load_tabfile(tab_file, "utf_8")
        except (UnicodeDecodeError, UnicodeError):
            try:
                kwargs, wd_freq, wsdata = _load_tabfile(tab_file, "utf_16")
            except (UnicodeDecodeError, UnicodeError):
                try:
                    kwargs, wd_freq, wsdata = _load_tabfile(tab_file, "cp1256")
                except (UnicodeDecodeError, UnicodeError):
                    raise ValueError(
                        "Unknown encoding for .tab file, please save as ASCII or UTF-8"
                    )

    ws_freq = wsdata[:, 1:]
    ws_bins = np.append(0, wsdata[:, 0])

    return _freqs_to_dataset(ws_freq, wd_freq, ws_bins, **kwargs)


def _parse_owc(owc, crs=4326):
    """
    Parses an OWC file into a bwc object

    Parameters
    ----------
    owc : xml tree
        An XML element loaded by lxml
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon/WGS84 geodetic datum)

    Returns
    -------
    xr.DataSet
        xarray DataSet that is formatted to match the bwc description
    """
    # Get main dimensions
    num_sec = int(owc.attrib["CountOfSectors"])
    num_wsbins = int(
        owc.xpath("ObservedWind[1]/SpeedFrequencyDistribution" + "/@NumberOfBins")[0]
    )

    # Create arrays
    ws_freq = np.zeros((num_wsbins, num_sec))
    wd_freq = np.zeros(num_sec)
    cen_angle = np.zeros(num_sec)
    ws_bins = np.zeros(num_wsbins)

    # Get site information
    site_info = owc.xpath("RveaAnemometerSiteDetails")[0].attrib
    lat = float(site_info["LatitudeDegrees"])
    lon = float(site_info["LongitudeDegrees"])
    height = float(site_info["HeightAGL"])
    header = site_info["Description"]

    # Get wind speed histogram
    for obsWind in owc.xpath("ObservedWind"):
        # Get sector information
        sec = int(obsWind.attrib["Index"]) - 1
        cen_angle[sec] = float(obsWind.attrib["SectorWidthDegrees"])
        wd_freq[sec] = float(obsWind.attrib["SectorFrequency"])

        # Get wind speed histogram
        for wsBin, ws in enumerate(obsWind.getchildren()[0]):
            ws_bins[wsBin] = float(ws.attrib["UpperSpeedBound"])
            ws_freq[wsBin, sec] = float(ws.attrib["Frequency"])

    # Extract 1st column which is wind speeds and
    # add a 0.0 value to the first position
    ws_bins = np.insert(ws_bins, 0, 0.0)

    kwargs = {
        "south_north": lat,
        "west_east": lon,
        "height": height,
        "description": header,
        "crs": crs,
    }

    return _freqs_to_dataset(ws_freq, wd_freq, ws_bins, **kwargs)


def _open_owcfile(xml_file, crs=4326):
    """Creates bwc object from a .owc xml file

    Parameters
    ----------
    n: xml_file
        Path to xml file
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS`
        Defaults to 4326 (Lat-Lon/WGS84 geodetic datum)

    Returns
    -------
    bwc
    """
    tree = etree.parse(str(xml_file))
    root = tree.getroot()
    return _parse_owc(root, crs)


def _count_to_wd_freq(wind_hist):
    """Convert wind vector count histogram to wind sector-wise relative frequency.

    Parameters
    ----------
    wind_hist : xarray.DataArray
        A valid pywasp wind-vector-count histogram DataArray


    Returns
    -------
    relfreq : xarray.DataArray
        Data array with sectorwise relative frequencies.
    """
    relfreq = wind_hist.sum(dim=[DIM_WS], skipna=False) / wind_hist.sum(
        dim=[DIM_WS] + [DIM_WD], skipna=False
    )
    relfreq.name = VAR_WD_FREQ
    return _update_var_attrs(relfreq, _BWC_ATTRS)


def _count_to_ws_freq_by_sector(wind_hist):
    """DEPRECATED, use windkit.bwc_from_counts instead"""
    warnings.warn(
        "The 'count_to_ws_freq_by_sector' function is renamed as 'bwc_from_counts' and will be removed in a future version. "
        + "Use 'bwc_from_counts' instead.",
        FutureWarning,
        stacklevel=2,
    )
    return _bwc_from_counts(wind_hist)


def _bwc_from_counts(wind_hist):
    """Convert wind vector count histogram to binned wind climate dataset.

    Parameters
    ----------
    wind_hist : xarray.DataArray
        A valid pywasp wind-vector-count histogram DataArray


    Returns
    -------
    relfreq : xarray.Dataset
        Dataset with wind speed frequencies
        normalized in each sector and the rel.
        frequency of occurance of wind direction.
    """
    if isinstance(wind_hist, xr.Dataset):
        wind_hist = wind_hist[WV_COUNT]

    original_dim_order = list(wind_hist.sizes.keys())

    ds = xr.Dataset()
    wsfreq = wind_hist / wind_hist.sum(dim=DIM_WS, skipna=False)
    ds[VAR_WD_FREQ] = _count_to_wd_freq(wind_hist)
    ds.attrs.update(wind_hist.attrs)
    # sectors with zero frequencies result in nans
    # point which have some probability mass in some sectors
    # but not all, are manually set to 0.0
    point_not_empty = wsfreq.sum([DIM_WD, DIM_WS]) > 0

    ds[VAR_WS_FREQ_BY_SECTOR] = wsfreq.where(~(point_not_empty & wsfreq.isnull()), 0.0)
    ds = ds.transpose(*original_dim_order)

    ds = _update_var_attrs(ds, _BWC_ATTRS)
    return _update_history(ds)


@_validate_tswc_wrapper_factory(run_extra_checks=False)
def bwc_from_tswc(
    ts, wsbin_width=1.0, n_wsbins=30, n_sectors=12, normalize=True, **kwargs
):
    """Creates object from a timeseries.

    Parameters
    ----------
    ts : xarray.Dataset
        Xarray dataset with variables 'wind_speed'
        and 'wind_direction' and with a coordinate and
        dimension 'time'.
    wsbin_width: float
        Width of the wind speed bins, defaults to 1.0.
    n_wsbins : int
        Number of wind speed bins, defaults to 30.
    n_sectors : int
        Number of sectors, defaults to 12.
    normalize : bool
        If set to True, convert wind vector count histogram to
        wind sector-wise relative frequency. Defaults to True
    kwargs: dict
        Additional argument 'wasp_desription' can be added to the dataset.

    Returns
    -------
    bwc : xarray.Dataset
        Binned wind climate from the timeseries.
    """

    def point_histogram2d(ws, wd, bins):
        hist, _, _ = np.histogram2d(ws, wd, bins=bins)
        hist_no_nan = np.nan_to_num(hist)

        return hist_no_nan

    # stack windkit dataset to point
    ds = _spatial_stack(ts)
    ds_attrs = {
        "description": kwargs.get("wasp_desription", ""),
        **_create_time_attributes(ds),
    }
    # ignore times when any of the time series is not available
    ds = ds.dropna(dim=DIM_TIME)
    if ds.sizes["time"] < 1:
        raise ValueError("Need at least 1 sample to create a histogram")

    ws_bins = create_wsbin_coords(n_wsbins, width=wsbin_width)
    wd_bins = create_sector_coords(n_sectors)
    ws_bin_edges = np.append(0.0, ws_bins["wsceil"].values)

    # convert wdir to sectors
    # wd, wd_sec = dir_to_sec(ds[WD], n_sectors)
    (
        wd,
        _,
    ) = wd_to_sector(ds[WD], n_sectors, output_type="indices")
    ds["wd_bins"] = (ds[WD].dims, wd.data)
    bins = (ws_bin_edges, np.arange(n_sectors + 1))

    hist = xr.apply_ufunc(
        point_histogram2d,
        ds["wind_speed"],
        ds["wd_bins"],
        dask="allowed",
        vectorize=True,
        input_core_dims=[["time"], ["time"]],
        output_core_dims=[["wsbin", "sector"]],
        kwargs={"bins": bins},
        keep_attrs=True,
    )

    hist.name = WV_COUNT
    hist = hist.assign_coords({**ws_bins.coords, **wd_bins.coords})

    if normalize:
        hist = _bwc_from_counts(hist)
    else:
        hist = _update_var_attrs(hist.to_dataset(), _BWC_ATTRS)

    if "_pwio_data_is_2d" in ds["wind_speed"].attrs:
        for var in hist.data_vars:
            hist[var].attrs["_pwio_data_is_2d"] = ds["wind_speed"].attrs[
                "_pwio_data_is_2d"
            ]

        if "_pwio_data_is_2d" in hist.attrs:
            del hist.attrs["_pwio_data_is_2d"]

    # the _pwio_was_stacked_point attribute is lost with apply_ufunc
    hist.attrs.update(ds.attrs)

    hist = hist.assign_attrs(ds_attrs)
    hist = _spatial_unstack(hist)

    return _update_var_attrs(_spatial_unstack(hist), _BWC_ATTRS)


@_validate_tswc_wrapper_factory(run_extra_checks=False)
def _create_time_attributes(ds: xr.Dataset, hist=None):
    """Create time attributes for binned wind climate.

    We attached the time attributes to a new or existing
    binned wind climate. If it has existing attributes, these
    will be used as well when calculating the meta data.

    Parameters
    ----------
    ds : xarray.Dataset
        Xarray dataset with variables 'wind_speed'
        and 'wind_direction' and with a coordinate and
        dimension 'time'.
    hist : xarray.Dataset, optional
        A valid pywasp histogram dataset with, defaults to None

    Returns
    -------
    dic_result: dict
        Dictionary with 'start_time', 'end_time', 'interval',
        'count', 'count_missing', 'recovering_percentage'
    """
    # find the first and last time in the time series we process
    first_time = pd.Timestamp(ds["time"].min().values)
    last_time = pd.Timestamp(ds["time"].max().values)
    number_of_samples = int(ds.dropna(dim="time").sizes["time"])
    # find most frequent interval in minutes
    # currently when you provide an existing histogram
    # as input it will just overwrite the sampling interval
    # and recovery percentage. Since we only process model
    # data this way, it is probably OK for now.
    intervals, counts = np.unique(
        ds["time"].diff("time") / pd.Timedelta("1 ms"), return_counts=True
    )
    interval = intervals[counts.argmax()]
    series_start_to_end = np.arange(
        first_time, last_time, pd.Timedelta(f"{interval} ms")
    )
    # arange does not include the last step but we want
    # this for the max samples
    max_possible_samples = int(series_start_to_end.size + 1)

    # check for existing first and last time in input
    # it is assumed that this histogram has also been created
    # with this function and the attributes should be present
    try:
        first_time = np.min([first_time, pd.to_datetime(hist.attrs["start_time"])])
        last_time = np.max([last_time, pd.to_datetime(hist.attrs["end_time"])])
        max_possible_samples = max_possible_samples + hist.attrs["count_expected"]
        number_of_samples = number_of_samples + hist.attrs["count"]
    except (KeyError, AttributeError) as e:  # noqa
        logging.info("No attributes present yet, adding new ones.")

    dic_result = {
        "start_time": str(first_time),
        "end_time": str(last_time),
        "interval": str(pd.Timedelta(f"{interval} ms")),
        "count_expected": max_possible_samples,
        "count": number_of_samples,
        "count_missing": max_possible_samples - number_of_samples,
        "recovery_percentage": 100 * number_of_samples / max_possible_samples,
    }

    return dic_result


def _tab_string(bwc):
    """Returns string representation of bwc dataset

    Parameters
    ----------
    bwc: xr.Dataset
        Binned wind climate xr.Dataset object

    Returns
    -------
    string: str
        String representation of bwc dataset
    """

    def _to_string(node):
        nwsbin = node.sizes["wsbin"]
        n_sectors = node.sizes["sector"]

        le = "\n"

        header_str = node.attrs.get("description", "No Header")
        string = header_str + le

        string += (
            "\t".join(
                map(
                    str,
                    [
                        node["south_north"].values,
                        node["west_east"].values,
                        node["height"].values,
                    ],
                )
            )
            + le
        )

        string += "\t".join(map(str, [n_sectors, 1.0, 0.0])) + le

        string += "    \t" + "\t".join("%6.2f" % f for f in node.wdfreq * 100.0) + le

        wsfreq = np.round(node.wsfreq.values * 1000.0, 3)

        for iws in range(nwsbin):
            string += "%4.1f" % node.wsceil.values[iws] + "\t"
            string += "\t".join("%6.2f" % f for f in wsfreq[iws, :])
            if iws < nwsbin - 1:
                string += le

        return string

    return _to_string(bwc.squeeze())


@_wv_count_wrapper
def _to_tabfile(bwc, /, path=None):
    """Write bwc to tab-style ascii file.

    Parameters
    ----------
    bwc: xr.Dataset
        Binned wind climate xr.Dataset object.

    path: str or pathlib.Path
        dir or file path to write the file. Default value set
        to the current working directory.

    """

    def _write(node, fpath):
        with open(fpath, "w", newline="\r\n") as fobj:
            fobj.write(_tab_string(node))

    def _fmt_single_point_filename(ds):
        single_point_coords = ["height", "south_north", "west_east"]
        vals = []
        for coord in single_point_coords:
            vals.append(ds[coord].values.flatten()[0])
        filename = f"bwc_height{vals[0]}_south_north{vals[1]}_west_east{vals[2]}.tab"
        return filename

    if not get_crs(bwc).is_geographic:
        raise RuntimeError(
            "Binned wind climate dataset with projected coordinate systems cannot be written to a '.tab' file."
        )

    if path is None:
        path = Path.cwd()
    path = Path(path)
    if path.suffix == "":  # it is a Directory
        path.mkdir(parents=True, exist_ok=True)

    # If dataset has no extra dimensions (larger than  size=1):
    # write file and return early.
    if bwc.squeeze().wsfreq.ndim == 2:
        if Path(path).is_dir():
            # fpath = path / "bwc.tab"
            fpath = path / _fmt_single_point_filename(bwc)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            fpath = path
        _write(bwc.squeeze(), fpath)
        return

    # If dataset has extra dimensions (of size > 1):
    # Stack extra dimensions, loop over them, and write to tab files
    # Using file_name that contains coordinate information.
    dims_extra = [d for d in bwc.wsfreq.dims if d not in ["wsbin", "sector"]]
    stacked = bwc.stack(point=dims_extra)

    # Create file_name format string
    if Path(path).is_dir():
        file_name_fmt = (
            "_".join(["bwc"] + [f"{d}" + "{" + f"{d}" + "}" for d in dims_extra])
            + ".tab"
        )
    else:
        raise ValueError(
            "'path' argument is a filename, but the dataset has more than one point."
            " Try giving a directory as an argument."
        )

    # Loop and write to tab files
    for ipt in range(stacked.sizes["point"]):
        node = stacked.isel(point=slice(ipt, ipt + 1)).reset_index("point").squeeze()
        kw = {d: node[d].values for d in dims_extra}
        fpath = path / file_name_fmt.format(**kw)
        _write(node, fpath)

    return


@_validate_bwc_wrapper_factory(run_extra_checks=False)
def bwc_to_file(bwc, filename, *, file_format="infer", **kwargs):
    """Write binned wind climate to file.

    Parameters
    ----------
    bwc: xr.Dataset
        Binned wind climate xr.Dataset object.
    filename: str or pathlib.Path
        Path to the file to write the binned wind climate to.
    file_format: str
        The file format of the output file. If 'infer', the file format will be inferred from the file extension.
        Supported formats are 'tab'. Defaults to 'infer'.
    **kwargs: dict
        Additional keyword arguments to pass to the writing function.
    """
    if file_format == "infer":
        file_format = _infer_file_format(filename)

    if file_format == "tab":
        _to_tabfile(bwc, filename, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")


@_wv_count_wrapper
def _mean_ws_moment(bwc, /, n=1.0, bysector=False):
    """Calculate the n^th moment of the wind speed from a bwc

    Parameters
    ----------
    bwc: xarray.Dataset
        Binned wind climate xr.Dataset object
    n: float
        Moment to compute, defaults to 1.0.
    bysector: bool
        Whether to return the sectorwise wind speed moment or the
        all-sector mean moment. Defaults to False.

    Returns
    -------
    ws_moment: xarray.DataArray
        Array of wind speed moments.
    """
    if bysector:
        return (bwc.wsfreq * bwc.wsbin**n).sum(dim=["wsbin"], skipna=False)
    return (bwc.wdfreq * bwc.wsfreq * bwc.wsbin**n).sum(
        dim=["wsbin", "sector"], skipna=False
    )


@_wv_count_wrapper
def _ws_cdf(bwc, /, bysector=False):
    """Calculate the cumulative distribution function (CDF) of the wind speed from a bwc

    Parameters
    ----------
    bwc: xarray.Dataset
        Binned wind climate xr.Dataset object
    bysector: bool
        Whether to return the sectorwise wind speed cdf or the
        all-sector mean cdf. Defaults to False which returns the
        all-sector mean cdf.

    Returns
    -------
    ws_cdf: xarray.DataArray
        Array of wind speed cdf.
    """
    if bysector:
        return bwc.wsfreq.cumsum(dim=["wsbin"], skipna=False)
    return (
        (bwc.wdfreq * bwc.wsfreq)
        .sum(dim="sector", skipna=False)
        .cumsum(dim=["wsbin"], skipna=False)
    )


@_wv_count_wrapper
def _ws_freq_gt_mean(bwc, /, bysector=False):
    """Calculate the frequency of wind speeds greater than the mean wind speed.

    Parameters
    ----------
    bwc: xarray.Dataset
        Binned wind climate xr.Dataset object

    bysector: bool
        Whether to return the sectorwise wind speed cdf or the
        all-sector mean cdf. Defaults to False which returns the
        all-sector value.

    Returns
    -------
    freq_gt_mean: xarray.DataArray
        Array of fraction greater than the mean wind speed in the histograms

    """
    # check for dimensions with no coordinates and temporarily add them
    # to the dataset to avoid problems with xarrays .interp method.
    # This is due to an issue in xarray when we have dimensions
    # with no coordiatnes on both the dataset and interpolation coordinates.
    # We should make an issue on xarray to fix this and remove this workaround afterward.

    dims_no_coord = [d for d in bwc.dims if d not in bwc.coords]
    bwc = bwc.assign_coords({d: (d, np.arange(bwc[d].size)) for d in dims_no_coord})

    # We set the wsceil as the coordinate because we want to interpolate
    # between bin edges.
    cdf = _ws_cdf(bwc, bysector=bysector).set_index({"wsbin": "wsceil"})
    mean = _mean_wind_speed(bwc, bysector=bysector)
    fgtm = 1.0 - cdf.interp(wsbin=mean, method="linear")
    # If the mean wind speed is below the first bin ceiling or above the last, we get nan values back
    # We set these to 0.5, which is the value we would get if the mean wind speed was exactly in the middle
    fgtm = fgtm.fillna(0.5)

    # Remove variables related to the wind speed bins if present
    fgtm = fgtm.drop_vars([v for v in ["wsbin", "wsfloor"] if v in fgtm.coords])

    # remove temporary dimensions
    fgtm = fgtm.drop_vars(dims_no_coord)

    return fgtm


def _fill_wsbin(bwc, /, n_wsbins):
    """Expands a binned wind climate to n_wsbins number of bins
    This is a useful feature when you want to combine several
    binnen wind climates in one dataset, because that requires that they
    have the same dimensions. The last two bins of the histogram
    are used to extrapolate the spacing. Up to this point the bins
    can also be irregular.

    Parameters
    ----------
    bwc: :any:`windkit.bwc`
        Binned wind climate
    n_wsbins: int
        Number of wind speeds bins

    Returns
    -------
    filled_bwc: :any:`windkit.bwc`
        Binned wind climate with n_wsbins number of bins
    """
    extension_bin = -2  # index of second last bin of histogram
    owsbin = bwc.sizes["wsbin"]
    # get spacing between last two bins
    dws = np.diff(bwc.wsbin[extension_bin:])
    newbins = np.zeros(n_wsbins)  # create new array with desired length
    newbins[0:owsbin] = bwc.wsbin.values  # set old bins
    newbins[owsbin:n_wsbins] = newbins[owsbin - 1] + dws * np.arange(
        1, n_wsbins - owsbin + 1
    )  #
    wsceil = np.append(
        bwc.wsceil, bwc.wsceil[[-1]] + dws * np.arange(1, n_wsbins - owsbin + 1)
    )
    wsfloor = np.append(
        bwc.wsfloor, bwc.wsfloor[[-1]] + dws * np.arange(1, n_wsbins - owsbin + 1)
    )
    filled_bwc = bwc.interp(wsbin=newbins, kwargs={"fill_value": 0.0})
    filled_bwc["wsceil"] = (("wsbin"), wsceil, _WSBIN_COORD_ATTRS["wsceil"])
    filled_bwc["wsfloor"] = (("wsbin"), wsfloor, _WSBIN_COORD_ATTRS["wsfloor"])

    return filled_bwc


@_validate_bwc_wrapper_factory(run_extra_checks=False)
def weibull_fit(bwc, include_met_fields=None, atol=1e-8):
    """
    Returns sectorwise Weibull parameters using WAsP's fitting algorithm.

    Parameters
    ----------
    bwc : xarray.Dataset
        Binned wind climate xr.Dataset object

    include_met_fields : bool
        Whether to include met fields in the output. Defaults to False.

    atol : float
        Absolute tolerance for the weibull-fitting algorithm. Defaults to 1e-6.

    Returns
    -------
    xarray.Dataset
        Weibull Wind Climate of same spatial extent as the input bwc
    """

    # Not implemtened yet # TODO: implement
    if include_met_fields is not None:
        raise NotImplementedError(
            "The include_met_fields argument is not implemented yet."
        )

    m1 = _mean_ws_moment(bwc, 1.0, bysector=True)
    m3 = _mean_ws_moment(bwc, 3.0, bysector=True)
    fgtm = _ws_freq_gt_mean(bwc, bysector=True)

    shape, scale = weibull.fit_weibull_wasp_m1_m3_fgtm(m1, m3, fgtm, atol=atol)

    wb = bwc[["wdfreq"]].astype("float64").copy()
    wb["A"] = shape
    wb["k"] = scale

    wb = _update_var_attrs(wb, _WEIB_ATTRS)

    return _update_history(wb)


def _mean_wind_speed(bwc, bysector=False):
    """Calculate the mean wind speed.

    Parameters
    ----------
    bwc: xarray.Dataset
        Binned wind climate xr.Dataset object.
    bysector: bool
        Return sectorwise mean wind speed if True. Defaults to False.

    Returns
    -------
    bwc : xarray.DataArray
        Mean wind speed of the bwc.
    """
    ds = _mean_ws_moment(bwc, 1.0, bysector)
    return _update_history(ds)


def _mean_power_density(bwc, bysector=False, air_density=1.225):
    """Calculate the power density

    Calculates the power density using a standard atmosphere air density of 1.225 kg m-3

    Parameters
    ----------
    bwc: xarray.Dataset
        Binned wind climate xr.Dataset object.
    bysector: bool
        Return sectorwise mean wind speed if True. Defaults to False.
    air_dens : float
        Air density. Default set to 1.225 kg.m^-3.

    Returns
    -------
    bwc : xarray.DataArray
        Power density of the bwc.
    """
    return 1 / 2 * air_density * _mean_ws_moment(bwc, 3.0, bysector)
