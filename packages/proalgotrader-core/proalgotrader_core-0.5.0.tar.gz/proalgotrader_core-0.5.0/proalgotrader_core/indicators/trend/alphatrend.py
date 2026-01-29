import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class AlphaTrend(Indicator):
    """
    Alpha Trend.

    A trend-following indicator that filters out noise.

    Parameters
    - period (int, default: 14): ATR period
    - multiplier (float, default: 1.0): ATR multiplier
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - close_column (str, default: "close"): close price column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `alphatrend_{period}`.

    Output/Response
    - `data` contains `current_candle` plus 1 AlphaTrend column.
    - Output column names: `[<alphatrend>]`. Default: `alphatrend_{period}`.
    """

    def __init__(
        self,
        period: int = 14,
        multiplier: float = 1.0,
        high_column: str = "high",
        low_column: str = "low",
        close_column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.multiplier = multiplier
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.output_column = f"alphatrend_{period}"
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
        atr_val = tr.ewm_mean(alpha=1.0 / self.period)

        # Upper and lower bands
        upper_band = close + (atr_val * self.multiplier)
        lower_band = close - (atr_val * self.multiplier)

        # Alpha trend line
        is_up = close > close.shift(1)
        alpha_trend = pl.when(is_up).then(upper_band).otherwise(lower_band)

        return alpha_trend

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
                    "AlphaTrend expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "AlphaTrend requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period * 3
