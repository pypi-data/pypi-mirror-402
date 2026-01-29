import polars as pl
from proalgotrader_core.indicators.indicators import Indicators

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class PLUS_DM(Indicator):
    """
    Plus Directional Movement (PLUS_DM).

    The Plus Directional Movement measures the strength of upward price movement.
    It is part of the directional movement system that includes ADX, ADXR, DX, MINUS_DM, and PLUS_DI.

    The PLUS_DM indicates the presence of an upward trend and works in conjunction
    with MINUS_DM to determine trend direction and strength.

    Parameters
    - timeperiod (int, default: 14)
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `plus_dm_{timeperiod}` (e.g. `plus_dm_14`).

    Output/Response
    - `data` contains `current_candle` plus 1 PLUS_DM column.
    - Output column names: `[<plus_dm>]`. Default: `plus_dm_{timeperiod}`.
    """

    def __init__(
        self,
        timeperiod: int = 14,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.plus_dm_col = f"plus_dm_{timeperiod}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        return Indicators.build_plus_dm(
            high=pl.col("high"),
            low=pl.col("low"),
            timeperiod=self.timeperiod,
        )

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.plus_dm_col)]

    def output_columns(self) -> List[str]:
        return [self.plus_dm_col]

    def required_columns(self) -> List[str]:
        return ["high", "low"]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "PLUS_DM expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "PLUS_DM requires a non-empty single output column name"
                )
            self.plus_dm_col = requested

    def window_size(self) -> int:
        return self.timeperiod

    def warmup_size(self) -> int:
        return self.timeperiod * 3
