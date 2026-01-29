"""
Defines a wind_turbines object

Wind turbines object can include groups of turbines.. Turbines are defined by their
position, and a mapping to a wind turbine generator.
"""

__all__ = [
    "validate_windturbines",
    "is_windturbines",
    "check_wtg_keys",
    "create_wind_turbines_from_dataframe",
    "create_wind_turbines_from_arrays",
    "wind_turbines_to_geodataframe",
]

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from numpy.typing import NDArray

from windkit.xarray_structures._validate import (
    _create_is_obj_function,
    _create_validation_wrapper_factory,
    _create_validator,
)
from windkit.spatial import create_dataset, get_crs

validate_windturbines = _create_validator(
    variables={},
    dims=["point"],
    coords=[
        "turbine_id",
        "group_id",
        "wtg_key",
    ],
)

_validate_windturbines_wrapper_factory = _create_validation_wrapper_factory(
    validate_windturbines
)

is_windturbines = _create_is_obj_function(validate_windturbines)


@_validate_windturbines_wrapper_factory(run_extra_checks=False)
def check_wtg_keys(wind_turbines: xr.Dataset, wtg_dict: dict):
    """Checks that all keys in a wind turbines object are there.

    Parameters
    ----------
    wind_turbines : xr.Dataset
        Wind turbines dataset like that created by the functions below.
    wtg_dict : dict
        Dictionary mapping keys to wind turbine generators
    """
    # Ensure all wtg_key values in the dataframe are in the supplied dictionary.
    missing_keys = []
    for wtg_key in np.unique(wind_turbines.wtg_key):
        if wtg_key not in wtg_dict.keys():
            missing_keys.append(wtg_key)
    if len(missing_keys) != 0:
        raise ValueError(
            f"Wind_turbines object includes the wtg_keys: {missing_keys}, that aren't in the wtg_dict."
        )


def create_wind_turbines_from_dataframe(
    location_df: pd.DataFrame | gpd.GeoDataFrame, crs: str | int = None
) -> xr.Dataset:
    """Creates a point dataset with required metadata from a dataframe.

    Parameters
    ----------
    location_df : pd.DataFrame | gpd.GeoDataFrame
        Dataframe with columns west_east, south_north, height, and wtg_key. Optional
        columns turbine_id, group_id can be set to give names to the turbine positions
        and groups. If not set turbine_id defaults to an integer from 0 to to the number of rows, and group_id defaults to 0.
    crs : str | int, optional
        Projection of the locations, by default None

    Returns
    -------
    xr.Dataset
        Windkit point dataset that includes the metadata needed for AEP calculations.

    Raises
    ------
    ValueError
        ValueError: if input is ill-formed.

    Examples
    --------
        >>> import pandas as pd
        >>> import windkit as wk
        >>> wts = create_wind_turbines_from_dataframe(pd.DataFrame(dict(west_east=[100., 200], south_north=[50., 150.], height=100., turbine_id=["Turb1", "Turb2"], wtg_key="DTU_10MW")), 32632)
    """

    # Set defaults for ids, if they aren't provided
    if "turbine_id" not in location_df.columns:
        location_df["turbine_id"] = range(len(location_df.index))

    if "group_id" not in location_df.columns:
        location_df["group_id"] = 0

    if type(location_df) is pd.DataFrame:
        if crs is None:
            raise ValueError("crs must be provided if location_df is a pd.DataFrame")

        # Return dataset with appropriate metadata
        locs = create_dataset(
            location_df.west_east,
            location_df.south_north,
            location_df.height,
            crs,
            struct="point",
        ).drop_vars("output")
    elif type(location_df) is gpd.GeoDataFrame:
        if location_df.crs is None and crs is None:
            raise ValueError("The GeoDataFrame must have a crs set")
        crs = location_df.crs if crs is None else crs

        locs = create_dataset(
            location_df.geometry.x,
            location_df.geometry.y,
            location_df.geometry.z,
            crs,
            struct="point",
        ).drop_vars("output")
    else:
        raise ValueError("location_df must be a pandas DataFrame or a GeoDataFrame")

    locs = locs.assign_coords(
        turbine_id=(("point",), location_df.turbine_id),
        group_id=(("point",), location_df.group_id),
        wtg_key=(("point",), location_df.wtg_key),
    )

    return locs


def create_wind_turbines_from_arrays(
    west_east: NDArray | list[float],
    south_north: NDArray | list[float],
    height: NDArray | list[float],
    wtg_keys: NDArray | list[int | str],
    turbine_ids: NDArray | list[int | str] | None = None,
    group_ids: NDArray | list[int | str] | None = None,
    crs: str | int = "EPSG:4326",
) -> xr.Dataset:
    """Creates a point dataset with required metadata from explicit arrays.

    Parameters
    ----------
    west_east : NDArray | list[float]
        west-east coordinates of the turbines.
    south_north : NDArray | list[float]
        south-north coordinates of the turbines.
    height : NDArray | list[float]
        height of the turbines.
    wtg_keys : NDArray | list[int  |  str]
        wtg_keys of the turbines.
    turbine_ids : NDArray | list[int  |  str] | None, optional
        turbine identifiers. If not set defaults to an integer from 0 to to the number of rows,
        by default None
    group_ids : NDArray | list[int  |  str] | None, optional
        group identifiers. If not set defaults to 0, by default None
    crs : _type_, optional
        Projection of the locations, by default "EPSG:4326"

    Raises
    ------
    ValueError
        ValueError: if input is ill-formed.

    Returns
    -------
    xr.Dataset
        Windkit point dataset that includes the metadata needed for AEP calculations.
    """

    def _validate_shapes():
        variables = [
            np.asarray(x)
            for x in [
                south_north,
                west_east,
                height,
                wtg_keys,
                turbine_ids,
                group_ids,
            ]
            if x is not None
        ]
        if not all(var.ndim == 1 for var in variables):
            raise ValueError("All arrays must be 1D arrays or lists of the same length")
        if not all(var.size == variables[0].size for var in variables):
            raise ValueError("All arrays must be 1D arrays or lists of the same length")

    _validate_shapes()

    ds = create_dataset(
        west_east, south_north, height, crs=crs, struct="point"
    ).drop_vars("output")

    # fill in defaults for turbine_ids and group_ids
    if turbine_ids is None:
        turbine_ids = np.arange(len(west_east))
    if group_ids is None:
        group_ids = np.zeros(len(west_east))

    ds = ds.assign_coords(
        turbine_id=(("point",), turbine_ids),
        group_id=(("point",), group_ids),
        wtg_key=(("point",), wtg_keys),
    )
    return ds


def wind_turbines_to_geodataframe(ds: xr.Dataset) -> gpd.GeoDataFrame:
    """Converts a wind turbine dataset to a geopandas dataframe.

    Parameters
    ----------
    ds : xr.Dataset
        Wind turbine dataset.

    Returns
    -------
    gpd.GeoDataFrame
        Geopandas dataframe with the turbine positions and metadata.
    """

    south_north = ds["south_north"].values
    west_east = ds["west_east"].values
    height = ds["height"].values
    turbine_id = ds["turbine_id"].values
    group_id = ds["group_id"].values
    wtg_key = ds["wtg_key"].values

    geometry = gpd.points_from_xy(west_east, south_north, height)
    gdf = gpd.GeoDataFrame(geometry=geometry, crs=get_crs(ds))
    gdf["turbine_id"] = turbine_id
    gdf["group_id"] = group_id
    gdf["wtg_key"] = wtg_key

    return gdf
