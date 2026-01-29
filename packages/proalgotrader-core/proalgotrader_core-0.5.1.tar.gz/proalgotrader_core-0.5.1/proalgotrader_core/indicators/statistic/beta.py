"""
BETA - Beta

Category: Statistic Functions
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class BETA(Indicator):
    """
    BETA - Beta

    Category: Statistic Functions

    The Beta (BETA) is a statistical function that measures the volatility
    of a price series relative to another price series. It quantifies the
    systematic risk or sensitivity of one asset compared to another.

    BETA is useful for:
    - Risk analysis and portfolio management
    - Measuring systematic risk
    - Asset correlation analysis
    - Portfolio diversification
    - Risk-adjusted performance evaluation

    The calculation formula:
    BETA = Covariance(price0, price1) / Variance(price1)

    This statistical measure helps investors understand how much
    one asset moves relative to another over a specified time period.

    Parameters:
        price0: First price series column (default: "high")
        price1: Second price series column (default: "low")
        timeperiod: Time period for calculation (default: 5)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with beta column
    """

    def __init__(
        self,
        price0: str = "high",
        price1: str = "low",
        timeperiod: int = 5,
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.price0 = price0
        self.price1 = price1
        self.timeperiod = timeperiod

        base = prefix or f"beta_{timeperiod}_{price0}_{price1}"
        self.beta_col = base
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build BETA expression."""
        return Indicators.build_beta(
            high=pl.col(self.price0),
            low=pl.col(self.price1),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return BETA expressions."""
        return [self.build().alias(self.beta_col)]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.beta_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.price0, self.price1]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "BETA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("BETA requires a non-empty output column name")
            self.beta_col = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # BETA needs the timeperiod for calculation
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # BETA needs warmup data for stable statistical calculation
        return self.timeperiod
