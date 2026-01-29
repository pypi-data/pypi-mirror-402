import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class VHF(Indicator):
    """
    Vertical Horizontal Filter.

    Measures whether a trend is present (VHF close to 1) or ranging (VHF close to 0).

    Parameters
    - period (int, default: 28): lookback window length
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `vhf_{period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 VHF column.
    - Output column names: `[<vhf>]`. Default: `vhf_{period}_{column}`.
    """

    def __init__(
        self,
        period: int = 28,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.column = column
        self.output_column = f"vhf_{period}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        source = pl.col(self.column)

        # Calculate change
        change = source.diff().abs()

        # Numerator: difference between highest and lowest close
        numerator = source.rolling_max(self.period) - source.rolling_min(self.period)

        # Denominator: sum of all changes
        denominator = change.rolling_sum(self.period)

        return numerator / denominator

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
                    "VHF expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("VHF requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period
