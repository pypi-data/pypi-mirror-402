# (c) 2024 DTU Wind Energy
"""
Class and associated methods to work with AEP uncertainty.
"""

__all__ = [
    "get_uncertainty_table",
    "validate_uncertainty_table",
    "total_uncertainty",
    "uncertainty_table_summary",
    "total_uncertainty_factor",
]

from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

MANDATORY_COLUMNS = ["uncertainty_kind", "uncertainty_name", "uncertainty_percentage"]
OPTIONAL_COLUMNS = [
    "uncertainty_category",
    "uncertainty_lower_bound",
    "uncertainty_upper_bound",
    "uncertainty_default",
    "description",
]

TABLES_DIR = Path(__file__).parent.parent / "data"


def get_uncertainty_table(table_name="dtu_default"):
    """Get the wind and energy uncertainty DataFrame from the supported uncertainty tables.

    The uncertainty table contains information about various types of uncertainties.
    Mandatory fields of an uncertainty table are: names and values of the uncertainties (as a percentage of total energy [%]).
    Optional fields are: category, lower and upper bounds, default values, and descriptions.

    Parameters
    ----------
    table_name : str
        The name of the uncertainty table to get. Default is 'dtu_default'.

    Returns
    -------
    DataFrame
        DataFrame containing both wind and energy uncertainties.

    Raises
    ------
    ValueError
        If the table_name is not one of the supported tables.

    Notes
    -----
    This function merges the wind and energy uncertainty dictionary tables into a single DataFrame.

    Examples
    --------
    >>> get_uncertainty_table('dtu_default')
    """
    if table_name == "dtu_default":
        dtu_table_path = TABLES_DIR / "uncertainty_tables/dtu_uncertainty_table.csv"
        uncertainty_table = pd.read_csv(dtu_table_path)

        # Reorder columns to have 'uncertainty_kind' as the first column
        cols = ["uncertainty_kind"] + [
            col for col in uncertainty_table.columns if col != "uncertainty_kind"
        ]
        uncertainty_table = uncertainty_table[cols]

        return uncertainty_table

    else:
        raise ValueError(
            f"Only 'dtu_default' is supported as table_name. Got '{table_name}' instead."
        )


def validate_uncertainty_table(uncertainty_table):
    """Perform several checks to ensure that an uncertainty table DataFrame is valid.

    Parameters
    ----------
    uncertainty_table : DataFrame
        The DataFrame containing the uncertainties.

    Raises
    ------
    ValueError
        - If mandatory columns are missing, are incorrectly defined, or contain missing values.
        - If the uncertainty_kind column contains values other than 'wind' or 'energy'.
        - If the uncertainty_percentage column contains invalid data types.
        - If uncertainty_percentage values are outside the specified bounds.

    Notes
    -----
    - The function assumes that the DataFrame columns are named exactly as specified in the mandatory columns list:
      MANDATORY_COLUMNS = ['uncertainty_kind', 'uncertainty_name', 'uncertainty_percentage'].
    - The 'uncertainty_percentage' values must be within the range specified by 'uncertainty_lower_bound' and 'uncertainty_upper_bound' for each row, if these are present.

    Examples
    --------
    >>> uncertainty_table = get_uncertainty_table('dtu_default')
    >>> validate_uncertainty_table(uncertainty_table)
    """
    # Check if all mandatory columns are present and if uncertainty_kind column contains only 'wind' or 'energy' strings
    for col in MANDATORY_COLUMNS:
        if col not in uncertainty_table.columns:
            raise ValueError(f"Mandatory column '{col}' is missing from the DataFrame.")
        if col == "uncertainty_kind":
            if not all(uncertainty_table[col].isin(["wind", "energy"])):
                raise ValueError(
                    f"Column '{col}' should only contain 'wind' or 'energy' strings."
                )

    # Check if mandatory columns have no missing values and check that uncertainty_percentage values are numbers
    for col in MANDATORY_COLUMNS:
        if uncertainty_table[col].isnull().any():
            raise ValueError(f"Mandatory column '{col}' contains missing values.")
        if col == "uncertainty_percentage":
            if not is_numeric_dtype(uncertainty_table[col]):
                raise ValueError(
                    f"Mandatory column '{col}' should contain only floats or integers."
                )

    # Check if value is between lower_bound and upper_bound
    if (
        "uncertainty_lower_bound" in uncertainty_table.columns
        and "uncertainty_upper_bound" in uncertainty_table.columns
    ):
        for i in range(len(uncertainty_table)):
            lower_bound = uncertainty_table["uncertainty_lower_bound"][i]
            upper_bound = uncertainty_table["uncertainty_upper_bound"][i]
            uncertainty_percentage = uncertainty_table["uncertainty_percentage"][i]
            if (
                uncertainty_percentage < lower_bound
                or uncertainty_percentage > upper_bound
            ):
                raise ValueError(
                    f"Uncertainty_percentage value {uncertainty_percentage} is outside of bounds ({lower_bound}, {upper_bound}) for row {i}"
                )


def total_uncertainty(uncertainty_table, sensitivity_factor=1.5):
    """Calculate the total uncertainty in the DataFrame.

    Parameters
    ----------
    uncertainty_table : DataFrame
        The DataFrame containing the uncertainties.
    sensitivity_factor : float
        The sensitivity factor value.

    Returns
    -------
    tuple[float, float, float]
        A tuple containing:
        - The total uncertainty value as a percentage of total AEP [%]. (i.e non-dimensional).
        - The total wind uncertainty relative to the mean predicted wind speed in the wind farm [%].
        - The total uncertainty from technical losses affecting the energy as a percentage of total AEP [%].

    Examples
    --------
    >>> uncertainty_table = get_uncertainty_table('dtu_default')
    >>> sensitivity_factor = sensitivity_factor(pwc, wtg, wind_perturbation_factor=0.05)
    >>> total_uncertainty(uncertainty_table, sensitivity_factor)
    """
    uncertainty_table = uncertainty_table.copy()

    # Retrieve all the wind uncertainties percentages and perform the sum of the squares
    wind_uncertainty_table = uncertainty_table[
        uncertainty_table["uncertainty_kind"] == "wind"
    ]
    wind_uncertainty_sigmas = np.array(
        wind_uncertainty_table["uncertainty_percentage"].values
    )
    wind_uncertainty = np.sqrt(np.sum(wind_uncertainty_sigmas**2))

    # Retrieve all the energy uncertainties percentages and perform the sum of the squares
    energy_uncertainty_table = uncertainty_table[
        uncertainty_table["uncertainty_kind"] == "energy"
    ]
    energy_uncertainty_sigmas = np.array(
        energy_uncertainty_table["uncertainty_percentage"].values
    )
    energy_uncertainty = np.sqrt(np.sum(energy_uncertainty_sigmas**2))

    total_uncertainty_value = np.sqrt(
        (sensitivity_factor * wind_uncertainty) ** 2 + energy_uncertainty**2
    )

    return total_uncertainty_value, wind_uncertainty, energy_uncertainty


def uncertainty_table_summary(uncertainty_table, sensitivity_factor=1.5):
    """Print a summary of the uncertainties in the DataFrame.

    Parameters
    ----------
    uncertainty_table : DataFrame
        The DataFrame containing the uncertainties.
    sensitivity_factor : float, optional
        The sensitivity factor value to be included in the summary. Default is 1.5.

    Examples
    --------
    >>> uncertainty_table = get_uncertainty_table('dtu_default')
    >>> sensitivity_factor = sensitivity_factor(pwc, wtg, wind_perturbation_factor=0.05)
    >>> uncertainty_table_summary(uncertainty_table, sensitivity_factor)
    """

    # Create a list to store the rows for the summary DataFrame
    summary_rows = []

    # Populate the summary rows
    for _, row in uncertainty_table.iterrows():
        if row["uncertainty_kind"] == "wind":
            wind_speed_uncertainty = row["uncertainty_percentage"]
            energy_uncertainty = wind_speed_uncertainty * sensitivity_factor
            summary_rows.append(
                {
                    "Uncertainty kind": "wind",
                    "Uncertainty name": row["uncertainty_name"],
                    "Wind Speed Uncertainty (%)": wind_speed_uncertainty,
                    "Sensitivity Factor": sensitivity_factor,
                    "Energy Uncertainty (%)": energy_uncertainty,
                }
            )
        elif row["uncertainty_kind"] == "energy":
            summary_rows.append(
                {
                    "Uncertainty kind": "energy",
                    "Uncertainty name": row["uncertainty_name"],
                    "Wind Speed Uncertainty (%)": "",
                    "Sensitivity Factor": "",
                    "Energy Uncertainty (%)": row["uncertainty_percentage"],
                }
            )

    # Calculate total uncertainties
    (
        total_uncertainty_value,
        total_wind_uncertainty,
        total_energy_uncertainty,
    ) = total_uncertainty(uncertainty_table, sensitivity_factor)

    total_energy_uncertainty_from_wind = total_wind_uncertainty * sensitivity_factor

    # Add total uncertainty rows
    summary_rows.append(
        {
            "Uncertainty kind": "Total Wind Uncertainty (%)",
            "Uncertainty name": "",
            "Wind Speed Uncertainty (%)": total_wind_uncertainty,
            "Sensitivity Factor": sensitivity_factor,
            "Energy Uncertainty (%)": total_energy_uncertainty_from_wind,
        }
    )
    summary_rows.append(
        {
            "Uncertainty kind": "Total Energy Uncertainty (%)",
            "Uncertainty name": "",
            "Wind Speed Uncertainty (%)": "",
            "Sensitivity Factor": "",
            "Energy Uncertainty (%)": total_energy_uncertainty,
        }
    )

    # Add final row for total uncertainty
    summary_rows.append(
        {
            "Uncertainty kind": "Total Uncertainty (%)",
            "Uncertainty name": "",
            "Wind Speed Uncertainty (%)": "",
            "Sensitivity Factor": "",
            "Energy Uncertainty (%)": total_uncertainty_value,
        }
    )

    # Create the summary DataFrame from the list of rows
    summary_df = pd.DataFrame(summary_rows)

    return print(summary_df.to_string(index=False))


def compute_factor(p):
    """Convert percentiles to PPF values"""
    from scipy.stats import norm

    if isinstance(p, (list, tuple, np.ndarray)):
        return norm.ppf(np.asarray(p) / 100)  # Returns NumPy array
    return norm.ppf(float(p) / 100)


def total_uncertainty_factor(uncertainty_table, sensitivity_factor=1.5, percentile=90):
    """Calculate the total uncertainty factor for a given exceedance probability or a list of probabilities.

    Parameters
    ----------
    uncertainty_table : DataFrame
        The DataFrame containing the uncertainties.
    sensitivity_factor : float
        The sensitivity factor that multiplies the wind uncertainty terms.
    percentile : int, float, or list/tuple of int/float
        The exceedance probability or probabilities (Pxx) for which to calculate the uncertainty factor.
        Default is 90 (for P90).

    Returns
    -------
    float or list of float
        The total uncertainty factor(s) that can be multiplied by the net_aep to get the Px value(s).

    Notes
    -----
    - The function to calculate the value of AEP associated with a given exceedance probability is:
      Px = net_aep * (1 - ppf * total_uncertainty_value / 100), where:
    - ppf is the quantile (inverse CDF) corresponding to the given probability, for a normal distribution (mu=0, sigma=1).

    Examples
    --------
    >>> uncertainty_table = get_uncertainty_table('dtu_default')
    >>> sensitivity_factor = sensitivity_factor(pwc, wtg, wind_perturbation_factor=0.05)
    >>> total_uncertainty_factor(uncertainty_table, sensitivity_factor, percentile=90)
    >>> total_uncertainty_factor(uncertainty_table, sensitivity_factor, percentile=[90, 95, 99])
    """
    total_uncertainty_value, _, _ = total_uncertainty(
        uncertainty_table, sensitivity_factor
    )

    ppf = compute_factor(percentile)

    total_uncertainty_factor = 1 - (ppf * (total_uncertainty_value / 100))

    return total_uncertainty_factor
