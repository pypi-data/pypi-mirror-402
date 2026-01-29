import polars as pl
from proalgotrader_core.indicators.indicators import Indicators

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class DEMA(Indicator):
    """
    Double Exponential Moving Average (DEMA).

    The DEMA reduces lag compared to traditional EMA by applying the EMA calculation twice.
    It provides faster responsiveness while maintaining smoothness.

    Parameters
    - timeperiod (int, default: 30): lookback window length
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `dema_{timeperiod}_{column}` (e.g. `dema_30_close`).

    Output/Response
    - `data` contains `current_candle` plus 1 DEMA column.
    - Output column names: `[<dema_column>]`. Default: `dema_{timeperiod}_{column}`.
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
        self.dema_col = f"dema_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        return Indicators.build_dema(
            source=pl.col(self.column), timeperiod=self.timeperiod
        )

    def expr(self) -> pl.Expr:
        return self.build().alias(self.dema_col)

    def _exprs(self) -> List[pl.Expr]:
        return [self.expr()]

    def output_columns(self) -> List[str]:
        return [self.dema_col]

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "DEMA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("DEMA requires a non-empty single output column name")
            self.dema_col = requested

    def window_size(self) -> int:
        return self.timeperiod

    def warmup_size(self) -> int:
        # use extra history to stabilize DEMA
        return self.timeperiod * 3
