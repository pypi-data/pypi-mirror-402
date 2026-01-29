import numpy as np


def _parse_standard_conditions(tree):
    """Parse a "StandardConditions" XML element tree.

    Parameters
    ----------
    tree : lmxl.etree.ElementTree
        "StandardConditions" XML element tree.

    Returns
    -------
    gen_roughness_standard, gen_height_standard : array_like or None

    """

    gen_roughness_standard, gen_height_standard = None, None

    descendants = list(e.tag for e in tree.iterdescendants())

    if "ReferenceRoughnessLengths" in descendants:
        gen_roughness_standard = np.array(
            list(
                float(e.attrib["AerodynamicRoughnessLengthMetres"])
                for e in tree.find(".//ReferenceRoughnessLengths").findall(
                    ".//RoughnessLength"
                )
                if "AerodynamicRoughnessLengthMetres" in e.attrib
            )
        )

    if "ReferenceHeights" in descendants:
        gen_height_standard = np.array(
            list(
                float(e.attrib["HeightAglMetres"])
                for e in tree.find(".//ReferenceHeights").findall(".//Height")
                if "HeightAglMetres" in e.attrib
            )
        )

    return gen_roughness_standard, gen_height_standard


def _parse_rvea_latitude_longitude_coordinate(tree):
    """parse a "RveaLatitudeLongitudeCoordinate" XML element trees.

    Parameters
    ----------
    tree : lmxl.etree.ElementTree
        "RveaLatitudeLongitudeCoordinate" XML element trees.

    Returns
    -------
    latitude, longitude : float or None

    """

    latitude, longitude = None, None

    descendants = list(e.tag for e in tree.iterdescendants())

    if "LatitudeDegrees" in tree.attrib:
        latitude = float(tree.attrib["LatitudeDegrees"])

    if "LongitudeDegrees" in tree.attrib:
        longitude = float(tree.attrib["LongitudeDegrees"])

    if latitude is None:
        if "Latitude" in descendants:
            latitude_tree = tree.find(".//Latitude")
            if "Degrees" in latitude_tree.attrib:
                latitude = float(latitude_tree.attrib["Degrees"])

    if longitude is None:
        if "Longitude" in descendants:
            longitude_tree = tree.find(".//Longitude")
            if "Degrees" in longitude_tree.attrib:
                longitude = float(longitude_tree.attrib["Degrees"])

    return latitude, longitude


def _parse_rvea_generalised_mean_wind_climate(tree):
    """Parse a "RveaGeneralizedMeanWindClimate" XML element into a dictionary of arrays.

    Parameters
    ----------
    tree : lmxl.etree.Element
        The XML element to parse.

    Returns
    -------
    dict
        A dictionary of arrays containing the parsed data.
        Contains:
            - "wdfreq" : array of shape (num_sec, num_gen_height, num_gen_roughness)
            - "A" : array of shape (num_sec, num_gen_height, num_gen_roughness)
            - "k" : array of shape (num_sec, num_gen_height, num_gen_roughness)
            - "gen_roughness" : array of shape (num_gen_roughness)
            - "gen_height" : array of shape (num_gen_height)
        Optional:
            - "sector" : array of shape (num_sec) with central sector angles
            - "latitude" : float or None
            - "longitude" : float or None

    Raises
    ------
    ValueError
        If the XML element is not a "RveaGeneralizedMeanWindClimate" element.
    """

    if tree.tag != "RveaGeneralisedMeanWindClimate":
        raise ValueError("tree must be 'RveaGeneralisedMeanWindClimate'")

    output = {}

    n_sector = None
    n_gen_height = None
    n_gen_roughness = None

    if "CountOfSector" in tree.attrib:
        n_sector = int(tree.attrib["CountOfSector"])

    if "CountOfReferenceHeights" in tree.attrib:
        n_gen_height = int(tree.attrib["CountOfReferenceHeights"])

    if "CountOfReferenceRoughnessLengths" in tree.attrib:
        n_gen_roughness = int(tree.attrib["CountOfReferenceRoughnessLengths"])

    descendants = list(e.tag for e in tree.iterdescendants())

    if "RveaLatitudeLongitudeCoordinate" in descendants:
        latitude, longitude = _parse_rvea_latitude_longitude_coordinate(
            tree.find(".//RveaLatitudeLongitudeCoordinate")
        )
        output["latitude"] = latitude
        output["longitude"] = longitude

    if "StandardConditions" in descendants:
        gen_roughness_standard, gen_height_standard = _parse_standard_conditions(
            tree.find(".//StandardConditions")
        )
        output["gen_roughness_standard"] = gen_roughness_standard
        output["gen_height_standard"] = gen_height_standard

    weibull_wind_roses = tree.findall(".//WindAtlasWeibullWindRose")

    if len(weibull_wind_roses) == 0:
        raise ValueError("No WindAtlasWeibullWindRose elements found")

    if n_sector is None:
        if "CountOfSectors" in weibull_wind_roses[0].attrib:
            n_sector = int(weibull_wind_roses[0].attrib["CountOfSectors"])

    if n_gen_height is None and "gen_height_standard" in output:
        n_gen_height = len(gen_height_standard)

    if n_gen_roughness is None and "gen_roughness_standard" in output:
        n_gen_roughness = len(gen_roughness_standard)

    # Create arrays
    wdfreq = np.zeros((n_sector, n_gen_height, n_gen_roughness))
    A = np.zeros((n_sector, n_gen_height, n_gen_roughness))
    k = np.zeros((n_sector, n_gen_height, n_gen_roughness))
    cen_angle = np.zeros(n_sector)
    gen_roughness = np.zeros(n_gen_roughness)
    gen_height = np.zeros(n_gen_height)

    for wwr in weibull_wind_roses:
        if "RoughnessLength" in wwr.attrib:
            z0 = float(wwr.attrib["RoughnessLength"])
        elif "ReferenceRoughnessLength" in wwr.attrib:
            z0 = float(wwr.attrib["ReferenceRoughnessLength"])
        else:
            z0 = None

        if "ReferenceHeight" in wwr.attrib:
            z = float(wwr.attrib["ReferenceHeight"])
        else:
            z = None

        if "ReferenceRoughnessLengthNumber" in wwr.attrib:
            iz0 = int(wwr.attrib["ReferenceRoughnessLengthNumber"]) - 1
        elif "RoughnessLengthNumber" in wwr.attrib:
            iz0 = int(wwr.attrib["RoughnessLengthNumber"]) - 1
        else:
            iz0 = None

        if "ReferenceHeightNumber" in wwr.attrib:
            iz = int(wwr.attrib["ReferenceHeightNumber"]) - 1
        else:
            iz = None

        if z0 is None and iz0 is not None and "gen_roughness_standard" in output:
            z0 = gen_roughness_standard[iz0]

        if z is None and iz is not None and "gen_height_standard" in output:
            z = gen_height_standard[iz]

        if iz0 is None and z0 is not None and "gen_roughness_standard" in output:
            iz0 = np.where(gen_roughness_standard == z0)[0][0]

        if iz is None and z is not None and "gen_height_standard" in output:
            iz = np.where(gen_height_standard == z)[0][0]

        gen_roughness[iz0] = z0
        gen_height[iz] = z

        for ww in wwr.findall(".//WeibullWind"):
            isec = int(ww.attrib["Index"]) - 1
            cen_angle[isec] = float(ww.attrib["CentreAngleDegrees"])
            A[isec, iz, iz0] = float(ww.attrib["WeibullA"])
            k[isec, iz, iz0] = float(ww.attrib["WeibullK"])
            wdfreq[isec, iz, iz0] = float(ww.attrib["SectorFrequency"])

    output["wdfreq"] = wdfreq
    output["A"] = A
    output["k"] = k
    output["sector"] = cen_angle
    output["gen_roughness"] = gen_roughness
    output["gen_height"] = gen_height
    return output


def _parse_rvea_anemometer_site_details(tree):
    """Parse "RveaAnemometerSiteDetails" XML element.

    Parameters
    ----------
    tree :  xml.etree.ElementTree.Element
        XML element to parse.

    Returns
    -------
    output : dict
        Dictionary containing parsed data.
        Possible output is:
            - height: float
            - latitude: float
            - longitude: float
            - header: str

    """
    if tree.tag != "RveaAnemometerSiteDetails":
        raise ValueError("tree must be 'RveaAnemometerSiteDetails'")

    output = {}
    if "HeightAGL" in tree.attrib:
        output["height"] = float(tree.attrib["HeightAGL"])
    if "LatitudeDegrees" in tree.attrib:
        output["latitude"] = float(tree.attrib["LatitudeDegrees"])
    if "LongitudeDegrees" in tree.attrib:
        output["longitude"] = float(tree.attrib["LongitudeDegrees"])
    if "Description" in tree.attrib:
        output["header"] = tree.attrib["Description"]

    return output
