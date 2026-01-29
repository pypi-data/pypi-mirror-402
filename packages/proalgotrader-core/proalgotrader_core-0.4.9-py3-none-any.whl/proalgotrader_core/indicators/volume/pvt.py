import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class PVT(Indicator):
    """
    Price Volume Trend.

    Cumulative volume-based indicator.

    Parameters
    - column (str, default: "close"): close price column
    - volume_column (str, default: "volume"): volume column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `pvt_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 PVT column.
    - Output column names: `[<pvt>]`. Default: `pvt_{column}`.
    """

    def __init__(
        self,
        column: str = "close",
        volume_column: str = "volume",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.column = column
        self.volume_column = volume_column
        self.output_column = f"pvt_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        close = pl.col(self.column)
        volume = pl.col(self.volume_column)

        # Price change percentage
        price_change = (close - close.shift(1)) / close.shift(1)

        # PVT contribution
        pvt_contribution = price_change * volume

        # Cumulative sum
        return pvt_contribution.cum_sum()

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.output_column)]

    def output_columns(self) -> List[str]:
        return [self.output_column]

    def required_columns(self) -> List[str]:
        return [self.column, self.volume_column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "PVT expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("PVT requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return 0

    def warmup_size(self) -> int:
        return 0
