import polars as pl

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class RSI(Indicator):
    """
    Relative Strength Index (RSI).

    Parameters
    - timeperiod (int, default: 14)
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `rsi_{timeperiod}_{column}` (e.g. `rsi_14_close`).

    Output/Response
    - `data` contains `current_candle` plus 1 RSI column.
    - Output column names: `[<rsi>]`. Default: `rsi_{timeperiod}_{column}`.
    """

    def __init__(
        self,
        timeperiod: int = 14,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.column = column
        self.rsi_col = f"rsi_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        delta = pl.col(self.column).diff()
        gains = pl.when(delta > 0).then(delta).otherwise(0)
        losses = pl.when(delta < 0).then(-delta).otherwise(0)
        avg_gain = gains.ewm_mean(adjust=False, alpha=1.0 / self.timeperiod)
        avg_loss = losses.ewm_mean(adjust=False, alpha=1.0 / self.timeperiod)
        rs = avg_gain / pl.when(avg_loss == 0).then(1).otherwise(avg_loss)
        return 100 - (100 / (1 + rs))

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.rsi_col)]

    def output_columns(self) -> List[str]:
        return [self.rsi_col]

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "RSI expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("RSI requires a non-empty single output column name")
            self.rsi_col = requested

    def window_size(self) -> int:
        return self.timeperiod

    def warmup_size(self) -> int:
        return self.timeperiod * 3
