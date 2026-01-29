"""
MAVP - Moving Average with Variable Period

Category: Overlap Studies
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class MAVP(Indicator):
    """
    MAVP - Moving Average with Variable Period

    Category: Overlap Studies

    The Moving Average with Variable Period (MAVP) calculates a moving average
    where the period length varies based on input data. This allows for adaptive
    smoothing that can respond to changing market conditions by adjusting the
    lookback period dynamically.

    The indicator takes two inputs:
    - real: The price data to be smoothed
    - periods: The variable period data that determines the lookback length

    Parameters:
        real: Input price data (default: "close")
        periods: Variable period data (default: "periods")
        minperiod: Minimum period length (default: 2)
        maxperiod: Maximum period length (default: 30)
        matype: Moving average type (default: 0 = SMA)
        output_columns: Optional custom output column names

    Returns:
        DataFrame with MAVP column
    """

    def __init__(
        self,
        real: str = "close",
        periods: str = "periods",
        minperiod: int = 2,
        maxperiod: int = 30,
        matype: int = 0,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.real = real
        self.periods = periods
        self.minperiod = minperiod
        self.maxperiod = maxperiod
        self.matype = matype
        self.output_column = f"mavp_{minperiod}_{maxperiod}_{matype}_{real}_{periods}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build MAVP expression."""
        return Indicators.build_mavp(
            source=pl.col(self.real),
            periods=pl.col(self.periods),
            minperiod=self.minperiod,
            maxperiod=self.maxperiod,
            matype=self.matype,
        )

    def expr(self) -> pl.Expr:
        """Return MAVP expression with alias."""
        return self.build().alias(self.output_column)

    def _exprs(self) -> List[pl.Expr]:
        """Return MAVP expressions."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.output_column]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.real, self.periods]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "MAVP expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("MAVP requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # MAVP uses variable periods, so we use the maximum period as window size
        return self.maxperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # MAVP needs warmup to establish stable variable period calculations
        return self.maxperiod
