import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class AccBands(Indicator):
    """
    Acceleration Bands.

    Bands that expand during acceleration and contract during deceleration.

    Returns struct with (upper, middle, lower).

    Parameters
    - period (int, default: 20): lookback window length
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - close_column (str, default: "close"): close price column
    - output_columns (list[str] | None): optional; must contain exactly 3 names.

    Output/Response
    - `data` contains `current_candle` plus 3 AccBands columns.
    - Output column names: `[<upper>, <middle>, <lower>]`.
    """

    def __init__(
        self,
        period: int = 20,
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
        self.output_columns_list = output_columns or [
            "accbands_upper",
            "accbands_middle",
            "accbands_lower",
        ]

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)
        close = pl.col(self.close_column)

        # Middle band is SMA
        middle = close.rolling_mean(window_size=self.period)

        # Calculate acceleration factors
        high_factor = (high / close).rolling_mean(window_size=self.period)
        low_factor = (low / close).rolling_mean(window_size=self.period)

        # Upper and lower bands
        upper = middle * high_factor
        lower = middle * low_factor

        return pl.struct(
            upper=upper,
            middle=middle,
            lower=lower,
        )

    def _exprs(self) -> List[pl.Expr]:
        struct_expr = self.build()
        return [
            struct_expr.struct.field("upper").alias(self.output_columns_list[0]),
            struct_expr.struct.field("middle").alias(self.output_columns_list[1]),
            struct_expr.struct.field("lower").alias(self.output_columns_list[2]),
        ]

    def output_columns(self) -> List[str]:
        return self.output_columns_list

    def required_columns(self) -> List[str]:
        return [self.high_column, self.low_column, self.close_column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 3:
                raise ValueError("AccBands expects exactly 3 output column names")
            if not all(
                isinstance(name, str) and name
                for name in self._requested_output_columns
            ):
                raise ValueError("All output column names must be non-empty strings")
            self.output_columns_list = self._requested_output_columns

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period * 3
