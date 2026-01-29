# (c) 2022 DTU Wind Energy
"""
Processes WAsP CFD volume results for use in PyWAsP
"""

__all__ = ["read_cfdres"]

import logging
import tempfile
from lxml import etree as ET
import zipfile
from pathlib import Path

import xarray as xr

from .xarray_structures.sector import create_sector_coords
from .spatial import set_crs

logger = logging.getLogger(__name__)

CFD_ZIP_NAMES = [
    "SpeedUpGrid",
    "DirectionDeflectionGrid",
    "TurbulenceIntensityGrid",
    "InclinationGrid",
]
CFD_VAR_NAMES = [
    "speedups",
    "turnings",
    "turbulence_intensity",
    "flow_inclination",
]


def _read_grd(path):
    """
    Create a raster from 1-band GIS files able to be read by rasterio.

    Note: we cannot use windkits read_raster_map function, because that was
    nearly a factor 100 slower. So I made simpler function here.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to file (on disk or in zipfile)

    Returns
    -------
    xarray.DataArray
        Raster object according to WindKit conventions
    """
    ds = xr.load_dataset(path, engine="rasterio").isel(band=0).squeeze()
    _, dx, _, _, _, dy = [
        float(i) for i in ds.spatial_ref.attrs["GeoTransform"].split(" ")
    ]
    array = ds.drop_vars(["band", "spatial_ref"])["band_data"]
    array = array.rename({"x": "west_east", "y": "south_north"})

    if dy < 0:
        array = array.sortby("south_north")

    if dx < 0:
        array = array.sortby("west_east")

    return array


def read_cfdres(path, crs):
    """
    Read .cfdres file into xarray

    A .cfdres file is a zipfile that contains a xml file
    ``TerrainAnalysisResultsManifest``, which contains all
    metadata of the things that are inside the zipfile.
    There is a PDF report which reports some basic characteristics of the
    CFD simulation. All the CFD results are in Surfer .GRD file format,
    which is readable by nearly all GIS tools (more info about each field
    is given below in the notes).

    Parameters
    ----------
    file_path : str or pathlib.Path
        Path to file (on disk or in zipfile)
    crs : int, dict, str or pyproj.crs.CRS
        Value to initialize `pyproj.crs.CRS` (Default: read from file)

    Returns
    -------
    xarray.DataArray
        Raster object according to WindKit conventions
    """
    cfd = zipfile.ZipFile(path)
    meta = cfd.open("TerrainAnalysisResultsManifest.xml", "r")
    xml = ET.parse(meta).getroot()
    result = xml.find("WindSimulationResults")

    with tempfile.TemporaryDirectory() as tempdir:
        tmp_dir = Path(tempdir)
        meta = cfd.open("TerrainAnalysisResultsManifest.xml", "r")
        cfd.extractall(tempdir)
        xml = ET.parse(meta).getroot()
        result = xml.find("WindSimulationResults")

        all_arrays = []
        z0meso = []
        for sector in result.findall("WindCondition"):
            sector_list = []
            z0meso.append(float(sector.attrib["MesoscaleRoughnessLength"]))
            for sector_agl in sector.findall("HeightResults"):
                sec_dir = float(
                    sector.find("DirectionDistributionUniform").attrib[
                        "CentreAngleDegrees"
                    ]
                )
                agl = float(sector_agl.attrib["HeightAgl"])
                logger.debug(
                    f"Loading .grd file for sector {sec_dir} and height {agl}."
                )
                for name, our_name in zip(CFD_ZIP_NAMES, CFD_VAR_NAMES):
                    file_name = sector_agl.find(name).attrib["Filename"]
                    array = _read_grd(tmp_dir / file_name)
                    array.name = our_name
                    array.coords["height"] = agl
                    array = array.expand_dims(["height"])
                    sector_list.append(array)
            # combine all data arrays into a dataset
            ds_sector = xr.merge(sector_list)
            # load mesoscale roughness length
            ds_sector.coords["sector"] = sec_dir
            ds_sector = ds_sector.expand_dims(["sector"])
            all_arrays.append(ds_sector)

        ds_cfd = xr.concat(all_arrays, dim="sector")
        ds_cfd["z0meso"] = (("sector",), z0meso)
        # make sure all the meta data for sectors are there
        ds_cfd = ds_cfd.assign_coords(
            create_sector_coords(ds_cfd.sizes["sector"]).coords
        )

        # TODO add also assign attributes to height coordinate, see here https://gitlab-internal.windenergy.dtu.dk/ram/software/pywasp/windkit/-/issues/372

        # load terrain elevation
        file_name = xml.find("ElevationGrid").attrib["FileName"]
        array = _read_grd(tmp_dir / file_name)
        ds_cfd["elevation"] = array

        # add the projection information to the dataset
        ds_cfd = set_crs(ds_cfd, crs)

        meta_data = {}
        results = xml.findall("JobInfo")
        for elem in results:
            for e in elem:
                if e.text is None:
                    meta_data.update(e.attrib)
                else:
                    meta_data[e.tag] = e.text

        ds_cfd = ds_cfd.assign_attrs(meta_data)

        meta.close()

        return ds_cfd.load()
