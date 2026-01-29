"""Spatial decorators for windkit."""

__all__ = []

import functools

from xarray import DataArray, Dataset

from ._struct import get_spatial_struct
from .spatial import _spatial_stack, _spatial_unstack


def _stack_then_unstack(_func=None, *, merge_with_input=False):
    """Decorator to automatically run spatial stack before
    and spatial unstack after a function.

    Assumes that

    Parameters
    ----------
    _func : function
        Function to decorate
    merge_with_input : bool
        Whether to return result together with the input dataset, or just the
        stand-alone dataarray.
    """

    def decorator_stack_then_unstack(func):
        @functools.wraps(func)
        def wrapper_stack_then_unstack(*args, **kwargs):
            # Convert to mutable
            args = list(args)

            # The spatial object is assumed to be the first argument.
            ds = args[0].copy()

            # Treat case where struct is already point
            # Check the spatial structure of ds
            spatial_struct = get_spatial_struct(ds)
            # Stack the object if not point already
            if spatial_struct == "point":
                result = func(*args, **kwargs)
                # return standalone dataset or everything (merged with input)
                if merge_with_input:
                    return ds.merge(result)
                else:
                    return result

            # Stack the object
            stacked = _spatial_stack(ds)

            # Swap the first object with the stacked object
            args[0] = stacked

            # Run the function
            result = func(*args, **kwargs)

            # Merge with stacked dataset to get coords/dims/attrs and then unstack
            stacked = stacked.drop_vars(stacked.data_vars)
            if isinstance(result, Dataset):
                stacked = stacked.assign(result)
            elif isinstance(result, DataArray):
                stacked[result.name] = result
            result_unstacked = _spatial_unstack(stacked)

            # Return if result was a DataArray
            if isinstance(result, DataArray):
                return result_unstacked[result.name]

            # return standalone dataset or everything (merged with input)
            if merge_with_input:
                return ds.update(result_unstacked)
            else:
                return result_unstacked

        return wrapper_stack_then_unstack

    if _func is None:
        return decorator_stack_then_unstack
    else:
        return decorator_stack_then_unstack(_func)
