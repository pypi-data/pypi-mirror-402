
(c) DTU Wind Energy

# windkit.spatial

The WindKit spatial package is a collection of functions for working with
geospatial objects supported by WindKit.

The supported objects include:

 1. Vector Maps in the form of geopandas objects: GeoDataFrame's and GeoSeries's
 2. Array-like data in the form of xarray objects: DataArray's and xarray.Dataset's. Three public structures of array-like objects are supported as well as two private structures:
    1. **point** (..., *point*) with x, y, and z-coordinates each of length *point*
    2. **stacked_point** (..., *stacked_point*) with x, y-coordiantes each of length *stacked_point*
    3. **cuboid** (..., *height*, *south_north*, *west_east*) this requires regular spacing in the *south_north* and *west_east* dimensions
    4. **raster** (..., *south_north*, *west_east*) this is an internal structure that behaves like a 2D **cuboid**
    5. **vertical** (..., 'height') This is just the height dimension



### Overview of modules:
 * `spatial.py`: contains the user-facing API's and calls appropriate functions for each type+structure.
 * `crs.py`: code for working with Coordinate Reference System's.
 * `bbox.py`: Code for working with bounding boxes.
 * `vector.py`: contains vector related spatial functions.
 * `dimensions.py`: defines spatial dimension names and order for array objects
 * `struct.py`: functions for checking the structure of array objects
 * `point.py`: functions for working with point-like array objects
 * `raster.py`: functions for working with raster-like array objects (including cuboid's)
 * `vertical.py`: functions for working with vertical data.
 * `utm.py`: code for working with UTM zones.
