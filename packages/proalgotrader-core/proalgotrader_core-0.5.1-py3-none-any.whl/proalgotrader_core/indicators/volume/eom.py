import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class EOM(Indicator):
    """
    Ease of Movement.

    Shows how easily price moves based on volume.

    Parameters
    - period (int, default: 14): lookback window length
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - volume_column (str, default: "volume"): volume column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `eom_{period}`.

    Output/Response
    - `data` contains `current_candle` plus 1 EOM column.
    - Output column names: `[<eom>]`. Default: `eom_{period}`.
    """

    def __init__(
        self,
        period: int = 14,
        high_column: str = "high",
        low_column: str = "low",
        volume_column: str = "volume",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.high_column = high_column
        self.low_column = low_column
        self.volume_column = volume_column
        self.output_column = f"eom_{period}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)
        volume = pl.col(self.volume_column)

        # Midpoint move
        midpoint_move = (high + low) / 2 - ((high.shift(1) + low.shift(1)) / 2)

        # Box ratio
        box_ratio = (high - low) / volume

        # Ease of Movement (scaled by 1 billion)
        eom_raw = midpoint_move / box_ratio

        # Smooth with SMA
        return eom_raw.rolling_mean(window_size=self.period)

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.output_column)]

    def output_columns(self) -> List[str]:
        return [self.output_column]

    def required_columns(self) -> List[str]:
        return [self.high_column, self.low_column, self.volume_column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "EOM expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("EOM requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period
