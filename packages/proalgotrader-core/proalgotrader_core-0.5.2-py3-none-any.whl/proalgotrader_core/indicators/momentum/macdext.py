"""
MACDEXT - MACD with Controllable MA Type

Category: Momentum Indicators
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class MACDEXT(Indicator):
    """
    MACDEXT - MACD with Controllable MA Type

    Category: Momentum Indicators

    The MACD with Controllable MA Type (MACDEXT) is an enhanced version of the
    standard MACD indicator that allows you to specify different moving average
    types for the fast, slow, and signal lines. This provides more flexibility
    in customizing the MACD calculation to suit different trading strategies.

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
        fastperiod: Fast MA period (default: 12)
        fastmatype: Fast MA type (default: 0 = SMA)
        slowperiod: Slow MA period (default: 26)
        slowmatype: Slow MA type (default: 0 = SMA)
        signalperiod: Signal MA period (default: 9)
        signalmatype: Signal MA type (default: 0 = SMA)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with MACD, MACD signal, and MACD histogram columns
    """

    def __init__(
        self,
        real: str = "close",
        fastperiod: int = 12,
        fastmatype: int = 0,
        slowperiod: int = 26,
        slowmatype: int = 0,
        signalperiod: int = 9,
        signalmatype: int = 0,
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.real = real
        self.fastperiod = fastperiod
        self.fastmatype = fastmatype
        self.slowperiod = slowperiod
        self.slowmatype = slowmatype
        self.signalperiod = signalperiod
        self.signalmatype = signalmatype

        base = (
            prefix
            or f"macdext_{fastperiod}_{fastmatype}_{slowperiod}_{slowmatype}_{signalperiod}_{signalmatype}_{real}"
        )
        self.macd_col = f"{base}"
        self.signal_col = f"{base}_signal"
        self.hist_col = f"{base}_hist"

        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build MACDEXT expression."""
        return Indicators.build_macdext(
            source=pl.col(self.real),
            fastperiod=self.fastperiod,
            fastmatype=self.fastmatype,
            slowperiod=self.slowperiod,
            slowmatype=self.slowmatype,
            signalperiod=self.signalperiod,
            signalmatype=self.signalmatype,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return MACDEXT expressions."""
        macdext_result = self.build()
        return [
            macdext_result.struct.field("macd").alias(self.macd_col),
            macdext_result.struct.field("macdsignal").alias(self.signal_col),
            macdext_result.struct.field("macdhist").alias(self.hist_col),
        ]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.macd_col, self.signal_col, self.hist_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.real]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 3:
                raise ValueError(
                    "MACDEXT expects exactly 3 output column names in 'output_columns'"
                )
            macd_col, signal_col, hist_col = self._requested_output_columns
            cols = [macd_col, signal_col, hist_col]
            if any(not isinstance(c, str) or not c for c in cols):
                raise ValueError("MACDEXT requires three non-empty output column names")
            self.macd_col, self.signal_col, self.hist_col = cols

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        return max(self.fastperiod, self.slowperiod, self.signalperiod)

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # MACDEXT needs more warmup due to multiple MA types
        return self.window_size() * 3
