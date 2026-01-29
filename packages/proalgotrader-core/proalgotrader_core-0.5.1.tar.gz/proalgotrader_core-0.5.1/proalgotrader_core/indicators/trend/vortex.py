import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class Vortex(Indicator):
    """
    Vortex Indicator.

    Identifies trend start and changes.

    Returns struct with (vi_plus, vi_minus).

    Parameters
    - period (int, default: 14): lookback window length
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - close_column (str, default: "close"): close price column
    - output_columns (list[str] | None): optional; must contain exactly 2 names.

    Output/Response
    - `data` contains `current_candle` plus 2 Vortex columns.
    - Output column names: `[<vi_plus>, <vi_minus>]`.
    """

    def __init__(
        self,
        period: int = 14,
        high_column: str = "high",
        low_column: str = "low",
        close_column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.output_columns_list = output_columns or ["vi_plus", "vi_minus"]

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)
        close = pl.col(self.close_column)

        # True Range
        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()
        tr = pl.max_horizontal(hl, hc, lc)

        # Vortex movements
        vm_plus = (high - low.shift(1)).abs()
        vm_minus = (low - high.shift(1)).abs()

        # Sum over period
        tr_sum = tr.rolling_sum(self.period)
        vm_plus_sum = vm_plus.rolling_sum(self.period)
        vm_minus_sum = vm_minus.rolling_sum(self.period)

        # Vortex Indicator
        vi_plus = vm_plus_sum / tr_sum
        vi_minus = vm_minus_sum / tr_sum

        return pl.struct(
            vi_plus=vi_plus,
            vi_minus=vi_minus,
        )

    def _exprs(self) -> List[pl.Expr]:
        struct_expr = self.build()
        return [
            struct_expr.struct.field("vi_plus").alias(self.output_columns_list[0]),
            struct_expr.struct.field("vi_minus").alias(self.output_columns_list[1]),
        ]

    def output_columns(self) -> List[str]:
        return self.output_columns_list

    def required_columns(self) -> List[str]:
        return [self.high_column, self.low_column, self.close_column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 2:
                raise ValueError("Vortex expects exactly 2 output column names")
            if not all(
                isinstance(name, str) and name
                for name in self._requested_output_columns
            ):
                raise ValueError("All output column names must be non-empty strings")
            self.output_columns_list = self._requested_output_columns

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period
