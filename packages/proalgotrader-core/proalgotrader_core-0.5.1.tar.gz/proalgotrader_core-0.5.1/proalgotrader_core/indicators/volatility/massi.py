import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class MassI(Indicator):
    """
    Mass Index.

    Identifies potential reversals when the range expands excessively.

    Parameters
    - period (int, default: 9): EMA period for range calculation
    - sum_period (int, default: 25): summation period
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `massi_{period}_{sum_period}`.

    Output/Response
    - `data` contains `current_candle` plus 1 MassI column.
    - Output column names: `[<massi>]`. Default: `massi_{period}_{sum_period}`.
    """

    def __init__(
        self,
        period: int = 9,
        sum_period: int = 25,
        high_column: str = "high",
        low_column: str = "low",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.sum_period = sum_period
        self.high_column = high_column
        self.low_column = low_column
        self.output_column = f"massi_{period}_{sum_period}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)

        # Calculate range
        range_val = high - low

        # Calculate EMA of range
        alpha = 2.0 / (self.period + 1)
        ema1 = range_val.ewm_mean(alpha=alpha)
        ema2 = ema1.ewm_mean(alpha=alpha)

        # Mass index ratio
        ratio = ema1 / ema2

        # Sum over the period
        return ratio.rolling_sum(self.sum_period)

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.output_column)]

    def output_columns(self) -> List[str]:
        return [self.output_column]

    def required_columns(self) -> List[str]:
        return [self.high_column, self.low_column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "MassI expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("MassI requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.period + self.sum_period

    def warmup_size(self) -> int:
        return self.window_size() * 3
