import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class PVI(Indicator):
    """
    Positive Volume Index.

    Tracks price movement on days when volume increases.

    Parameters
    - column (str, default: "close"): close price column
    - volume_column (str, default: "volume"): volume column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `pvi_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 PVI column.
    - Output column names: `[<pvi>]`. Default: `pvi_{column}`.
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
        self.output_column = f"pvi_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        close = pl.col(self.column)
        volume = pl.col(self.volume_column)

        # Calculate ROC
        roc_val = 100 * (close - close.shift(1)) / close.shift(1)

        # PVI changes only when volume increases
        pvi_change = (
            pl.when(volume > volume.shift(1)).then(roc_val / 100 + 1).otherwise(1)
        )

        # Calculate PVI cumulatively
        return pvi_change.cum_product()

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
                    "PVI expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("PVI requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return 0

    def warmup_size(self) -> int:
        return 0
