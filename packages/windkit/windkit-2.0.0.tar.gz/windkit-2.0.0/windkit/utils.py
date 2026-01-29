# (c) 2024 DTU Wind Energy
"""
Collection of utility functions.
"""

__all__ = []

import zipfile
from pathlib import Path


def _infer_file_format(
    filename,
):
    """
    Infer the file format from the filename or type of file object.

    Parameters
    ----------
    filename : str or pathlib.Path
        File path

    Returns
    -------
    str
        File format.
    """

    if isinstance(filename, zipfile.ZipExtFile):
        file_format = "ZipExtFile"
    else:
        file_format = Path(filename).suffix.lower()[1:]

    return file_format
