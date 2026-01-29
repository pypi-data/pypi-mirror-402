"""
SAREXT - Parabolic SAR Extended (Stop and Reverse Extended)

Category: Overlap Studies
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class SAREXT(Indicator):
    """
    SAREXT - Parabolic SAR Extended (Stop and Reverse Extended)

    Category: Overlap Studies

    The Parabolic SAR Extended is an enhanced version of the Parabolic SAR that
    provides more flexibility in parameter configuration. It allows separate
    acceleration factors for long and short positions, providing more control
    over the indicator's sensitivity to price changes.

    Formula: SAR = Previous SAR + AF * (EP - Previous SAR)
    Where:
    - AF (Acceleration Factor) can be different for long and short positions
    - EP (Extreme Point) is the highest high in an uptrend or lowest low in a downtrend
    - Separate acceleration parameters for long and short positions

    Parameters:
        high: High price data (default: "high")
        low: Low price data (default: "low")
        startvalue: Starting value for SAR (default: 0)
        offsetonreverse: Offset on reverse (default: 0)
        accelerationinitlong: Initial acceleration for long positions (default: 0.02)
        accelerationlong: Acceleration increment for long positions (default: 0.02)
        accelerationmaxlong: Maximum acceleration for long positions (default: 0.2)
        accelerationinitshort: Initial acceleration for short positions (default: 0.02)
        accelerationshort: Acceleration increment for short positions (default: 0.02)
        accelerationmaxshort: Maximum acceleration for short positions (default: 0.2)
        output_columns: Optional custom output column names

    Returns:
        DataFrame with SAREXT column
    """

    def __init__(
        self,
        high: str = "high",
        low: str = "low",
        startvalue: float = 0,
        offsetonreverse: float = 0,
        accelerationinitlong: float = 0.02,
        accelerationlong: float = 0.02,
        accelerationmaxlong: float = 0.2,
        accelerationinitshort: float = 0.02,
        accelerationshort: float = 0.02,
        accelerationmaxshort: float = 0.2,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.high = high
        self.low = low
        self.startvalue = startvalue
        self.offsetonreverse = offsetonreverse
        self.accelerationinitlong = accelerationinitlong
        self.accelerationlong = accelerationlong
        self.accelerationmaxlong = accelerationmaxlong
        self.accelerationinitshort = accelerationinitshort
        self.accelerationshort = accelerationshort
        self.accelerationmaxshort = accelerationmaxshort
        self.output_column = f"sarext_{accelerationinitlong}_{accelerationmaxlong}_{accelerationinitshort}_{accelerationmaxshort}_{high}_{low}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build SAREXT expression."""
        return Indicators.build_sarext(
            high=pl.col(self.high),
            low=pl.col(self.low),
            startvalue=self.startvalue,
            offsetonreverse=self.offsetonreverse,
            accelerationinitlong=self.accelerationinitlong,
            accelerationlong=self.accelerationlong,
            accelerationmaxlong=self.accelerationmaxlong,
            accelerationinitshort=self.accelerationinitshort,
            accelerationshort=self.accelerationshort,
            accelerationmaxshort=self.accelerationmaxshort,
        )

    def expr(self) -> pl.Expr:
        """Return SAREXT expression with alias."""
        return self.build().alias(self.output_column)

    def _exprs(self) -> List[pl.Expr]:
        """Return SAREXT expressions."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.output_column]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.high, self.low]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "SAREXT expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "SAREXT requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # SAREXT doesn't have a fixed window size, but needs at least 2 periods to start
        return 2

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # SAREXT needs a few periods to establish trend direction
        return 5
