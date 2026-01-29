# (c) 2022 DTU Wind Energy
"""
WAsP GML Format

This format should be described by:
https://gitlab-internal.windenergy.dtu.dk/WAsP/wasp-schemas/-/blob/master/WaspVectorMap.xsd,
however, this is out of date and needs to be refreshed.

The format currently consists of:

WaspVectorMap
    Description
    CreatedBy
    MaxExtents
    (SurfacePropertiesTable) -- Optional
    LandCoverMapMember | ElevationMapMember
"""

from collections import defaultdict
from enum import Enum
from itertools import chain
from pathlib import Path
from typing import Optional, Union

import lxml.etree as ET
import pyproj
from shapely.geometry import LineString

from ._vectormap_helpers import (
    VECTORMAP_ELEV_COL,
    VECTORMAP_IDL_COL,
    VECTORMAP_IDR_COL,
    MapTypes,
    _explode_gdf,
    _is_lc,
)
from ..import_manager import _import_optional_dependency
from .landcover import LandCoverTable


class LandCoverType(Enum):
    WATER = "Water_Surface"
    Z0 = "Land_Roughness"
    DISP = "Roughness_and_Displacement"


def _get_desc(root):  # pragma: no cover (Not used yet)
    return root.find("map:Description", root.nsmap).text


def _add_desc(root, desc):
    e = root.makeelement(f"{{{root.nsmap['map']}}}Description", nsmap=root.nsmap)
    e.text = desc
    root.append(e)


def _get_created_by(root):  # pragma: no cover (Not used yet)
    """Dict of {software, version}"""
    return root.find("map:CreatedBy", root.nsmap).attrib


def _add_created_by(root):
    # currently WAsP only opens the files when they contain the right version
    # attrs = dict(software=__name__.split(".")[0], version=version[0:5])
    attrs = dict(software=__name__.split(".")[0], version="12.04.04.65")
    e = root.makeelement(f"{{{root.nsmap['map']}}}CreatedBy", attrs, nsmap=root.nsmap)

    root.append(e)


def _get_extents(root):
    me = root.find("map:MaxExtents", root.nsmap)
    env = me.find("gml:Envelope", root.nsmap)
    lc = env.find("gml:lowerCorner", root.nsmap)
    uc = env.find("gml:upperCorner", root.nsmap)
    proj = pyproj.CRS(env.attrib["srsName"])
    mins = [float(i) for i in lc.text.split()]
    maxes = [float(i) for i in uc.text.split()]

    return proj, mins + maxes


def _add_extents(root, bbox, srs):
    me = root.makeelement(f"{{{root.nsmap['map']}}}MaxExtents", nsmap=root.nsmap)
    env = me.makeelement(
        f"{{{root.nsmap['gml']}}}Envelope",
        attrib={"srsName": f"urn:ogc:def:crs:EPSG::{srs.to_epsg()}"},
        nsmap=root.nsmap,
    )
    lc = env.makeelement(f"{{{root.nsmap['gml']}}}lowerCorner", nsmap=root.nsmap)
    lc.text = " ".join([str(i) for i in bbox[:2]])
    uc = env.makeelement(f"{{{root.nsmap['gml']}}}upperCorner", nsmap=root.nsmap)
    uc.text = " ".join([str(i) for i in bbox[2:]])

    env.append(lc)
    env.append(uc)
    me.append(env)
    root.append(me)


def _get_table(root):
    # Short names for lookups
    _wasp_chg = f"{{{root.nsmap['wasp-chg']}}}"
    _gml = f"{{{root.nsmap['gml']}}}"
    _lct_key = f"{_wasp_chg}LandCoverType"

    # Find table element
    table = root.find("wasp-chg:SurfacePropertiesTable", root.nsmap)

    # Define empty data container
    data = {}

    for lc in table.findall("wasp-chg:SurfacePropertiesTableMember", table.nsmap):
        id = int(lc.getchildren()[0].attrib[f"{_gml}id"].split(".")[-1])
        data[id] = {}

        # Landcover type from element
        lct = lc.xpath(".//wasp-chg:LandCover", namespaces=lc.nsmap)[0].attrib[_lct_key]
        try:
            lct = LandCoverType(lct)
        except ValueError:  # pragma: no cover
            raise ValueError(f"Cannot process wasp-chg:LandCoverType '{lct}'")

        # Loop over parameters and add them to the dataset
        for lcp in lc.xpath(".//wasp-chg:LandCoverParameter", namespaces=lc.nsmap):
            param = lcp.attrib[f"{_wasp_chg}ParamID"].lower()
            value = float(lcp.getchildren()[0].text)
            data[id][param] = value

        # Check that we have d and Z0 for all fields
        if "z0" not in data[id].keys():  # pragma: no cover
            if lct is LandCoverType.WATER:
                data[id]["z0"] = 0.0
            else:
                raise ValueError(
                    f"""
                SurfaceProperties id {id}
                wasp-chg:LandCoverType {lct} must have roughness parameter 'Z0'
                """
                )

        if "d" not in data[id].keys():  # pragma: no cover
            if lct is LandCoverType.WATER or lct is LandCoverType.Z0:
                data[id]["d"] = 0.0
            else:
                raise ValueError(
                    f"""
                SurfaceProperties id {id}
                wasp-chg:LandCoverType {lct} must have displacement height parameter 'd'
                """
                )

        if "desc" not in data[id].keys():
            data[id]["desc"] = ""

    return LandCoverTable(data)


def _add_table(root, lctable):
    tbl = root.makeelement(
        f"{{{root.nsmap['wasp-chg']}}}SurfacePropertiesTable",
        {f"{{{root.nsmap['gml']}}}id": "sfpt.0"},
        nsmap=root.nsmap,
    )
    fmt_table = """
        <wasp-chg:SurfacePropertiesTableMember xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:map="http://www.wasp.dk/schemas/WaspVectorMap/1.0" xmlns:wasp-chg="http://www.wasp.dk/schemas/WaspChangeLines/1.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
			<wasp-chg:SurfaceProperties gml:id="sfp.{id}">
				<wasp-chg:LandCover wasp-chg:LandCoverType="{lct}">
					<wasp-chg:LandCoverParameters>{parameters}
					</wasp-chg:LandCoverParameters>
				</wasp-chg:LandCover>
			</wasp-chg:SurfaceProperties>
		</wasp-chg:SurfacePropertiesTableMember>
    """
    fmt_disp = """
						<wasp-chg:LandCoverParameter wasp-chg:ParamID="d" wasp-chg:ParamUnit="m" wasp-chg:ParamType="{param_type}">
							<wasp-chg:ZeroPlaneDisplacementHeight>{d}</wasp-chg:ZeroPlaneDisplacementHeight>
						</wasp-chg:LandCoverParameter>"""
    fmt_z0 = """
						<wasp-chg:LandCoverParameter wasp-chg:ParamID="Z0" wasp-chg:ParamUnit="m" wasp-chg:ParamType="{param_type}">
							<wasp-chg:AerodynamicalRoughnessLength>{z0}</wasp-chg:AerodynamicalRoughnessLength>
						</wasp-chg:LandCoverParameter>"""
    for k, v in lctable.items():
        # Always write as displacement and roughness
        lct = LandCoverType.DISP
        z0_param_type = "Configurable"
        d_param_type = "Configurable"

        param_str = fmt_z0.format(z0=v["z0"], param_type=z0_param_type)
        param_str += fmt_disp.format(d=v["d"], param_type=d_param_type)
        e = ET.fromstring(fmt_table.format(id=k, lct=lct.value, parameters=param_str))
        tbl.append(e)

    root.append(tbl)


### Parse posList elements
def _poslist2LineString(pos_list):
    # Split list by white-space and convert to float
    pos_list = [float(i) for i in pos_list.text.split()]

    # Create line string from coordinate list [[x1, y1], [x2, y2], ...]
    return LineString(zip(pos_list[::2], pos_list[1::2]))


def _get_landcover_lines(root):
    data = defaultdict(list)

    for lc in root.findall("map:LandCoverMapMember", root.nsmap):
        pos_list = lc.xpath(".//gml:posList", namespaces=lc.nsmap)[0]
        ls = _poslist2LineString(pos_list)

        data["geometry"].append(ls)

        data[VECTORMAP_IDL_COL].append(
            int(
                lc.xpath(".//wasp-chg:id_left/@xlink:href", namespaces=lc.nsmap)[
                    0
                ].split(".")[-1]
            )
        )
        data[VECTORMAP_IDR_COL].append(
            int(
                lc.xpath(".//wasp-chg:id_right/@xlink:href", namespaces=lc.nsmap)[
                    0
                ].split(".")[-1]
            )
        )

    return data


def _add_landcover(root, gdf):
    fmt_line = """
    <map:LandCoverMapMember xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:map="http://www.wasp.dk/schemas/WaspVectorMap/1.0" xmlns:wasp-chg="http://www.wasp.dk/schemas/WaspChangeLines/1.0" xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <wasp-chg:ChangeLine gml:id="line.{id}">
            <wasp-chg:geometry>
                <gml:LineString srsName="urn:ogc:def:crs:EPSG::{epsg}" gml:id="line.{id}.geom">
                    <gml:posList>{pos_list}</gml:posList>
                </gml:LineString>
            </wasp-chg:geometry>
            <wasp-chg:id_left xlink:href="#sfp.{id_left}"></wasp-chg:id_left>
            <wasp-chg:id_right xlink:href="#sfp.{id_right}"></wasp-chg:id_right>
        </wasp-chg:ChangeLine>
    </map:LandCoverMapMember>
    """

    for id, row in gdf.iterrows():
        pos_list = " ".join([f"{i:.1f}" for i in chain(*zip(*row.geometry.coords.xy))])
        e = ET.fromstring(
            fmt_line.format(
                id=id,
                id_left=int(row.id_left),
                id_right=int(row.id_right),
                epsg=gdf.crs.to_epsg(),
                pos_list=pos_list,
            )
        )
        root.append(e)


def _get_elevation(root):
    data = defaultdict(list)

    for eline in root.findall("map:ElevationMapMember", root.nsmap):
        pos_list = eline.xpath(".//gml:posList", namespaces=eline.nsmap)[0]
        ls = _poslist2LineString(pos_list)
        data["geometry"].append(ls)

        data[VECTORMAP_ELEV_COL].append(
            float(
                eline.xpath(".//el-vec:propertyValue", namespaces=eline.nsmap)[0].text
            )
        )

    return data


def _read_vector_map_gml(filename: Union[Path, str]):
    """Only Landcover and elevation right now"""
    gpd = _import_optional_dependency("geopandas")

    et = ET.parse(str(filename))
    root = et.getroot()
    if "wasp-chg" in root.nsmap.keys():
        map_type = MapTypes.landcover
    elif "el-vec" in root.nsmap.keys():
        map_type = MapTypes.elevation
    else:  # pragma: no cover
        raise ValueError("Unknown GML map type")

    # These aren't used at the moment as they can't be added to GeoDataFrames
    # desc = _get_desc(root)
    # created_by = _get_created_by(root)
    ext_srs, _ = _get_extents(root)

    if map_type == MapTypes.landcover:
        lctable = _get_table(root)
        lines = _get_landcover_lines(root)
        gdf = gpd.GeoDataFrame(lines, geometry="geometry", crs=ext_srs)
        return (gdf, lctable)
    elif map_type == MapTypes.elevation:
        lines = _get_elevation(root)
        gdf = gpd.GeoDataFrame(lines, geometry="geometry", crs=ext_srs)
        return (gdf, None)
    else:
        raise ValueError("Unknown map type")


def _write_vectormap_gml(
    filename: Union[Path, str],
    gdf,
    lctable: Optional[LandCoverTable],
    description: str,
):
    """Only landcover suported"""
    if not _is_lc(gdf):  # pragma: no cover
        raise ValueError("Only landcover maps can be written to GML.")
    if description == "":
        raise ValueError("Description cannot be empty for a .gml file.")
    gdf = _explode_gdf(gdf)

    nsmap = {
        "gml": "http://www.opengis.net/gml/3.2",
        "map": "http://www.wasp.dk/schemas/WaspVectorMap/1.0",
        "wasp-chg": "http://www.wasp.dk/schemas/WaspChangeLines/1.0",
        "wfs": "http://www.opengis.net/wfs/2.0",
        "xlink": "http://www.w3.org/1999/xlink",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }
    attrs = {
        f"{{{nsmap['gml']}}}id": "WaspVectorMap.0",
        f"{{{nsmap['xsi']}}}schemaLocation": "http://www.wasp.dk/schemas/ http://ogr.maptools.org/ WaspVectorMap.xsd",
    }

    out = ET.Element(f"{{{nsmap['map']}}}WaspVectorMap", attrs, nsmap=nsmap)
    _add_desc(out, description)
    _add_created_by(out)
    _add_extents(out, gdf.total_bounds, gdf.crs)
    _add_table(out, lctable)
    _add_landcover(out, gdf)

    # Convert to ElementTree and write results to file
    ET.ElementTree(out).write(str(filename), pretty_print=True)
