"""This module contains functions responsible for downloading / extracting
data from the different tutorial or example cases for testing porpuses."""

import json
import warnings
import zipfile
from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import requests
import xarray as xr
from platformdirs import user_data_dir

# Constants duplicated from config to avoid loading pydantic on import
APPNAME = "windkit"
APPAUTHOR = "DTU Wind Energy"

_ZENODO_BASE_URL = "https://zenodo.org/records/15294898/files/"

_TUTORIAL_DATASETS = {"serra_santa_luzia": "SerraSantaLuzia.zip"}


def _download_tutorial_data(zip_path):
    """Downloads the tutorial data from Zenodo if not already cached.

    Parameters
    ----------
    zip_path : str
        Path to the zip file where the tutorial data will be downloaded to.

    Raises
    ------
    ConnectionError
        If there is no internet connection.
    RuntimeError
        If the download fails or the status code is not 200.

    """

    # Check internet connection
    try:
        requests.get("https://www.google.com", timeout=5)
    except requests.ConnectionError:
        raise ConnectionError("No internet connection. Cannot download tutorial data.")
    # Clear directory if incomplete
    zip_filename = zip_path.name
    zip_url = f"{_ZENODO_BASE_URL}{zip_filename}?download=1"
    print(f"Downloading {zip_filename} from Zenodo...")
    response = requests.get(zip_url)
    if response.status_code == 200:
        with open(zip_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded {zip_filename} to {zip_path}")
    else:
        raise RuntimeError(
            f"Failed to download {zip_filename} from Zenodo. Status code: {response.status_code}"
        )


def _parse_tutorial_data(zip_path):
    """Parses the tutorial data from the zip file.
    Reads the metadata.json file and extracts the data files.

    Parameters
    ----------
    zip_path : str
        Path to the zip file containing the tutorial data.

    Returns
    -------
    SimpleNamespace
        Object with all the contents of a specific tutorial dataset or a specific object if requested
    """

    zip = zipfile.ZipFile(zip_path, "r")
    metadata = json.loads(zip.read("metadata.json"))

    data = {}
    for fileinfo in metadata["files"]:
        path = fileinfo["path"]
        name, file_ext = Path(path).stem, Path(path).suffix
        if file_ext == ".nc":
            # Read NetCDF files
            data[name] = xr.load_dataset(zip.open(path))
        elif file_ext == ".gpkg":
            # Since we are reading from a zip file, we need the file extension
            # is not recognized as .gpkg, so we filter out that
            # concrete warning
            with warnings.catch_warnings():
                # Read GeoPackage files
                warnings.filterwarnings(
                    "ignore",
                    message=".*but non conformant file extension.*",
                    category=RuntimeWarning,
                )
                data[name] = gpd.read_file(zip.open(path), engine="pyogrio")
        else:
            print("Skipping file:", path)
            continue

    return SimpleNamespace(**data)


def get_tutorial_data(name, force_download=False):
    r"""Downloads and extracts tutorial data from Zenodo if not already cached.

    The local cache is stored in the user data directory under the name "windkit".
    On Windows, this is typically located at:

    'C:\Users\<username>\AppData\Roaming\windkit\tutorial_data'

    On Linux, it is typically located at:

    '/home/<username>/.local/share/windkit/tutorial_data'

    You can check the location of the user data directory using the ``user_data_dir``
    function from the ``platformdirs`` package.

    Parameters
    ----------
    name : str, optional
        Name of the dataset to download. Currently only "serra_santa_luzia" is avaiable.
    force_download : bool, optional
        If True, forces re-download of the dataset even if it already exists. Default is False.

    Returns
    -------
    SimpleNamespace
        Object with all the contents of a specific tutorial dataset or a specific object if requested

    Raises
    ------
    ValueError
        If the name is not valid or the dataset is not available.
    ConnectionError
        If there is no internet connection when trying to download the data.
    RuntimeError
        If the download fails or the status code is not 200.

    Examples
    --------
    >>> data = get_tutorial_data("serra_santa_luzia")
    >>> data
    namespace(turbines=<xarray.Dataset>
              bwc=<xarray.Dataset>
              elev=<geopandas.geodataframe.GeoDataFrame>
              rgh=<geopandas.geodataframe.GeoDataFrame>
              wtg=<xarray.Dataset>)
    >>> data.bwc
    <xarray.Dataset> Size: 4kB
    Dimensions:       (point: 1, sector: 12, wsbin: 32)
    Coordinates:
        height        (point) float64 8B ...
        crs           int8 1B ...
        wsceil        (wsbin) float64 256B ...
        wsfloor       (wsbin) float64 256B ...
        sector_ceil   (sector) float64 96B ...
        sector_floor  (sector) float64 96B ...
    * wsbin         (wsbin) float64 256B 0.5 1.5 2.5 3.5 ... 28.5 29.5 30.5 31.5
    * sector        (sector) float64 96B 0.0 30.0 60.0 90.0 ... 270.0 300.0 330.0
        west_east     (point) float64 8B ...
        south_north   (point) float64 8B ...
    Dimensions without coordinates: point
    Data variables:
        wdfreq        (sector, point) float64 96B ...
        wsfreq        (wsbin, sector, point) float64 3kB ...
    """

    if name not in _TUTORIAL_DATASETS:
        raise ValueError(
            f"Invalid case name '{name}'. Available datasets: {', '.join(_TUTORIAL_DATASETS)}"
        )

    # check if the data is already downloaded
    tutorial_dir = (
        Path(user_data_dir(APPNAME, APPAUTHOR, roaming=True)) / "tutorial_data" / name
    )
    tutorial_dir.mkdir(parents=True, exist_ok=True)
    zip_filename = _TUTORIAL_DATASETS[name]
    zip_path = tutorial_dir / zip_filename

    # Check if the zip file already exists
    if not zip_path.exists() or force_download:
        _download_tutorial_data(zip_path)

    data = _parse_tutorial_data(zip_path)
    return data
