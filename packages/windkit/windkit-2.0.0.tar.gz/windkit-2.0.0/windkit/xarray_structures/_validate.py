# (c) 2022 DTU Wind Energy
"""
Package for validation of xarray objects
"""

from functools import wraps

from .._errors import WindkitValidationError


def _create_validator(
    variables=None, dims=None, coords=None, *, attrs=None, extra_checks=None
):
    """
    Factory to build validation functions for xarray datasets.

    Parameters
    ----------
    variables : dict, optional
        A dictionary of variables and their dimensions that must be present, by default None.
    dims : list, optional
        A list with the dimensions that should be present in the dataset.
    coords : list, optional
        A list with the coordinates that should be present in the dataset.
    attrs : list, optional
        A list with the attributes that should be present in the dataset.
    extra_checks : list, optional
        A list of functions that should be run to check the dataset, by default None.
        The functions should be of the form `func(obj)->obj`

    Returns
    -------
    function
        A function that validates the dataset.

    """

    if variables is None:
        variables = {}

    if dims is None:
        dims = []

    if coords is None:
        coords = []

    if attrs is None:
        attrs = {}

    def validator(obj, run_extra_checks=True):
        """
        Validation function.

        Parameters
        ----------
        obj : xarray.Dataset
            The object to validate.
        run_extra_checks : bool, optional
            If extra checks should be run (if present), by default True.

        Raises
        ------
        WindkitValidationError
            If the object is not valid.

        """

        errors = []

        for var, var_dims in variables.items():
            if var not in obj.data_vars:
                errors.append(f"{len(errors) + 1}. Missing variable: {var}")
            else:
                for dim in var_dims:
                    if dim not in obj[var].dims:
                        errors.append(
                            f"{len(errors) + 1}. Missing dimension {dim} on variable: {var}"
                        )

        # find missing dimensions
        for dim in dims:
            if dim not in obj.dims:
                errors.append(f"{len(errors) + 1}. Missing dimension: {dim}")

        # find missing coordinates
        for coord in coords:
            if coord not in obj.coords:
                errors.append(f"{len(errors) + 1}. Missing coordinate: {coord}")

        # find missing attributes
        for attr in attrs:
            if attr not in obj.attrs:
                errors.append(f"{len(errors) + 1}. Missing attribute: {attr}")

        # run extra checks
        if extra_checks is not None and run_extra_checks:
            for f in extra_checks:
                err_msg = f(obj)
                if err_msg is not None:
                    if isinstance(err_msg, str):
                        errors.append(f"{len(errors) + 1}. {err_msg}")
                    else:
                        for val in err_msg:
                            errors.append(f"{len(errors) + 1}. {val}")
        if errors:
            raise WindkitValidationError(
                f"validate found {len(errors)} errors \n" + "\n".join(errors)
            )

    return validator


def _create_validation_wrapper_factory(validator):
    """
    Create a validation wrapper for a function.

    NB: This function creates are decorator factory, not a decorator.
    So it should never be used as a unclosed decorator function like:
    @my_decorator_factory
    def my_function(obj):
        pass

    This is done to allow for the passing of arguments to the decorator.
    To use this to decorate a function, you need to call the returned function with the
    arguments you want to pass to the decorator.

    Example:
    my_decorator_factory = _create_validation_wrapper_factory_factory(my_validator)
    @my_decorator_factory(index=0)
    def my_function(obj):
        pass

    Parameters
    ----------
    validator : function
        The validation function to use.

    Returns
    -------
    function
        A function that first validates the object before calling the initial function.

    """

    def validation_decorator_factory(index=None, run_extra_checks=True):
        def validator_wrapper(func):
            """
            Validation function for the gwc data format.

            Parameters
            ----------
            func: function
                The function that should validate the object
            index: int, optional
                The index of the object in the function arguments, by default None
            run_extra_checks: bool, optional
                If extra checks should be run (if present), by default True

            Returns
            -------
            function
                A function that first validates the dataset and then calls the initial
                function.
            """

            @wraps(func)
            def validate(*args, **kwargs):
                if index is None:
                    index_ = 0
                else:
                    index_ = index

                obj = args[index_]

                # Do bwc checks
                validator(
                    obj, run_extra_checks=run_extra_checks
                )  # Raises ValueError if errors exist

                result = func(*args, **kwargs)
                return result

            return validate

        return validator_wrapper

    return validation_decorator_factory


def _create_is_obj_function(validator):
    """
    Create a function that checks if an object is valid.

    Parameters
    ----------
    validator : function
        The validation function to use.

    Returns
    -------
    function
        A function that checks if an object is valid.
    """

    def is_obj(obj, run_extra_checks=False):
        """
        Check that an object is valid.

        Parameters
        ----------
        obj : xarray.Dataset
            The object to check.

        Returns
        -------
        bool
            True if the object is valid, False otherwise.
        """
        try:
            validator(obj, run_extra_checks=run_extra_checks)
            return True
        except WindkitValidationError:
            return False

    return is_obj
