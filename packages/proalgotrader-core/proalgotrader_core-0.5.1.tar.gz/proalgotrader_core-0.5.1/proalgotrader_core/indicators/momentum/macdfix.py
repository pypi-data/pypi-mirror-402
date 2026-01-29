"""
MACDFIX - Moving Average Convergence/Divergence Fix 12/26

Category: Momentum Indicators
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class MACDFIX(Indicator):
    """
    MACDFIX - Moving Average Convergence/Divergence Fix 12/26

    Category: Momentum Indicators

    The MACD Fix 12/26 (MACDFIX) is a simplified version of the MACD indicator
    that uses fixed periods for the fast and slow moving averages (12 and 26
    respectively) and only allows customization of the signal period. This
    provides a standardized MACD calculation that is commonly used in trading
    systems.

    The indicator calculates:
    - Fast MA: 12-period exponential moving average
    - Slow MA: 26-period exponential moving average
    - MACD Line: Fast MA - Slow MA
    - Signal Line: Signal period exponential moving average of MACD Line
    - Histogram: MACD Line - Signal Line

    Parameters:
        real: Input price data (default: "close")
        signalperiod: Signal line period (default: 9)
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with MACD, MACD signal, and MACD histogram columns
    """

    def __init__(
        self,
        real: str = "close",
        signalperiod: int = 9,
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.real = real
        self.signalperiod = signalperiod

        base = prefix or f"macdfix_{signalperiod}_{real}"
        self.macd_col = f"{base}"
        self.signal_col = f"{base}_signal"
        self.hist_col = f"{base}_hist"

        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build MACDFIX expression."""
        return Indicators.build_macdfix(
            source=pl.col(self.real),
            signalperiod=self.signalperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        """Return MACDFIX expressions."""
        macdfix_result = self.build()
        return [
            macdfix_result.struct.field("macd").alias(self.macd_col),
            macdfix_result.struct.field("macdsignal").alias(self.signal_col),
            macdfix_result.struct.field("macdhist").alias(self.hist_col),
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
                    "MACDFIX expects exactly 3 output column names in 'output_columns'"
                )
            macd_col, signal_col, hist_col = self._requested_output_columns
            cols = [macd_col, signal_col, hist_col]
            if any(not isinstance(c, str) or not c for c in cols):
                raise ValueError("MACDFIX requires three non-empty output column names")
            self.macd_col, self.signal_col, self.hist_col = cols

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # MACDFIX uses fixed 12/26 periods, so we need the maximum
        return 26

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # MACDFIX needs warmup for stable MACD calculation
        return 26 * 2
