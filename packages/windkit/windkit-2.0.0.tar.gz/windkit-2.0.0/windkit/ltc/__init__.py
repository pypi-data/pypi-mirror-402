# (c) 2023 DTU Wind Energy
"""
A collection of functions for long term correction of wind time series.
"""

__all__ = [
    "LinRegMCP",
    "VarRatMCP",
    "calc_scores",
]

from .mcp import LinRegMCP, VarRatMCP
from .scores import calc_scores
