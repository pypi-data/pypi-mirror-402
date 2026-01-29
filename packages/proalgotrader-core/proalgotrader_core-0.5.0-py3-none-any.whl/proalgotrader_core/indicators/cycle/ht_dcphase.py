import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class HT_DCPHASE(Indicator):
    """
    HT_DCPHASE - Hilbert Transform - Dominant Cycle Phase

    The Hilbert Transform - Dominant Cycle Phase (HT_DCPHASE) is a cycle indicator
    that uses the Hilbert Transform to identify the phase of the dominant cycle in price data.
    This indicator is part of the Hilbert Transform family of indicators that provide
    insights into market cycles and their phase characteristics.

    HT_DCPHASE analyzes the price data using advanced mathematical transformations
    to identify the current phase of the most significant cycle. This approach makes HT_DCPHASE
    particularly useful for:
    - Cycle phase identification
    - Market cycle analysis
    - Phase-based trading strategies
    - Cycle timing analysis
    - Market regime identification

    Key characteristics:
    - Real-valued output (cycle phase in degrees or radians)
    - No timeperiod parameter required
    - Advanced mathematical transformation
    - Excellent for cycle phase analysis
    - Useful for timing identification
    - Works well across all timeframes

    The calculation formula:
    HT_DCPHASE uses Hilbert Transform mathematical analysis to determine
    the current phase of the dominant cycle in the price data. The output represents
    the phase angle of the most significant cycle.

    Interpretation:
    - Phase values: Typically range from 0 to 360 degrees (or 0 to 2π radians)
    - 0° (0 rad): Cycle peak
    - 90° (π/2 rad): Cycle rising
    - 180° (π rad): Cycle trough
    - 270° (3π/2 rad): Cycle falling
    - Phase transitions: Indicate cycle phase changes
    - Stable phases: Consistent cycle phases
    - Changing phases: Cycle phase transitions

    Typical HT_DCPHASE values:
    - Peak phase: 0° (0 rad)
    - Rising phase: 0° to 180° (0 to π rad)
    - Trough phase: 180° (π rad)
    - Falling phase: 180° to 360° (π to 2π rad)
    - Phase transitions: Changes between phase ranges

    Common applications:
    - Cycle phase identification
    - Market cycle analysis
    - Phase-based strategy timing
    - Cycle detection and analysis
    - Market regime identification

    Parameters:
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        ht_dcphase = HT_DCPHASE()
        ht_dcphase_high = HT_DCPHASE(column='high', output_columns=['ht_dcphase_high'])
    """

    def __init__(
        self,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.column = column
        self.ht_dcphase_col = f"ht_dcphase_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the HT_DCPHASE expression using polars_talib."""
        return Indicators.build_ht_dcphase(source=pl.col(self.column))

    def expr(self) -> pl.Expr:
        """Return the HT_DCPHASE expression with proper column alias."""
        return self.build().alias(self.ht_dcphase_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.ht_dcphase_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "HT_DCPHASE expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "HT_DCPHASE requires a non-empty single output column name"
                )

            self.ht_dcphase_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for HT_DCPHASE calculation."""
        # HT_DCPHASE uses Hilbert Transform which typically needs a reasonable amount of data
        return 50

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable HT_DCPHASE calculation."""
        # Hilbert Transform needs more warmup data for stable calculations
        return 100
