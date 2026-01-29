import polars as pl

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class DX(Indicator):
    """
    Directional Movement Index (DX).

    The DX indicator measures the difference between upward and downward price movement,
    expressed as a percentage. It is the raw calculation that forms the basis for the ADX indicator.

    Parameters
    - timeperiod (int, default: 14)
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `dx_{timeperiod}` (e.g. `dx_14`).

    Output/Response
    - `data` contains `current_candle` plus 1 DX column.
    - Output column names: `[<dx>]`. Default: `dx_{timeperiod}`.
    """

    def __init__(
        self,
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.dx_col = f"dx_{timeperiod}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        # Calculate True Range
        high = pl.col("high")
        low = pl.col("low")
        close = pl.col("close")

        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()
        tr = pl.max_horizontal(hl, hc, lc)

        # Calculate +DM and -DM
        up_move = high.diff()
        down_move = -low.diff()

        plus_dm = (
            pl.when((up_move > down_move) & (up_move > 0)).then(up_move).otherwise(0)
        )
        minus_dm = (
            pl.when((down_move > up_move) & (down_move > 0))
            .then(down_move)
            .otherwise(0)
        )

        # Smooth with EMA
        alpha = 2.0 / (self.timeperiod + 1)
        atr_val = (
            pl.when(tr.is_null())
            .then(0)
            .otherwise(tr)
            .ewm_mean(alpha=alpha, adjust=False)
        )
        plus_di = 100 * plus_dm.ewm_mean(alpha=alpha, adjust=False) / atr_val
        minus_di = 100 * minus_dm.ewm_mean(alpha=alpha, adjust=False) / atr_val

        # Calculate DX
        return 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.dx_col)]

    def output_columns(self) -> List[str]:
        return [self.dx_col]

    def required_columns(self) -> List[str]:
        return ["high", "low", "close"]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "DX expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("DX requires a non-empty single output column name")
            self.dx_col = requested

    def window_size(self) -> int:
        return self.timeperiod

    def warmup_size(self) -> int:
        return self.timeperiod * 3
