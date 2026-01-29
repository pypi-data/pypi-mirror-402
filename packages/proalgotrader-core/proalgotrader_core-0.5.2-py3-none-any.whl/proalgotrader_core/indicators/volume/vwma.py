import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class VWMA(Indicator):
    """
    Volume Weighted Moving Average.

    A moving average weighted by volume.

    Parameters
    - period (int, default: 20): lookback window length
    - column (str, default: "close"): input column name
    - volume_column (str, default: "volume"): volume column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `vwma_{period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 VWMA column.
    - Output column names: `[<vwma>]`. Default: `vwma_{period}_{column}`.
    """

    def __init__(
        self,
        period: int = 20,
        column: str = "close",
        volume_column: str = "volume",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.column = column
        self.volume_column = volume_column
        self.output_column = f"vwma_{period}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        source = pl.col(self.column)
        volume = pl.col(self.volume_column)

        # Price * Volume
        pv = source * volume

        # Rolling sums
        pv_sum = pv.rolling_sum(self.period)
        volume_sum = volume.rolling_sum(self.period)

        return pv_sum / volume_sum

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
                    "VWMA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("VWMA requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period
