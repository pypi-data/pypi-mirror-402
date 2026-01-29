import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class KVO(Indicator):
    """
    Klinger Volume Oscillator.

    Identifies long-term trends of money flow.

    Returns struct with (kvo, signal).

    Parameters
    - fast_period (int, default: 34): fast EMA period
    - slow_period (int, default: 55): slow EMA period
    - signal_period (int, default: 13): signal line period
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - close_column (str, default: "close"): close price column
    - volume_column (str, default: "volume"): volume column
    - output_columns (list[str] | None): optional; must contain exactly 2 names.

    Output/Response
    - `data` contains `current_candle` plus 2 KVO columns.
    - Output column names: `[<kvo>, <signal>]`.
    """

    def __init__(
        self,
        fast_period: int = 34,
        slow_period: int = 55,
        signal_period: int = 13,
        high_column: str = "high",
        low_column: str = "low",
        close_column: str = "close",
        volume_column: str = "volume",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.volume_column = volume_column
        self.output_columns_list = output_columns or ["kvo", "kvo_signal"]

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)
        close = pl.col(self.close_column)
        volume = pl.col(self.volume_column)

        # Trend calculation
        hlc3 = (high + low + close) / 3
        trend = pl.when(hlc3 > hlc3.shift(1)).then(1).otherwise(-1)

        # Volume Force
        vf = trend * volume * (2 * (high.diff() / (high - low)) - 1)

        # KVO line
        alpha_fast = 2.0 / (self.fast_period + 1)
        alpha_slow = 2.0 / (self.slow_period + 1)
        kvo_line = vf.ewm_mean(alpha=alpha_fast) - vf.ewm_mean(alpha=alpha_slow)

        # Signal line
        alpha_signal = 2.0 / (self.signal_period + 1)
        signal_line = kvo_line.ewm_mean(alpha=alpha_signal)

        return pl.struct(kvo=kvo_line, signal=signal_line)

    def _exprs(self) -> List[pl.Expr]:
        struct_expr = self.build()
        return [
            struct_expr.struct.field("kvo").alias(self.output_columns_list[0]),
            struct_expr.struct.field("signal").alias(self.output_columns_list[1]),
        ]

    def output_columns(self) -> List[str]:
        return self.output_columns_list

    def required_columns(self) -> List[str]:
        return [
            self.high_column,
            self.low_column,
            self.close_column,
            self.volume_column,
        ]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 2:
                raise ValueError("KVO expects exactly 2 output column names")
            if not all(
                isinstance(name, str) and name
                for name in self._requested_output_columns
            ):
                raise ValueError("All output column names must be non-empty strings")
            self.output_columns_list = self._requested_output_columns

    def window_size(self) -> int:
        return self.slow_period

    def warmup_size(self) -> int:
        return self.slow_period * 3
