import polars as pl

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class TRANGE(Indicator):
    """
    True Range (TRANGE).

    True Range is the greatest of the following:
    - Current high minus current low
    - Absolute value of current high minus previous close
    - Absolute value of current low minus previous close

    True Range is the foundation for other volatility indicators like ATR (Average True Range).

    Parameters
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `trange`.

    Output/Response
    - `data` contains `current_candle` plus 1 TRANGE column.
    - Output column names: `[<trange>]`. Default: `trange`.
    """

    def __init__(
        self,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.trange_col = "trange"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        high = pl.col("high")
        low = pl.col("low")
        close = pl.col("close")

        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()

        return pl.max_horizontal(hl, hc, lc)

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.trange_col)]

    def output_columns(self) -> List[str]:
        return [self.trange_col]

    def required_columns(self) -> List[str]:
        return ["high", "low", "close"]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "TRANGE expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "TRANGE requires a non-empty single output column name"
                )
            self.trange_col = requested

    def window_size(self) -> int:
        return 1  # TRANGE only needs current candle data

    def warmup_size(self) -> int:
        return 1  # Minimal warmup since it uses previous close
