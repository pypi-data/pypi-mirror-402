import polars as pl
from proalgotrader_core.indicators.indicators import Indicators

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class MINUS_DM(Indicator):
    """
    Minus Directional Movement (MINUS_DM).

    The Minus Directional Movement measures the strength of downward price movement.
    It is part of the directional movement system that includes ADX, ADXR, DX, MINUS_DI, and PLUS_DM.

    The MINUS_DM indicates the presence of a downward trend and works in conjunction
    with PLUS_DM to determine trend direction and strength.

    Parameters
    - timeperiod (int, default: 14)
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `minus_dm_{timeperiod}` (e.g. `minus_dm_14`).

    Output/Response
    - `data` contains `current_candle` plus 1 MINUS_DM column.
    - Output column names: `[<minus_dm>]`. Default: `minus_dm_{timeperiod}`.
    """

    def __init__(
        self,
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.minus_dm_col = f"minus_dm_{timeperiod}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        return Indicators.build_minus_dm(
            high=pl.col("high"),
            low=pl.col("low"),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.minus_dm_col)]

    def output_columns(self) -> List[str]:
        return [self.minus_dm_col]

    def required_columns(self) -> List[str]:
        return ["high", "low"]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "MINUS_DM expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "MINUS_DM requires a non-empty single output column name"
                )
            self.minus_dm_col = requested

    def window_size(self) -> int:
        return self.timeperiod

    def warmup_size(self) -> int:
        return self.timeperiod * 3
