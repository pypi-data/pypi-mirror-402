"""
Data validation utilities for ProAlgoTrader Core.

This module provides helper functions for common data validation patterns
used across indicators and charts.
"""

import polars as pl
from typing import Optional, Any


def get_dataframe_row(
    data: Optional[pl.DataFrame], row_number: int, column_name: Optional[str] = None
) -> Any:
    """
    Get data from a DataFrame row with proper validation.

    Args:
        data: The DataFrame to access (can be None)
        row_number: The row number (0 = most recent, -1 = previous, etc.)
        column_name: Optional column name to extract specific value

    Returns:
        The requested data (full row or specific column value)

    Raises:
        Exception: If data is None, row_number is positive, or column not found
    """
    if data is None:
        raise Exception("Invalid dataframe")

    if row_number > 0:
        raise Exception("Invalid row number")

    actual_row_number = row_number - 1
    row_data = data[actual_row_number]

    if column_name:
        if column_name not in row_data.columns:
            raise Exception(
                f"Column '{column_name}' not found. Available: {row_data.columns}"
            )
        # Return scalar value instead of Series
        return row_data[column_name].item()

    return row_data
