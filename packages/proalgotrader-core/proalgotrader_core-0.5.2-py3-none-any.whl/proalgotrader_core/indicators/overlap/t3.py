import polars as pl
from proalgotrader_core.indicators.indicators import Indicators
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class T3(Indicator):
    """
    T3 - Triple Exponential Moving Average (T3)

    The T3 (Triple Exponential Moving Average) is an advanced smoothing indicator
    developed by Tim Tillson. It's designed to provide better smoothing than traditional
    moving averages while reducing lag through the use of a volume factor.

    T3 is essentially a triple smoothed exponential moving average with a volume factor
    that can be adjusted to control the trade-off between smoothness and responsiveness.
    The algorithm applies exponential smoothing six times using a volume factor to
    determine the smoothing constant.

    Key characteristics:
    - Superior lag reduction compared to traditional EMAs
    - Excellent smoothing properties with reduced noise
    - Volume factor allows fine-tuning of responsiveness vs smoothness
    - Better trend-following capabilities than simple moving averages
    - Reduces whipsaws while maintaining sensitivity to genuine trend changes

    The T3 calculation involves:
    1. Six applications of exponential smoothing
    2. Volume factor (vfactor) determines the smoothing constant
    3. Default volume factor of 0.7 provides good balance
    4. Higher vfactor = more responsive, lower vfactor = smoother

    Parameters:
    - timeperiod: The period for T3 calculation (default: 5)
    - vfactor: Volume factor for smoothing (default: 0.7, range: 0.0-1.0)
    - column: The input column name (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        t3 = T3(timeperiod=14, vfactor=0.7)
        t3_smooth = T3(timeperiod=20, vfactor=0.5, output_columns=["t3_smooth"])
        t3_responsive = T3(timeperiod=10, vfactor=0.9)
    """

    def __init__(
        self,
        timeperiod: int = 5,
        vfactor: float = 0.7,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.vfactor = vfactor
        self.column = column
        self.t3_col = f"t3_{timeperiod}_{vfactor}_{column}"
        self._requested_output_columns = output_columns

        # Validate vfactor range
        if not 0.0 <= vfactor <= 1.0:
            raise ValueError(f"vfactor must be between 0.0 and 1.0, got {vfactor}")

    def build(self) -> pl.Expr:
        """Build the T3 expression using polars_talib."""
        return Indicators.build_t3(
            source=pl.col(self.column), timeperiod=self.timeperiod, vfactor=self.vfactor
        )

    def expr(self) -> pl.Expr:
        """Return the T3 expression with proper column alias."""
        return self.build().alias(self.t3_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.t3_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "T3 expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("T3 requires a non-empty single output column name")

            self.t3_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for T3 calculation."""
        return self.timeperiod

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable T3 calculation."""
        # T3 needs significant warmup due to six-fold smoothing
        # Using 4x timeperiod for stable calculation
        return self.timeperiod * 4
