import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class Fisher(Indicator):
    """
    Fisher Transform.

    Transforms price to make it nearly Gaussian, identifying turning points.

    Parameters
    - period (int, default: 9): lookback window length
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `fisher_{period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 Fisher column.
    - Output column names: `[<fisher>]`. Default: `fisher_{period}_{column}`.
    """

    def __init__(
        self,
        period: int = 9,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.column = column
        self.output_column = f"fisher_{period}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        source = pl.col(self.column)

        # Normalize to -1 to 1 range
        max_val = source.rolling_max(self.period)
        min_val = source.rolling_min(self.period)
        normalized = (source - min_val) / (max_val - min_val)

        # Apply Fisher transformation
        x = 2 * (normalized - 0.5)

        # Handle log(0) and log(negative) by filling with 0
        numerator = (1 + x).fill_null(0)
        denominator = (1 - x).fill_null(0)
        ratio = pl.when(denominator == 0).then(0).otherwise(numerator / denominator)

        y = 0.5 * ratio.log()

        # Smooth the result
        alpha = 2.0 / (self.period / 3 + 1)
        return y.fill_nan(0).fill_null(0).ewm_mean(alpha=alpha)

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
                    "Fisher expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "Fisher requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period * 3
