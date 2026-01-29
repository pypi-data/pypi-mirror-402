# (c) 2022 DTU Wind Energy
"""
WAsP Workspace module.

Module containing a class and related methods for importing WAsP workspace
XML and converting it to WindKit data structures.
"""

__all__ = ["Workspace"]

import tempfile
import warnings
import zipfile
from pathlib import Path

import lxml.etree as ET
import numpy as np
import pandas as pd
from packaging import version

from windkit._rvea_xml import _parse_rvea_generalised_mean_wind_climate
from windkit.xarray_structures.metadata import (
    _BWC_ATTRS,
    _WEIB_ATTRS,
    _update_history,
    _update_var_attrs,
)
from windkit.spatial import create_dataset, set_crs
from windkit.topography.vector_map import _crs_from_map_file, _read_vector_map
from windkit.wind_climate.binned_wind_climate import _parse_owc
from windkit.wind_climate.generalized_wind_climate import _weibull_to_dataset

_MAP_TYPE_MAPPING = {
    "RoughnessChangeLines": "roughness",
    "ElevationContours": "elevation",
    "Boundaries": "boundaries",
}


class Workspace:
    """
    Workspace class for interacting with WAsP workspace XML files

    Parameters
    -------
    tree : lxml.etree._ElementTree
        WAsP workspace XML tree
    path: str or Path
        File path.

    """

    def __init__(self, tree, path):
        self.tree = tree
        self.path = path
        self.root = tree.getroot()
        self._id_map = {}
        self._vector_map_id = []
        self._met_mast_id = None
        self.mast_coords = None
        self._map_files = {}
        self.catalogue = {}
        self.crs = None
        try:
            self.format_version = self.root.attrib["FormatVersion"]
        except (AttributeError, KeyError):
            raise TypeError("Not a WWH file")
        if version.parse(self.format_version) < version.parse("4.01.0004"):
            raise NotImplementedError(
                f"""The input WWH file has version {self.format_version} which is not supported. Only version 4.01.0004 and higher of WWH files can be loaded."""
            )

        self._create_catalogue()
        self._add_parent()
        self._add_children()
        self._get_vector_map_id()
        self._get_map_filenames()
        self._update_map_files_dict()
        self._update_met_mast_coords()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        lst = []
        allowed_objects = [
            "Turbine site group",
            "Generalised wind climate",
            "Observed wind climate",
            "Vector map",
        ]
        for key in self.catalogue.keys():
            if self.catalogue[key]["ObjectDescription"] in allowed_objects:
                lst += [
                    [
                        key,
                        self.catalogue[key]["ObjectDescription"],
                        self.catalogue[key]["CRS"],
                    ]
                ]

        df = pd.DataFrame.from_records(lst)
        df.columns = ["Object ID", "Object description", "Object CRS"]
        return df.to_string(index=False)

    def _get_desc(self):  # pragma: no cover private_method
        """
        Get a full list of XML objects and their relations

        Returns
        -------
        str
            Table with XML objects and their relations
        """
        lst = []
        for key in self.catalogue.keys():
            lst += [
                [
                    key,
                    self.catalogue[key]["ObjectDescription"],
                    self.catalogue[key]["ParentID"],
                    self.catalogue[key]["ChildrenID"],
                ]
            ]

        df = pd.DataFrame.from_records(lst)
        df.columns = [
            "Object ID",
            "Object description",
            "Parent object ID",
            "Children object ID",
        ]
        return print(df.to_string(index=False))

    @classmethod
    def read_wwh(cls, path):
        """
        Instantiated Workspace class using WAsP Workspace Hierarchy (WWH) file.

        Parameters
        ----------
        path : str, path
            Path to WAsP Workspace Hierarchy file to read.

        Returns
        -------
        Workspace
            Instantiated Workspace class.
        """

        with zipfile.ZipFile(path) as myZip:
            tree = ET.parse(myZip.open("Inventory.xml"))

        return cls(tree, path)

    def _create_catalogue(self):
        """
        Creates catalogue of objects from WAsP workspace XML tree

        Returns
        -------
        obj_cat : dict
            Dictionary containing WAsP workspace objects
        """

        search_template = '//*[@ID="{insert_id}"]'
        obj_cat = {}
        for i, elem in enumerate(self.root.iter("WaspHierarchyMember")):
            ID = elem.attrib["ID"].replace("{", "").replace("}", "")
            self._id_map.update({ID: i})

            # there should be only one path!
            path_binary = self.tree.xpath(search_template.replace("insert_id", ID))[0]

            # converting binary path to string path
            path_str = self.tree.getpath(path_binary).replace("/" + self.root.tag, ".")
            obj_cat.update(
                {
                    i: {
                        "ObjectDescription": elem.attrib["ClassDescription"],
                        "XPATH": path_str,
                        "ParentID": None,
                        "ChildrenID": [],
                        "CRS": {},
                    }
                }
            )
            if elem.attrib["ClassDescription"] == "Met. station":
                self._met_mast_id = i

        self.catalogue = obj_cat

    def _get_parent_id(self, ID):
        """
        Gets object's parent ID

        Parameters
        ----------
        ID : int
            ID of object for which parent ID is extracted

        Returns
        -------
        int
            ID of parent or 0 if it is root object
        """
        elem = self._get_object_xml(ID)
        parent_xml = elem.getparent().getparent()

        if parent_xml is not None:
            ID = parent_xml.attrib["ID"].replace("{", "").replace("}", "")
            return self._id_map[ID]
        else:
            return 0

    def _add_parent(self):
        """
        Adds IDs of parent objects to catalogue
        """
        for key in self.catalogue.keys():
            self.catalogue[key]["ParentID"] = self._get_parent_id(key)

    def _add_children(self):
        """
        Adds IDs of children objects to catalogue
        """
        for key in self.catalogue.keys():
            parent_id = self.catalogue[key]["ParentID"]
            self.catalogue[parent_id]["ChildrenID"] += [key]

    def _get_vector_map_id(self):
        """
        Updates self._vector_map_id object ids corresponding to vector maps.
        """
        for obj_id, obj in self.catalogue.items():
            if obj["ObjectDescription"] == "Vector map":
                self._vector_map_id += [obj_id]

    def _get_map_filenames(self):
        """
        Updates self._map_files with file names of vector maps in .wwh file
        """
        if len(self._vector_map_id) > 0:
            for ID in self._vector_map_id:
                vector_map_xml = self._get_object_xml(ID).xpath(
                    "./ChildMembers/WaspHierarchyMember"
                )
                self._map_files.update({ID: {}})
                for m in vector_map_xml:
                    _type = m.xpath("./MemberData/DataLayer")[0].attrib[
                        "DataPhenomenon"
                    ]
                    _file_name = m.xpath("./MemberData/ExternalArchive")[0].attrib[
                        "ArchiveTagID"
                    ]
                    self._map_files[ID].update(
                        {
                            _MAP_TYPE_MAPPING[_type]: {
                                "filename": _file_name,
                                "crs": None,
                            }
                        }
                    )

    def _update_map_files_dict(self):
        """
        Updates self._map_files with crs of vector maps in .wwh file
        """
        crs_ls = []
        if len(self._map_files) > 0:
            for ID, metadata in self._map_files.items():
                tempfolder = tempfile.TemporaryDirectory()
                path_tmp = Path(tempfolder.name)
                for map_type, info in metadata.items():
                    with zipfile.ZipFile(self.path) as myZip:
                        myZip.extract(info["filename"], path_tmp)
                    crs = _crs_from_map_file(path_tmp.joinpath(info["filename"]))
                    self._map_files[ID][map_type]["crs"] = crs
                    self.catalogue[ID]["CRS"].update({map_type: crs})
                    if crs is not None:
                        crs_ls += [crs]
                tempfolder.cleanup()
        crs_ls = np.unique(np.asarray(crs_ls))
        if len(crs_ls) == 1:
            self.crs = int(crs_ls[0])

    def _update_met_mast_coords(self):
        """
        Updates self.mast_coords which contains met mast position coordinates.
        """
        if self._met_mast_id is not None:
            mast_xml = self._get_object_xml(self._met_mast_id)
            height = float(
                mast_xml.xpath("./MemberData/SiteInformation")[0].attrib[
                    "WorkingHeightAgl"
                ]
            )
            west_east = float(
                mast_xml.xpath("./MemberData/SiteInformation/Location")[0].attrib[
                    "x-Location"
                ]
            )
            south_north = float(
                mast_xml.xpath("./MemberData/SiteInformation/Location")[0].attrib[
                    "y-Location"
                ]
            )

            header = mast_xml.attrib["Description"]

            self.mast_coords = {
                "height": height,
                "west_east": west_east,
                "south_north": south_north,
                "description": header,
                "crs": self.crs,
            }

    def _get_object_xml(self, ID):
        """
        Extracts objects XML from WAsP workspace XML

        Parameters
        ----------
        ID : int
            ID of object to be extracted

        Returns
        -------
        lxml.etree._Element
            Object XML representation
        """
        return self.root.find(self.catalogue[ID]["XPATH"])

    def _write_object(self, ID, path):  # pragma: no cover private_method
        """
        Write XML object to XML file

        Parameters
        ----------
        ID : int
            ID of object to be written to XML file
        path : str, path
            Path to XML file

        Returns
        -------
        file
            XML file on user machine
        """
        return ET.ElementTree(self._get_object_xml(ID)).write(path)

    def _print_object(self, ID):  # pragma: no cover private_method
        """
        Prints XML object

        Parameters
        ----------
        ID : int
            XML object ide

        Returns
        -------
        str
            String of XML object
        """
        return print(ET.tostring(self._get_object_xml(ID), encoding="unicode"))

    def get_owc(self, ID, crs=None):
        """
        Converts XML representation of owc to WindKit bwc data structure.

        Parameters
        ----------
        ID : int
            ID of bwc object in .wwh file.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`
        Returns
        -------
        xarray.Dataset
            xarray Dataset that is formatted to match the bwc description.
        """
        if ID not in self.catalogue:
            raise ValueError("ID does not exist in object catalogue")
        if self.catalogue[ID]["ObjectDescription"] != "Observed wind climate":
            raise ValueError("ID is not linked to binned wind climate")
        if self.crs is None and crs is None:
            raise ValueError(
                "No CRS associated with observed wind climate, CRS must be provided!"
            )
        if crs is None and self.crs is not None:
            crs = self.crs

        # subset XML
        bwc_xml = self._get_object_xml(ID).xpath(
            "./MemberData/RveaObservedWindClimate"
        )[0]
        bwc = _parse_owc(bwc_xml)

        # adding mast location and crs
        if self.mast_coords is not None:
            bwc.height.values = np.array([self.mast_coords["height"]])
            bwc.south_north.values = np.array([self.mast_coords["south_north"]])
            bwc.west_east.values = np.array([self.mast_coords["west_east"]])
            return set_crs(bwc, self.crs)

        bwc = set_crs(bwc, crs)
        ds = _update_var_attrs(bwc, _BWC_ATTRS)
        return _update_history(ds)

    def get_gwc(
        self,
        ID,
        crs=None,
        west_east=None,
        south_north=None,
        height=None,
        description=None,
    ):
        """
        Converts XML representation of gwc to WindKit gwc data structure.

        Parameters
        ----------
        ID : int
            ID of gwc object in .wwh file.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS` Default, use from file.
        west_east, south_north : float or None, optional
            x- and y-coordinates of gwc location. Defaults to None, which means
            the coordinates are taken from the met mast location or the file.
            If the met mast location is not available, an error is raised.
        height : float or None, optional
            Height of gwc location. Defaults to None, which means the height
            is taken from the met mast location or the file. If the met mast
            location is not available, the height is set to 0 m.
        description : str or None, optional
            Header of gwc. Defaults to None, which means the header
            is attempted to be taken from the met mast or the file.

        Returns
        -------
        xarray.Dataset
            xarray Dataset that is formatted to match the gwc description.

        Raises
        ------
        ValueError
            If the ID does not exist in the catalogue.
        ValueError
            If the ID is not linked to a gwc.
        ValueError
            If the mast location is not available and the coordinates are not
            provided.
        ValueError
            If no CRS is provided and the file does not contain a CRS.

        Warns
        -----
        UserWarning
            If no height is provided and the mast location is not available.
            The height is set to 0 m.

        """
        if ID not in self.catalogue:
            raise ValueError("ID does not exist in object catalogue")
        if self.catalogue[ID]["ObjectDescription"] != "Generalised wind climate":
            raise ValueError("ID is not linked to generalised wind climate")

        # subset XML
        tree = self._get_object_xml(ID)

        gwc_data = _parse_rvea_generalised_mean_wind_climate(
            tree.find(".//RveaGeneralisedMeanWindClimate")
        )

        if west_east is not None and south_north is not None:
            if crs is None:
                warnings.warn("No CRS provided, defaulting to file CRS")
                crs = self.crs
        elif self.mast_coords is not None:
            west_east = self.mast_coords["west_east"]
            south_north = self.mast_coords["south_north"]
            height = self.mast_coords["height"]
            crs = self.mast_coords["crs"]
            if description is None:
                description = self.mast_coords["description"]
        elif "longitude" in gwc_data and "latitude" in gwc_data:
            west_east = gwc_data["longitude"]
            south_north = gwc_data["latitude"]
            crs = "EPSG:4326"
        else:
            raise ValueError(
                "No location information provided, either provide coordinates or mast location"
            )

        if height is None:
            height = 0.0
            warnings.warn("No height provided, defaulting to 0 m")

        if self.crs is None and crs is None:
            raise ValueError(
                "No CRS associated with generalised wind climate, CRS must be provided!"
            )

        if description is None:
            description = ""

        gwc = _weibull_to_dataset(
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

        gwc = set_crs(gwc, crs)
        gwc = _update_var_attrs(gwc, _WEIB_ATTRS)
        return _update_history(gwc)

    def get_elevation_map(
        self,
        ID,
        crs=None,
    ):
        """
        Extracts elevation map from WWH and creates VectorMap object.

        Parameters
        ----------
        ID : int
            ID of vector map object to be extracted.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS` Default, use from file.

        Returns
        -------
        geopandas.GeoDataFrame
            Vector representation of the map.
        """
        if ID not in self.catalogue:
            raise ValueError("ID does not exist in object catalogue")
        if self.catalogue[ID]["ObjectDescription"] != "Vector map":
            raise ValueError("ID is not linked to vector map")
        if crs is None and self._map_files[ID]["elevation"]["crs"] is None:
            raise ValueError(
                "No CRS associated with this vector map, CRS must be provided!"
            )
        if crs is None and self._map_files[ID]["elevation"]["crs"] is not None:
            crs = self._map_files[ID]["elevation"]["crs"]

        filename = self._map_files[ID]["elevation"]["filename"]
        tempfolder = tempfile.TemporaryDirectory()
        path_tmp = Path(tempfolder.name)

        with zipfile.ZipFile(self.path) as myZip:
            myZip.extract(filename, path_tmp)

        vector_map = _read_vector_map(
            path_tmp.joinpath(filename),
            crs,
            map_type="elevation",
        )
        tempfolder.cleanup()

        return vector_map

    def get_roughness_map(
        self,
        ID,
        crs=None,
        convert_to_landcover=False,
        polygons=True,
    ):
        """
        Extracts vector map from WWH and creates VectorMap object.

        Parameters
        ----------
        ID : int
            ID of vector map object to be extracted.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS` Default, use from file.
        convert_to_landcover : bool, optional
            If True, convert roughness map to landcover map and landcover table.
            Defaults to False.
        polygons : bool, optional
            If True, convert roughness map to polygons. Defaults to True.

        Returns
        -------
        geopandas.GeoDataFrame
            Vector representation of the map.
        """
        map_type = "roughness"

        if ID not in self.catalogue:
            raise ValueError("ID does not exist in object catalogue")
        if self.catalogue[ID]["ObjectDescription"] != "Vector map":
            raise ValueError("ID is not linked to vector map")
        if crs is None and self._map_files[ID][map_type]["crs"] is None:
            raise ValueError(
                "No CRS associated with this vector map, CRS must be provided!"
            )
        if crs is None and self._map_files[ID][map_type]["crs"] is not None:
            crs = self._map_files[ID][map_type]["crs"]

        filename = self._map_files[ID][map_type]["filename"]
        tempfolder = tempfile.TemporaryDirectory()
        path_tmp = Path(tempfolder.name)

        with zipfile.ZipFile(self.path) as myZip:
            myZip.extract(filename, path_tmp)

        vector_map = _read_vector_map(
            path_tmp.joinpath(filename),
            crs,
            map_type,
            convert_to_landcover=convert_to_landcover,
            polygons=polygons,
        )
        tempfolder.cleanup()

        return vector_map

    def get_turbines(self, ID, crs=None):
        """
        Extracts turbine positions from WWH and creates WindKit xarray DataArray.

        Parameters
        ----------
        ID : int
            ID of turbine site group object to be converted.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS` Default, use from file.

        Returns
        -------
        xarray.DataArray
            WindKit formated zero-filled data array with point dimension
        """
        if ID not in self.catalogue:
            raise ValueError("ID does not exist in object catalogue")
        if self.catalogue[ID]["ObjectDescription"] != "Turbine site group":
            raise ValueError("ID is not linked to turbine site group")
        if crs is None and self.crs is None:
            raise ValueError(
                "No CRS associated with the turbine site group, CRS must be provided!"
            )
        if crs is None and self.crs is not None:
            crs = self.crs
        height = []
        x = []
        y = []

        for child in self.catalogue[ID]["ChildrenID"]:
            if self.catalogue[child]["ObjectDescription"] == "Turbine site":
                xml = self._get_object_xml(child).xpath("./MemberData/SiteInformation")[
                    0
                ]
                height += [float(xml.attrib["WorkingHeightAgl"])]
                x += [float(xml.xpath("./Location")[0].attrib["x-Location"])]
                y += [float(xml.xpath("./Location")[0].attrib["y-Location"])]

        return create_dataset(x, y, height, crs)

    def get_object(self, ID, map_type="elevation", crs=None):
        """
        Extracts object from .wwh file.

        Parameters
        ----------
        ID : int
            ID of object to be extracted.
        map_type : str, optional
            Feature type to extract from mapfile
            Possible values 'elevation', 'roughness'. Defaults to 'elevation'.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS` Default, use from file.

        Returns
        -------
        gwc, bwc, vector map or xarray.Dataset of turbine positions
        """
        if ID not in self.catalogue:
            raise ValueError("ID does not exist in object catalogue")
        if self.catalogue[ID]["ObjectDescription"] == "Vector map":
            if map_type == "elevation":
                return self.get_elevation_map(ID, crs=crs)
            elif map_type == "roughness":
                return self.get_roughness_map(ID, crs=crs)
        if self.catalogue[ID]["ObjectDescription"] == "Generalised wind climate":
            ds = self.get_gwc(ID, crs=crs)
            return _update_history(ds)
        if self.catalogue[ID]["ObjectDescription"] == "Observed wind climate":
            ds = self.get_owc(ID, crs=crs)
            return _update_history(ds)
        if self.catalogue[ID]["ObjectDescription"] == "Turbine site group":
            return self.get_turbines(ID, crs=crs)
        else:
            raise TypeError(
                "\nCan only convert: \n\t(1) Vector maps, \n\t(2) Generalised wind climate, \n\t(3) Observed wind climate and \n\t(4) Turbine site group"
            )
