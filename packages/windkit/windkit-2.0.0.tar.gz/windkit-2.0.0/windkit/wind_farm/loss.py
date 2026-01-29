# (c) 2024 DTU Wind Energy
"""
Class and associated methods to work with AEP losses.
"""

__all__ = [
    "get_loss_table",
    "validate_loss_table",
    "total_loss",
    "loss_table_summary",
    "total_loss_factor",
]

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from pathlib import Path

MANDATORY_COLUMNS = ["loss_name", "loss_percentage"]
OPTIONAL_COLUMNS = [
    "loss_category",
    "loss_lower_bound",
    "loss_upper_bound",
    "loss_default",
    "description",
]

TABLES_DIR = Path(__file__).parent.parent / "data"


def get_loss_table(table_name="dtu_default"):
    """Get a DataFrame from the supported loss tables.

    The loss table contains information about various types of losses.
    Mandatory fields of a loss table are: names and values of the losses (as a percentage of total energy [%]).
    Optional fields are: category, lower and upper bounds, default values, and descriptions.

    +----------------------------+-------------------+----------------+------------------+--------------------+--------------+-------------+
    | loss_name                  | loss_percentage   | loss_category  | loss_lower_bound | loss_upper_bound   | loss_default | description |
    +============================+===================+================+==================+====================+==============+=============+
    | Turbine_Availability       | 3.0               | Availability   | 0                | 5                  | 3.0          | des1        |
    | Balance_plant_availability | 0.0               | Availability   | 0                | 5                  | 0.0          | des2        |
    | Grid_availability          | 0.0               | Availability   | 0                | 5                  | 0.0          | des3        |
    | Electrical_ope             | 1.0               | Electrical     | 0                | 5                  | 1.0          | des4        |
    | WF_consumption             | 1.0               | Electrical     | 0                | 5                  | 1.0          | des5        |
    +----------------------------+-------------------+----------------+------------------+--------------------+--------------+-------------+

    Parameters
    ----------
    table_name : str
        The name of the table to get. Default is 'dtu_default'.

    Returns
    -------
    DataFrame
        The DataFrame containing the loss table.

    Notes
    -----
    - There is no fixed order of columns in a loss table. Methods work with the columns based on their names.
    - The names of the columns must follow the syntax shown in the example table above.

    Examples
    --------
    >>> get_loss_table('dtu_default')
    """
    if table_name == "dtu_default":
        dtu_table_path = TABLES_DIR / "loss_tables/dtu_loss_table.csv"
        return pd.read_csv(dtu_table_path)
    else:
        raise ValueError(
            f"Only 'dtu_default' is supported as table_name. Got '{table_name}' instead."
        )


def validate_loss_table(loss_table):
    """Perform several checks to ensure that the loss table DataFrame is valid.

    Parameters
    ----------
    loss_table : DataFrame
        The DataFrame containing the losses.

    Raises
    ------
    ValueError
        - If mandatory columns are missing, incorrectly defined, or contain missing values.
        - If the loss_percentage column contains invalid data types.
        - If loss_percentage values are outside the specified bounds.

    Notes
    -----
    - The function assumes that the DataFrame columns are named exactly as specified in the mandatory columns list:
      MANDATORY_COLUMNS = ['loss_name', 'loss_percentage'].
    - The 'loss_percentage' values must be within the range specified by 'loss_lower_bound' and 'loss_upper_bound' for each row, if these are present.

    Examples
    --------
    >>> loss_table = get_loss_table('dtu_default')
    >>> validate_loss_table(loss_table)
    """
    # Check if all mandatory columns are present
    for col in MANDATORY_COLUMNS:
        if col not in loss_table.columns:
            raise ValueError(f"Mandatory column '{col}' is missing from the DataFrame.")

    # Check if mandatory columns have no missing values and check that loss_percentage values are numbers
    for col in MANDATORY_COLUMNS:
        if loss_table[col].isnull().any():
            raise ValueError(f"Mandatory column '{col}' contains missing values.")
        if col == "loss_percentage":
            if not is_numeric_dtype(loss_table[col]):
                raise ValueError(
                    f"Mandatory column '{col}' should contain only floats or integers."
                )

    # Check if value is between lower_bound and upper_bound
    if (
        "loss_lower_bound" in loss_table.columns
        and "loss_upper_bound" in loss_table.columns
    ):
        for i in range(len(loss_table)):
            lower_bound = loss_table["loss_lower_bound"][i]
            upper_bound = loss_table["loss_upper_bound"][i]
            loss_percentage = loss_table["loss_percentage"][i]
            if loss_percentage < lower_bound or loss_percentage > upper_bound:
                raise ValueError(
                    f"Loss_percentage value {loss_percentage} is outside of bounds ({lower_bound}, {upper_bound}) for row {i}"
                )


def total_loss(loss_table):
    """Calculate the total losses in the DataFrame.

    Parameters
    ----------
    loss_table : DataFrame
        The DataFrame containing the losses.

    Returns
    -------
    float
        The total loss value as a percentage.
    """
    return np.sum(loss_table["loss_percentage"])


def loss_table_summary(loss_table):
    """Print a summary of the losses in the DataFrame.

    Parameters
    ----------
    loss_table : DataFrame
        The DataFrame containing the losses.
    """

    # Group by loss_category and sum the Value column
    category_totals = loss_table.groupby("loss_category")["loss_percentage"].sum()
    # Calculate the total losses
    total_losses = total_loss(loss_table)
    # Create the summary string
    summary = "Loss Summary:\n"
    for category, total in category_totals.items():
        summary += f"Total value of losses for {category}: {total} %\n"
    summary += f"Total value of all losses: {total_losses} %"

    return print(summary)


def total_loss_factor(loss_table):
    """Calculate the total loss factor in the DataFrame.

    Parameters
    ----------
    loss_table : DataFrame
        The DataFrame containing the losses.

    Returns
    -------
    float
        The total loss factor value as a percentage.
    """
    total_loss_value = total_loss(loss_table)

    return 1 - total_loss_value / 100
