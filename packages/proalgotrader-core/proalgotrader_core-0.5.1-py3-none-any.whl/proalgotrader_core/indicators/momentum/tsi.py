import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class TSI(Indicator):
    """
    True Strength Index.

    Shows both trend direction and overbought/oversold conditions.

    Parameters
    - fast_period (int, default: 13): first smoothing period
    - slow_period (int, default: 25): second smoothing period
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `tsi_{fast_period}_{slow_period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 TSI column.
    - Output column names: `[<tsi>]`. Default: `tsi_{fast_period}_{slow_period}_{column}`.
    """

    def __init__(
        self,
        fast_period: int = 13,
        slow_period: int = 25,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.column = column
        self.output_column = f"tsi_{fast_period}_{slow_period}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        # Calculate price change
        delta = pl.col(self.column).diff()

        # Double smooth momentum
        alpha_fast = 2.0 / (self.fast_period + 1)
        alpha_slow = 2.0 / (self.slow_period + 1)

        momentum_smoothed = (
            delta.abs().ewm_mean(alpha=alpha_fast).ewm_mean(alpha=alpha_slow)
        )
        abs_momentum_smoothed = delta.ewm_mean(alpha=alpha_fast).ewm_mean(
            alpha=alpha_slow
        )

        return 100 * abs_momentum_smoothed / momentum_smoothed

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.output_column)]

    def output_columns(self) -> List[str]:
        return [self.output_column]

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "TSI expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("TSI requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.slow_period

    def warmup_size(self) -> int:
        return self.slow_period * 3
