# (c) 2022 DTU Wind Energy
"""
WAsP Engineering Workspace module.

Module containing a methods for importing WAsP Engineering proyect file in
XML format and converting it to WindKit data structures.
"""

__all__ = ["WengWorkspace"]

import tempfile

# needed to parse workspaces
import zipfile
from pathlib import Path

import lxml.etree as ET
import pandas as pd

from windkit.xarray_structures.metadata import _GEWC_ATTRS, _update_var_attrs
from windkit.topography.raster_map import _read_raster_map
from windkit.spatial import create_dataset


class WengWorkspace:
    def __init__(self, wep_file_path):
        self.file = wep_file_path
        with zipfile.ZipFile(self.file) as myZip:
            tree = ET.parse(myZip.open("ProjectInventory.xml"))
        self.root = tree.getroot()
        self.filenames_dict = {
            "elevation": "OrographicGridMapInventoryTag",
            "roughness": "RoughnessChangeGridMapInventoryTag",
        }

    def _wd_to_sector(self, sec_val, bin_size):
        return (((sec_val + bin_size / 2) % 360) // bin_size) * bin_size

    def get_extreme_wind_climate(self, ewc_name, spatial_ds, n_sectors=12):
        """
        Retrieves extreme wind climates from wasp engineering file
        """
        bin_size = 360 / n_sectors
        for element in self.root.iter("RegionalExtremeWindClimate"):
            if element.get("Description") == ewc_name:
                reg_element = element
        l_ewc = []
        try:
            for val in reg_element.iter("ExtremeWindSpeedScatterPlotSequencePeriod"):
                l_ewc.append(val)
            one_condition = []
            for v in l_ewc:
                for val in v.findall("ExtremeWindSpeedCondition"):
                    one_condition.append(
                        [
                            val.get("OriginalRecordingTimeStamp"),
                            float(val.get("MeanWindSpeed")),
                            float(val.get("CorrespondingWindDirectionDegrees")),
                            # float(val.get("SpeedRecordingIntervalSeconds")),
                        ]
                    )
        except UnboundLocalError:  # reg_element is never created
            raise ValueError(
                "no extreme wind climate was found for '{}'".format(ewc_name)
            )
        df = pd.DataFrame(
            data=one_condition, columns=["max_time", "max_wspd", "max_wdir"]
        )
        df["max_time"] = pd.to_datetime(df["max_time"])
        df["year"] = df["max_time"].dt.year
        df["sector"] = self._wd_to_sector(df["max_wdir"], bin_size)

        newxr = df.set_index(["sector", "year"])[
            ["max_wspd", "max_wdir", "max_time"]
        ].to_xarray()
        newxr = newxr.expand_dims(spatial_ds.dims).assign_coords(spatial_ds.coords)

        return _update_var_attrs(newxr, _GEWC_ATTRS)

    def list_extreme_wind_climates(self):
        """
        List all extreme wind climate descriptions. The names are needed
        to call WengWorkspace.get_extreme_wind_climate

        Parameters
        ----------
        None

        Returns
        -------
        None
            print on the stdout the list of values
        """
        print("Extreme wind climates:")
        e = self._list_description("RegionalExtremeWindClimate")
        for val in e:
            print(f"- {val}")

    def get_raster_map(self, map_type, crs):
        """
        Retrieves elevation or landcover raster map from WAsP Engineering file

        Parameters
        ----------
        map_type: str
            Map type, possible values are 'elevation','roughness'
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`.

        Returns
        -------
        xarray.DataArray
            raster map file
        pywasp.LandCoverTable
            pywasp landcover table (in case of roughness)

        """
        proj_dom = self.root.find("ProjectDomain")
        filename = proj_dom.get(self.filenames_dict[map_type])
        tempfolder = tempfile.TemporaryDirectory()
        path_tmp = Path(tempfolder.name)
        with zipfile.ZipFile(self.file) as myZip:
            myZip.extract(filename, path_tmp)
            # this can be either a elevation rastermap or a tuple (landcover map, landcover table)
            response = _read_raster_map(
                path_tmp.joinpath(filename), crs=crs, map_type=map_type
            )
        tempfolder.cleanup()
        return response

    def get_site_group(self, group_name, height, crs):
        """
        Retrieves a group of sites from WAsP Engineering file

        Parameters
        ----------
        group_name: str
            Name of the site group as defined in WAsP Engineering
        height: float
            Height value to build the dataset
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`.

        Returns
        -------
        xarray.Dataset
            Spatial dataset with points.
        """
        sites_dom = self.root.find("Sites")
        data = []

        for element in sites_dom.iter("SiteGroup"):
            if element.get("Description") == group_name:
                for val in element.findall("Site"):
                    data.append(
                        [
                            float(val.get("LocationX")),
                            float(val.get("LocationY")),
                            val.get("Description"),
                        ]
                    )
        if data == []:
            raise ValueError("No site group was found for '{}'".format(group_name))
        df = pd.DataFrame(data, columns=["west_east", "south_north", "Description"])
        df["height"] = height

        return create_dataset(
            df[["west_east"]].values.flatten(),
            df[["south_north"]].values.flatten(),
            df[["height"]].values.flatten(),
            crs,
        ).drop_vars("output")

    def get_site(self, site_name, height, crs):
        """
        Retrieves a single from WAsP Engineering file

        Parameters
        ----------
        group_name: str
            Name of the site as defined in WAsP Engineering
        height: float
            Height value to build the dataset
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`.

        Returns
        -------
        xarray.Dataset
            Spatial dataset with point.
        """
        sites_dom = self.root.find("Sites")

        for element in sites_dom.iter("Site"):
            if element.get("Description") == site_name:
                list_data = [
                    [
                        float(element.get("LocationX")),
                        float(element.get("LocationY")),
                        element.get("Description"),
                    ]
                ]
                break

        try:
            df = pd.DataFrame(
                list_data, columns=["west_east", "south_north", "Description"]
            )

        except UnboundLocalError:  # list_data was never assigned
            raise ValueError("No site was found for '{}'".format(site_name))
        df["height"] = height

        return create_dataset(
            df[["west_east"]].values.flatten(),
            df[["south_north"]].values.flatten(),
            df[["height"]].values.flatten(),
            crs,
        ).drop_vars("output")

    def list_sites(self):
        """
        List all sites and site groups. The names are needed to call
        WengWorkspace.get_site and WengWorkspace.get_site_group

        Parameters
        ----------
        None

        Returns
        -------
        None
            print on the stdout the list of values
        """
        s = self._list_description("Site")
        sg = self._list_description("SiteGroup")
        print("Sites:")
        for val in s:
            print(f"- {val}")
        print("Site groups:")
        for val in sg:
            print(f"- {val}")

    def _list_description(self, tag_name):
        """
        helper function to list descriptions for the given tag

        Returns
        -------
        result: str
            List with the values.
        """
        result = []
        for element in self.root.iter(tag_name):
            result.append(element.get("Description"))
        return result
