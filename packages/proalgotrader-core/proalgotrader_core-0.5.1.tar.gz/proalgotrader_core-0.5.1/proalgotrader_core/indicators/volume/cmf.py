import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class CMF(Indicator):
    """
    Chaikin Money Flow.

    Measures buying and selling pressure over a period.

    Parameters
    - period (int, default: 20): lookback window length
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - close_column (str, default: "close"): close price column
    - volume_column (str, default: "volume"): volume column
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `cmf_{period}`.

    Output/Response
    - `data` contains `current_candle` plus 1 CMF column.
    - Output column names: `[<cmf>]`. Default: `cmf_{period}`.
    """

    def __init__(
        self,
        period: int = 20,
        high_column: str = "high",
        low_column: str = "low",
        close_column: str = "close",
        volume_column: str = "volume",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.volume_column = volume_column
        self.output_column = f"cmf_{period}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)
        close = pl.col(self.close_column)
        volume = pl.col(self.volume_column)

        # Money Flow Multiplier
        mfm = ((close - low) - (high - close)) / (high - low)
        mfm = mfm.fill_null(0)

        # Money Flow Volume
        mfv = mfm * volume

        # Sum of positive and negative MFM
        mfv_positive = pl.when(mfv > 0).then(mfv).otherwise(0)
        mfv_negative = pl.when(mfv < 0).then(mfv.abs()).otherwise(0)

        # Chaikin Money Flow
        cmf_positive = mfv_positive.rolling_sum(self.period)
        cmf_negative = mfv_negative.rolling_sum(self.period)

        return (cmf_positive - cmf_negative) / (cmf_positive + cmf_negative)

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.output_column)]

    def output_columns(self) -> List[str]:
        return [self.output_column]

    def required_columns(self) -> List[str]:
        return [
            self.high_column,
            self.low_column,
            self.close_column,
            self.volume_column,
        ]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "CMF expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("CMF requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period
