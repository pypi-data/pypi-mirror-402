import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class ZLMA(Indicator):
    """
    Zero Lag Moving Average.

    Reduces lag in the moving average by using error correction.

    Parameters
    - period (int, default: 30): lookback window length
    - column (str, default: "close"): input column name
    - offset (int, default: 1): lookback offset for error correction
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `zlma_{period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 ZLMA column.
    - Output column names: `[<zlma>]`. Default: `zlma_{period}_{column}`.
    """

    def __init__(
        self,
        period: int = 30,
        column: str = "close",
        offset: int = 1,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.column = column
        self.offset = offset
        self.output_column = f"zlma_{period}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        # ZLMA = EMA + (EMA - EMA.shift(offset))
        alpha = 2.0 / (self.period + 1)
        ema_val = pl.col(self.column).ewm_mean(alpha=alpha)
        lag = ema_val.shift(self.offset)
        return ema_val + (ema_val - lag)

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
                    "ZLMA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("ZLMA requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.period + self.offset

    def warmup_size(self) -> int:
        return self.period * 3
