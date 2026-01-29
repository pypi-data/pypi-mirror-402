"""
MA - Moving Average (Generic)

Category: Overlap Studies
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class MA(Indicator):
    """
    MA - Moving Average (Generic)

    Category: Overlap Studies

    The Moving Average (MA) is a generic moving average indicator that provides
    flexibility in choosing the type of moving average calculation. This is a
    generic wrapper that can be configured to use different moving average types
    through the matype parameter.

    Moving Average Types (matype):
    0 = Simple Moving Average (SMA)
    1 = Exponential Moving Average (EMA)
    2 = Weighted Moving Average (WMA)
    3 = Double Exponential Moving Average (DEMA)
    4 = Triple Exponential Moving Average (TEMA)
    5 = Triangular Moving Average (TRIMA)
    6 = Kaufman Adaptive Moving Average (KAMA)
    7 = MESA Adaptive Moving Average (MAMA)
    8 = T3 Moving Average

    Parameters:
        real: Input price data (default: "close")
        timeperiod: Number of periods for the moving average (default: 30)
        matype: Type of moving average (default: 0 = SMA)
        output_columns: Optional custom output column names

    Returns:
        DataFrame with MA column
    """

    def __init__(
        self,
        real: str = "close",
        timeperiod: int = 30,
        matype: int = 0,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.real = real
        self.timeperiod = timeperiod
        self.matype = matype
        self.output_column = f"ma_{timeperiod}_{matype}_{real}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build MA expression."""
        return Indicators.build_ma(
            source=pl.col(self.real),
            timeperiod=self.timeperiod,
            matype=self.matype,
        )

    def expr(self) -> pl.Expr:
        """Return MA expression with alias."""
        return self.build().alias(self.output_column)

    def _exprs(self) -> List[pl.Expr]:
        """Return MA expressions."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.output_column]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.real]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "MA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("MA requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # Different MA types have different warmup requirements
        if self.matype in [0, 1, 2]:  # SMA, EMA, WMA
            return 0
        elif self.matype in [3, 4]:  # DEMA, TEMA
            return self.timeperiod
        elif self.matype == 5:  # TRIMA
            return (self.timeperiod + 1) // 2
        else:  # KAMA, MAMA, T3
            return self.timeperiod
