# (c) 2022 DTU Wind Energy
"""
WindKit Bounding Box.

This is an object that represents the extent of a GIS object in its native
projection.

It is currently used for clipping raster Datasets and RasterMaps
"""

__all__ = ["BBox"]


import geopandas as gpd
import numpy as np
import pyproj
from shapely.geometry import LinearRing, Polygon
from shapely.ops import transform

from ..xarray_structures.metadata import _update_history


class BBox:
    """WindKit Bounding Box

    WindKit Bounding boxes are defined by the center coordinates of the grid rather than
    the corner coordinates like in GDAL.

    Parameters
    ----------
    ring : :py:class:`shapely.geometry.LinearRing`
        Square ring that envelopes the boundaries of the data
    crs : int, dict, str or :py:class:`pyproj.crs.CRS`
        Value to initialize :py:class:`pyproj.crs.CRS`
    """

    def __init__(self, ring, crs):
        if not isinstance(ring, LinearRing):
            raise TypeError("ring must be a shapely.geometry.LinearRing")

        self.ring = ring
        self.crs = pyproj.CRS.from_user_input(crs)

    def __str__(self):  # pragma:no cover str_fmt
        bnds = self.bounds()
        return (
            f"Bounds: ({bnds[0]}, {bnds[1]}) ({bnds[2]}, {bnds[3]})\n"
            + f"CRS: {self.crs.to_wkt()}"
        )

    def __repr__(self):
        return self.__str__()

    @property
    def __geo_interface__(self):
        """Return GeoJSON representation of BBox as Polygon geometry"""
        return self.polygon.__geo_interface__

    def bounds(self):
        """Return bounds of bounding box."""
        return self.ring.bounds

    @property
    def polygon(self):
        """Return polygon of bounding box."""
        return Polygon(self.ring.coords)

    @classmethod
    def utm_bbox_from_geographic_coordinate(
        cls, longitude, latitude, buffer=10000.0, datum_name="WGS 84"
    ):
        """Create a bounding box object in UTM coordinates from a geographic coordinate and
        a buffer distance

        The UTM zome will be estimated from the longitude coordinate.

        Parameters
        ----------
        longitude : float
            longitude coordinate of the point

        latitude : float
            latitude coordinate of the point

        buffer : float
            buffer distance in meters

        datum_name : str
            Name of the datum to use for the UTM zone estimation. Defaults to "WGS 84".

        Returns
        -------
        BBox
            A BBox object
        """

        pt = gpd.points_from_xy(
            np.asarray([longitude]), np.asarray([latitude]), crs="epsg:4326"
        )
        crs_utm = pt.estimate_utm_crs(datum_name=datum_name)

        if crs_utm is None:
            raise ValueError("UTM CRS not found")

        transformer = pyproj.Transformer.from_crs("epsg:4326", crs_utm, always_xy=True)

        x, y = transformer.transform(longitude, latitude)

        return cls.from_cornerpts(
            minx=x - buffer,
            miny=y - buffer,
            maxx=x + buffer,
            maxy=y + buffer,
            crs=crs_utm,
        )

    @classmethod
    def from_point_and_buffer(cls, x, y, buffer, crs="epsg:4326"):
        """Create a bounding box object from a point and buffer

        Parameters
        ----------
        x : float
            west_east coordinate of the point
        y : float
            south_north coordinate of the point
        buffer : float
            buffer distance in meters
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`
            Defaults to "epsg:4326".

        Returns
        -------
        BBox
            A BBox object

        """

        crs = pyproj.CRS.from_user_input(crs)

        return cls.from_cornerpts(
            minx=x - buffer,
            miny=y - buffer,
            maxx=x + buffer,
            maxy=y + buffer,
            crs=crs,
        )

    @classmethod
    def from_cornerpts(
        cls, minx=0.0, miny=0.0, maxx=1000.0, maxy=1000.0, crs="epsg:32632"
    ):  # pylint:disable=too-many-arguments
        """Create a bounding box object from min and max values

        Parameters
        ----------
        minx : float
            Minimum values of the east-west direction. Defaults to  0.0.
        maxx : float
            Maximum values of the east-west direction. Defaults to 1000.0.
        miny : float
            Minimum values of the south-north direction. Defaults to 0.0.
        maxy : float
            Maximum values of the south-north direction. Defaults to 1000.0.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`
            Defaults to "epsg:32632".

        Returns
        -------
        BBox
            A bounding box of the requested coordinates.
        """
        if minx >= maxx:
            raise ValueError(f"minx: {minx} is larger than maxx: {maxx}")
        if miny >= maxy:
            raise ValueError(f"miny: {miny} is larger than maxy: {maxy}")

        ring = LinearRing(((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)))

        return cls(ring, crs)

    @classmethod
    def from_bounds(cls, minx, miny, maxx, maxy, *, crs="epsg:4326"):
        """
        Create a bounding box object from min and max values

        Parameters
        ----------
        minx : float
            Minimum values of the east-west direction.
        maxx : float
            Maximum values of the east-west direction.
        miny : float
            Minimum values of the south-north direction.
        maxy : float
            Maximum values of the south-north direction.
        crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`
            Defaults to "epsg:4326".

        Returns
        -------
        BBox
            A bounding box of the requested coordinates.

        """
        return cls.from_cornerpts(minx, miny, maxx, maxy, crs=crs)

    @classmethod
    def from_ds(cls, ds):
        """Create a bounding box object from a WindKit Dataset.

        Parameters
        ----------
        ds : xarray.Dataset
            WindKit formatted GIS dataset.

        Returns
        -------
        BBox
            A bounding box of the dataset.
        """
        we = ds.west_east
        sn = ds.south_north

        ring = LinearRing(
            (
                (we.min(), sn.min()),
                (we.max(), sn.min()),
                (we.max(), sn.max()),
                (we.min(), sn.max()),
            )
        )

        crs = pyproj.CRS.from_wkt(ds.crs.attrs["crs_wkt"])

        return cls(ring, crs)

    def reproject(self, to_crs, use_bounds=True):
        """Reproject a bounding box object.

        Parameters
        ----------
        to_crs : int, dict, str or pyproj.crs.CRS
            Value to initialize `pyproj.crs.CRS`

        Returns
        -------
        BBox
            The linestring in the requested projection.
        """
        to_crs = pyproj.CRS.from_user_input(to_crs)

        transformer = pyproj.Transformer.from_crs(self.crs, to_crs, always_xy=True)

        if use_bounds:
            new_bounds = transformer.transform_bounds(*self.bounds())
            return self.__class__.from_bounds(*new_bounds, crs=to_crs)
        else:
            ring = transform(transformer.transform, self.ring)
            return self.__class__(ring, to_crs)

    def reproject_to_utm(self):
        """Reproject a bounding box object to UTM.

        Returns
        -------
        BBox
            The linestring in the requested projection.
        """
        pt = gpd.GeoSeries(self.ring.centroid, crs=self.crs)
        crs_utm = pt.estimate_utm_crs()
        return self.reproject(crs_utm)

    def reproject_to_geographic(self):
        """Reproject a bounding box object to geographic coordinates.

        Returns
        -------
        BBox
            The linestring in the requested projection.
        """
        return self.reproject("epsg:4326")

    def buffer(self, distance, cap_style=3, join_style=2):
        """Buffer bounding box by fixed distance.

        Parameters
        ----------
        Distance : float
            Distance to buffer each direction.
        cap_style: :py:class:`shapely.BufferCapStyle` or {'round', 'square', 'flat'}
            Shape of buffered line endings, it is passed to :py:mod:`shapely.buffer`.
            Defaults to (3) 'square'

        join_style: :py:class:`shapely.BufferJoinStyle` or {'round', 'mitre', 'bevel'}
            Shape of bufered line midpoints, it is passed to  :py:mod:`shapely.buffer`.
            Defaults  to (2) 'mitre'

        Returns
        -------
        BBox
            New Bounding box object buffered by requested amount.
        """
        poly = Polygon([pt for pt in zip(*self.ring.xy)])
        # cap_style="square"(3), join_style="mitre"(2)
        poly = poly.buffer(float(distance), cap_style=cap_style, join_style=join_style)
        new_ring = LinearRing(poly.exterior.coords)
        return self.__class__(new_ring, self.crs)

    def envelope(self):
        """Create an envelope around the bounding box.

        Returns
        -------
        BBox
            New Bounding box object that is the envelope of the original.
        """
        bounds = self.bounds()
        return self.__class__.from_cornerpts(*bounds, crs=self.crs)

    def to_grid(self, spacing, heights):
        """Create a WindKit Grid starting from the minimum points of the bbox.

        Parameters
        ----------
        spacing : float
            Distance between each point.
        heights : float or 1D array
            Heights to include in the grid.

        Returns
        -------
        xarray.Dataset
            WindKit xarray dataset with dummy variable.

        Notes
        -----
        This assumes a "fence-post" approach to creating the grid, meaning that there may
        be a point that falls outside of the bounding box on the positive side.
        """
        from .spatial import create_dataset  # here to avoid circular import

        # Get x0, y0
        minx, miny, maxx, maxy = self.bounds()

        # get number of points in x and y dimension
        nx = int(np.round((maxx - minx) / spacing)) + 1
        ny = int(np.round((maxy - miny) / spacing)) + 1

        out_ds = create_dataset(
            np.arange(nx) * spacing + minx,
            np.arange(ny) * spacing + miny,
            heights,
            self.crs,
        )

        return _update_history(out_ds)

    def to_geoseries(self, geo_as_polygon=False):
        """Convert Bounding box to geopandas.Geoseries.

        Parameters
        ----------
        geo_as_polygon : bool, optional
            Convert the LinearRing to Polygon first, by default False.

        Returns
        -------
        geopandas.GeoSeries
            Bounding box converted to geoseries.
        """
        if geo_as_polygon:
            geo = self.polygon
        else:
            geo = self.ring
        return gpd.GeoSeries(geo, crs=self.crs)

    def plot(self, **kwargs):
        """Plot the bounding box."""
        ax = self.to_geoseries().plot(**kwargs)
        ax.set_aspect("equal")
        return ax
