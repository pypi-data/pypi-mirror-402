"""
HT_PHASOR - Hilbert Transform - Phasor Components

Category: Cycle Indicators
"""

import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class HT_PHASOR(Indicator):
    """
    HT_PHASOR - Hilbert Transform - Phasor Components

    Category: Cycle Indicators

    The Hilbert Transform - Phasor Components (HT_PHASOR) is a cycle indicator
    that uses the Hilbert Transform to decompose price data into its phasor
    components: inphase and quadrature. These components represent the real
    and imaginary parts of the complex phasor representation of the price signal.

    The phasor components are fundamental to cycle analysis and provide insights
    into the phase relationships and cycle characteristics of price movements.
    This indicator is particularly useful for:
    - Cycle phase analysis
    - Market cycle identification
    - Phase relationship studies
    - Cycle-based trading strategies
    - Advanced cycle analysis

    The phasor representation allows for:
    - Phase angle calculations
    - Cycle period determination
    - Phase relationship analysis
    - Cycle synchronization
    - Advanced cycle filtering

    Parameters:
        real: Input price data (default: "close")
        output_columns: Optional custom output column names
        prefix: Optional base for default names

    Returns:
        DataFrame with inphase and quadrature columns
    """

    def __init__(
        self,
        real: str = "close",
        output_columns: Optional[List[str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.real = real

        base = prefix or f"ht_phasor_{real}"
        self.inphase_col = f"{base}_inphase"
        self.quadrature_col = f"{base}_quadrature"

        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build HT_PHASOR expression."""
        return Indicators.build_ht_phasor(source=pl.col(self.real))

    def _exprs(self) -> List[pl.Expr]:
        """Return HT_PHASOR expressions."""
        ht_phasor_result = self.build()
        return [
            ht_phasor_result.struct.field("inphase").alias(self.inphase_col),
            ht_phasor_result.struct.field("quadrature").alias(self.quadrature_col),
        ]

    def output_columns(self) -> List[str]:
        """Return output column names."""
        return [self.inphase_col, self.quadrature_col]

    def required_columns(self) -> List[str]:
        """Return required input columns."""
        return [self.real]

    def validate_output_columns(self) -> None:
        """Validate output columns."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 2:
                raise ValueError(
                    "HT_PHASOR expects exactly 2 output column names in 'output_columns'"
                )
            inphase_col, quadrature_col = self._requested_output_columns
            cols = [inphase_col, quadrature_col]
            if any(not isinstance(c, str) or not c for c in cols):
                raise ValueError("HT_PHASOR requires two non-empty output column names")
            self.inphase_col, self.quadrature_col = cols

    def window_size(self) -> int:
        """Return the window size needed for the indicator."""
        # HT_PHASOR uses Hilbert Transform which typically needs around 50-100 periods
        return 50

    def warmup_size(self) -> int:
        """Return warmup period needed for stable output."""
        # Hilbert Transform needs significant warmup for stable output
        return 50
