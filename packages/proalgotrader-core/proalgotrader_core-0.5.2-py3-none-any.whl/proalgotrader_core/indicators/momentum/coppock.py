import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class Coppock(Indicator):
    """
    Coppock Curve.

    A momentum indicator designed for long-term market timing.

    Parameters
    - roc1 (int, default: 14): first ROC period
    - roc2 (int, default: 11): second ROC period
    - wma_period (int, default: 10): WMA smoothing period
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `coppock_{roc1}_{roc2}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 Coppock column.
    - Output column names: `[<coppock>]`. Default: `coppock_{roc1}_{roc2}_{column}`.
    """

    def __init__(
        self,
        roc1: int = 14,
        roc2: int = 11,
        wma_period: int = 10,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.roc1 = roc1
        self.roc2 = roc2
        self.wma_period = wma_period
        self.column = column
        self.output_column = f"coppock_{roc1}_{roc2}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        source = pl.col(self.column)

        # Calculate ROCs
        r1 = 100 * (source - source.shift(self.roc1)) / source.shift(self.roc1)
        r2 = 100 * (source - source.shift(self.roc2)) / source.shift(self.roc2)

        # Sum and smooth with WMA (using SMA as approximation)
        coppock_raw = r1 + r2
        return coppock_raw.rolling_mean(window_size=self.wma_period)

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
                    "Coppock expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "Coppock requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        return max(self.roc1, self.roc2)

    def warmup_size(self) -> int:
        return self.window_size() * 3
