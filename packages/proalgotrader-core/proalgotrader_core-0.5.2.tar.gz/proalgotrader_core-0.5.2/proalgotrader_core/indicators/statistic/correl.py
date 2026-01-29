"""
CORREL - Pearson's Correlation Coefficient

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class CORREL(Indicator):
    """
    CORREL - Pearson's Correlation Coefficient

    Category: Statistic Functions

    The Pearson's Correlation Coefficient (CORREL) is a statistical function that
    measures the linear correlation between two price series. It quantifies the
    strength and direction of the linear relationship between the variables.

    CORREL is useful for:
    - Measuring linear relationships between assets
    - Portfolio diversification analysis
    - Risk management and correlation analysis
    - Market relationship studies
    - Statistical analysis and research

    The calculation formula:
    CORREL = Covariance(price0, price1) / (StdDev(price0) * StdDev(price1))

    This statistical measure ranges from -1 to +1, where:
    - +1 indicates perfect positive correlation
    - -1 indicates perfect negative correlation
    - 0 indicates no linear correlation

    Parameters:
        price0: First price series column (default: "high")
        price1: Second price series column (default: "low")
        timeperiod: Time period for calculation (default: 30)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with correl column
    """

    def __init__(
        self,
        price0: str = "high",
        price1: str = "low",
        timeperiod: int = 30,
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.price0 = price0
        self.price1 = price1
        self.timeperiod = timeperiod

        base = prefix or f"correl_{timeperiod}_{price0}_{price1}"
        self.correl_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build CORREL expression."""
        return Indicators.build_correl(
            high=pl.col(self.price0),
            low=pl.col(self.price1),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return CORREL expressions."""
        return [self.build().alias(self.correl_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.correl_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price0, self.price1]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "CORREL expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("CORREL requires a non-empty output column name")
            self.correl_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # CORREL needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # CORREL needs warmup data for stable statistical calculation
        return self.timeperiod
