import numpy as np

from ._raster import to_raster
from .spatial import create_dataset


def to_cuboid(obj, ignore_raster_check=False):
    """Converts a point based object to a cuboid based object

    Parameters
    ----------
    obj : xarray.Dataset, xarray.DataArray
        WindKit xarray dataset or dataarray containing spatial
        dimensions and CRS variable
    ignore_raster_check : bool
        Check if the object satisfy the requirements to become a raster
        Default set to False (i.e., not to check)

    Returns
    -------
    xarray.Dataset, xarray.DataArray
        Raster version of WindKit xarray dataset or dataarray

    Raises
    ------
    ValueError
        If dataset cannot be converted to cuboid
    """
    return to_raster(obj, ignore_raster_check=ignore_raster_check)


def _create_isotropic_cuboid(
    cmin,
    cmax,
    nx,
    ny,
    nz,
    crs="EPSG:32632",
    data_values="manhatten_distance",
    include_string_array=False,
    extra_dims=None,
):
    """
    Create a cuboid with isotropic coordinates.
    The cuboid dataset contains variables with different spatial dimensions. These
    variables are can be filled with different data values. The data values can be
    either random, manhatten distance or isotropic.

    Parameters
    ----------
    cmin, cmax : float

    nx, ny, nz : int
        Dimension sizes of each spatial dimension of the cuboid.

    crs : str, optional
        Coordinate reference system of the cuboid. Default is "EPSG:32632",
        which is the UTM32N coordinate reference system.

    data_values : str, optional
        Data values of the cuboid. Default is "manhatten_distance".
        Options are "random", "manhatten_distance" and "isotropic".
        * "manhatten_distance" is the distance from the origin (0, 0, 0) in
        descrete x, y, or z-steps of 1.
        * "equlidian_distance" is the distance from the origin (0, 0, 0)
        in continous euclidean distance matching the coordinates.
        * "random"  is random data values between 0 and 1.

    extra_dims : dict, optional
        Extra dimensions to add to the cuboid. Default is None, which means
        no extra dimensions are added.

    Returns
    -------
    cuboid : xarray.Dataset
        Cuboid dataset with isotropic coordinates containing variables with
        different spatial dimensions and data values following the chosen
        data_values option.

    Examples
    --------
    >>> import windkit as wk
    >>> cube = wk.spatial._create_isotropic_cuboid(0, 1, 2, 2, 2, crs="EPSG:32632")
    >>> cube
    <xarray.Dataset>
    Dimensions:      (height: 2, south_north: 2, west_east: 2)
    Coordinates:
        * west_east    (west_east) float64 0.0 1.0
        * south_north  (south_north) float64 0.0 1.0
        * height       (height) float64 0.0 1.0
    Data variables:
        z            (height) float64 0.0 1.0
        xy           (south_north, west_east) float64 0.0 1.0 0.0 1.0
        xyz          (height, south_north, west_east) float64 0.0 1.0 1.0 2.0 1.0 2.0 2.0 3.0
        string_array  (height) <U1 's' 's'
    Attributes:
        crs:      EPSG:32632

    Raises
    ------
    ValueError
        If data_values is not "random", "manhatten_distance" or "isotropic".

    """

    if extra_dims is None:
        extra_dims = {}

    cube = create_dataset(
        np.linspace(cmin, cmax, nx),
        np.linspace(cmin, cmax, ny),
        np.linspace(cmin, cmax, nz),
        struct="cuboid",
        crs=crs,
    ).drop_vars(["output"])

    if include_string_array:
        cube["string_array"] = (["height"], ["s"] * nz)

    if data_values == "manhatten_distance":
        cube["z"] = (["height"], np.arange(nz))
        cube["z"] = cube["z"].astype(np.float64)

        cube["yx"] = (
            ["south_north", "west_east"],
            np.arange(ny)[:, None] + np.arange(nx)[None, :],
        )
        cube["yx"] = cube["yx"].astype(np.float64)

        cube["zyx"] = (
            ["height", "south_north", "west_east"],
            np.arange(nz)[:, None, None]
            + np.arange(ny)[None, :, None]
            + np.arange(nx)[None, None, :],
        )
        cube["zyx"] = cube["zyx"].astype(np.float64)

    elif data_values == "contant":
        cube["z"] = (["height"], np.ones(nz))
        cube["yx"] = (["south_north", "west_east"], np.ones((ny, nx)))
        cube["zyx"] = (
            ["height", "south_north", "west_east"],
            np.ones((nz, ny, nx)),
        )

    elif data_values == "random":
        cube["z"] = (["height"], np.random.rand(nz))
        cube["yx"] = (["south_north", "west_east"], np.random.rand(ny, nx))
        cube["yzx"] = (
            ["height", "south_north", "west_east"],
            np.random.rand(nz, ny, nx),
        )

    elif data_values == "euqlidian_distance":
        cube["z"] = (["height"], np.linspace(cmin, cmax, nz))
        cube["yx"] = (
            ["south_north", "west_east"],
            np.sqrt(
                np.linspace(cmin, cmax, ny)[:, None] ** 2
                + np.linspace(cmin, cmax, nx)[None, :] ** 2
            ),
        )
        cube["zyx"] = (
            ["height", "south_north", "west_east"],
            np.sqrt(
                np.linspace(cmin, cmax, nz)[:, None, None] ** 2
                + np.linspace(cmin, cmax, ny)[None, :, None] ** 2
                + np.linspace(cmin, cmax, nx)[None, None, :] ** 2
            ),
        )

    else:
        raise ValueError(
            "data_values must be either 'random', 'constant', 'manhatten_distance' or 'euqlidian_distance'. Got {}".format(
                data_values
            )
        )

    if any(extra_dims.keys()):
        cube = cube.expand_dims(**extra_dims)

    return cube
