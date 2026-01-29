# (c) 2022 DTU Wind Energy
"""
Package exceptions message writing
"""


class UnsupportedFileTypeError(Exception):
    pass


class WindkitError(Exception):
    """Base class for windkit errors"""

    pass


class MultiPointError(WindkitError):
    """Error class to use when a single point is required, but multiple were applied"""

    def __init__(self):
        self.message = "Plotting multiple points is not supported now, please subset your dataset to a single point."
        super().__init__(self.message)


class IEC_type_error(WindkitError):
    """Error class to use when a single the IEC type is not well defined"""

    def __init__(self):
        self.message = "The IEC class is not correctly defined, please choose one between: IEC_I, IEC_II or IEC_III."
        super().__init__(self.message)


class PlottingAttrsError(WindkitError):
    """Error class to use when a single the IEC type is not well defined"""

    def __init__(self, errors, name):
        self.message = (
            f"The plot can't be displayed as the following attributes are not defined for '{name}' : \n"
            + "\n".join(errors)
            + "\nPlease, define a value for the empty attributes."
        )
        super().__init__(self.message)


class Missing_arguments(WindkitError):
    """Error class to use when no input in plotting function"""

    def __init__(self, func_name, errors):
        self.message = (
            f"{func_name} missing required positional argument:  \n" + "\n".join(errors)
        )
        super().__init__(self.message)


class WindkitValidationError(WindkitError):
    """Errror class to use when an xarray wind climate objetc is not well defined"""

    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)
