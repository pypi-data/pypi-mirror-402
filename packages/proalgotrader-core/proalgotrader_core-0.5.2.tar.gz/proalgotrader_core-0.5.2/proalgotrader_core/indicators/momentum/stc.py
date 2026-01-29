import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class STC(Indicator):
    """
    Schaff Trend Cycle.

    Combines MACD with stochastic to identify trends earlier.

    Parameters
    - fast_period (int, default: 23): fast EMA period
    - slow_period (int, default: 50): slow EMA period
    - k_period (int, default: 10): stochastic %K period
    - d_period (int, default: 3): stochastic %D period
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `stc_{fast_period}_{slow_period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 STC column.
    - Output column names: `[<stc>]`. Default: `stc_{fast_period}_{slow_period}_{column}`.
    """

    def __init__(
        self,
        fast_period: int = 23,
        slow_period: int = 50,
        k_period: int = 10,
        d_period: int = 3,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.k_period = k_period
        self.d_period = d_period
        self.column = column
        self.output_column = f"stc_{fast_period}_{slow_period}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        source = pl.col(self.column)

        # Calculate MACD
        alpha_fast = 2.0 / (self.fast_period + 1)
        alpha_slow = 2.0 / (self.slow_period + 1)
        macd_line = source.ewm_mean(alpha=alpha_fast) - source.ewm_mean(
            alpha=alpha_slow
        )

        # Calculate Stochastic of MACD
        lowest_macd = macd_line.rolling_min(self.k_period)
        highest_macd = macd_line.rolling_max(self.k_period)

        stoch_k = 100 * (macd_line - lowest_macd) / (highest_macd - lowest_macd)

        # Smooth with %D
        return stoch_k.rolling_mean(self.d_period)

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
                    "STC expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("STC requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return max(self.fast_period, self.slow_period)

    def warmup_size(self) -> int:
        return self.window_size() * 3
