import polars as pl

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class WMA(Indicator):
    """
    Weighted Moving Average (WMA).

    The WMA gives more weight to recent prices, with weights increasing linearly
    from the oldest to the newest price. This makes it more responsive to recent
    price changes compared to SMA but less aggressive than EMA.

    Parameters
    - timeperiod (int, default: 30): lookback window length
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `wma_{timeperiod}_{column}` (e.g. `wma_30_close`).

    Output/Response
    - `data` contains `current_candle` plus 1 WMA column.
    - Output column names: `[<wma_column>]`. Default: `wma_{timeperiod}_{column}`.
    """

    def __init__(
        self,
        timeperiod: int = 30,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.column = column
        self.wma_col = f"wma_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        # WMA implementation using linear weights
        # Sum of weights = timeperiod * (timeperiod + 1) / 2
        sum_weights = self.timeperiod * (self.timeperiod + 1) / 2

        # Calculate weighted sum over the rolling window
        source = pl.col(self.column)
        weighted_sum = pl.sum_horizontal(
            [source.shift(i) * (self.timeperiod - i) for i in range(self.timeperiod)]
        )

        return weighted_sum / sum_weights

    def expr(self) -> pl.Expr:
        return self.build().alias(self.wma_col)

    def _exprs(self) -> List[pl.Expr]:
        return [self.expr()]

    def output_columns(self) -> List[str]:
        return [self.wma_col]

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "WMA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("WMA requires a non-empty single output column name")
            self.wma_col = requested

    def window_size(self) -> int:
        return self.timeperiod

    def warmup_size(self) -> int:
        # use extra history to stabilize WMA
        return self.timeperiod * 3
