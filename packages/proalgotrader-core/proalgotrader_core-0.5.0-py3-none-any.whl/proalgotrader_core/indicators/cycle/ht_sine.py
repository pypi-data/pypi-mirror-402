"""
HT_SINE - Hilbert Transform - SineWave

Category: Cycle Indicators
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class HT_SINE(Indicator):
    """
    HT_SINE - Hilbert Transform - SineWave

    Category: Cycle Indicators

    The Hilbert Transform - SineWave (HT_SINE) is a cycle indicator
    that uses the Hilbert Transform to generate sine wave components
    from price data. This indicator provides two outputs: sine and leadsine,
    which represent different phases of the cycle analysis.

    The sine wave components are fundamental to cycle analysis and provide
    insights into the cyclical nature of price movements. This indicator
    is particularly useful for:
    - Cycle phase analysis
    - Market cycle identification
    - Sine wave cycle detection
    - Cycle-based trading strategies
    - Advanced cycle analysis

    The sine wave representation allows for:
    - Cycle phase identification
    - Cycle period determination
    - Phase relationship analysis
    - Cycle synchronization
    - Advanced cycle filtering

    Parameters:
        real: Input price data (default: "close")
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with sine and leadsine columns
    """

    def __init__(
        self,
        real: str = "close",
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.real = real

        base = prefix or f"ht_sine_{real}"
        self.sine_col = f"{base}_sine"
        self.leadsine_col = f"{base}_leadsine"

        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build HT_SINE expression."""
        return Indicators.build_ht_sine(source=pl.col(self.real))

    def _exprs(self) -> List[pl.Expr]:
        """Return HT_SINE expressions."""
        ht_sine_result = self.build()
        return [
            ht_sine_result.struct.field("sine").alias(self.sine_col),
            ht_sine_result.struct.field("leadsine").alias(self.leadsine_col),
        ]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.sine_col, self.leadsine_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.real]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 2:
                raise ValueError(
                    "HT_SINE expects exactly 2 output column names in 'output_columns'"
                )
            sine_col, leadsine_col = self._requested_output_columns
            cols = [sine_col, leadsine_col]
            if any(not isinstance(c, str) or not c for c in cols):
                raise ValueError("HT_SINE requires two non-empty output column names")
            self.sine_col, self.leadsine_col = cols

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # HT_SINE uses Hilbert Transform which typically needs around 50-100 periods
        return 50

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # Hilbert Transform needs significant warmup for stable output
        return 50
