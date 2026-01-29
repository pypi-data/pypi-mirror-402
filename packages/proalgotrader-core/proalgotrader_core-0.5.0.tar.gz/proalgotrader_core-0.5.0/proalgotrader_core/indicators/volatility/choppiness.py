import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class Choppiness(Indicator):
    """
    Choppiness Index.

    Measures whether the market is trending or choppy (ranging).
    Values above 61.8 indicate choppy, below 38.2 indicate trending.

    Parameters
    - period (int, default: 14): lookback window length
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - close_column (str, default: "close"): close price column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `choppiness_{period}`.

    Output/Response
    - `data` contains `current_candle` plus 1 Choppiness column.
    - Output column names: `[<choppiness>]`. Default: `choppiness_{period}`.
    """

    def __init__(
        self,
        period: int = 14,
        high_column: str = "high",
        low_column: str = "low",
        close_column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.output_column = f"choppiness_{period}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)
        close = pl.col(self.close_column)

        # Calculate ATR
        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()
        tr = pl.max_horizontal(hl, hc, lc)
        atr_val = tr.ewm_mean(alpha=1.0)

        # Sum of ATRs
        atr_sum = atr_val.rolling_sum(self.period)

        # Highest high and lowest low
        highest_high = high.rolling_max(self.period)
        lowest_low = low.rolling_min(self.period)

        # Choppiness formula
        numerator = 100 * pl.log10(atr_sum / (highest_high - lowest_low))
        denominator = pl.log10(self.period)

        return numerator / denominator

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.output_column)]

    def output_columns(self) -> List[str]:
        return [self.output_column]

    def required_columns(self) -> List[str]:
        return [self.high_column, self.low_column, self.close_column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "Choppiness expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "Choppiness requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period * 3
