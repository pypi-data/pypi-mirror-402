import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class KST(Indicator):
    """
    Know Sure Thing (KST).

    A momentum oscillator that combines multiple rate-of-change values.

    Returns struct with (kst, signal).

    Parameters
    - roc1 (int, default: 10): first ROC period
    - roc2 (int, default: 15): second ROC period
    - roc3 (int, default: 20): third ROC period
    - roc4 (int, default: 30): fourth ROC period
    - sma1 (int, default: 10): SMA period for first ROC
    - sma2 (int, default: 10): SMA period for second ROC
    - sma3 (int, default: 10): SMA period for third ROC
    - sma4 (int, default: 15): SMA period for fourth ROC
    - signal (int, default: 9): signal line period
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 2 names.

    Output/Response
    - `data` contains `current_candle` plus 2 KST columns.
    - Output column names: `[<kst>, <signal>]`. Default: `[kst, signal]`.
    """

    def __init__(
        self,
        roc1: int = 10,
        roc2: int = 15,
        roc3: int = 20,
        roc4: int = 30,
        sma1: int = 10,
        sma2: int = 10,
        sma3: int = 10,
        sma4: int = 15,
        signal: int = 9,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.roc1 = roc1
        self.roc2 = roc2
        self.roc3 = roc3
        self.roc4 = roc4
        self.sma1 = sma1
        self.sma2 = sma2
        self.sma3 = sma3
        self.sma4 = sma4
        self.signal = signal
        self.column = column
        self.output_columns_list = output_columns or ["kst", "signal"]

    def _roc(self, source: pl.Expr, timeperiod: int) -> pl.Expr:
        """Rate of Change helper."""
        return 100 * (source - source.shift(timeperiod)) / source.shift(timeperiod)

    def _sma(self, source: pl.Expr, timeperiod: int) -> pl.Expr:
        """Simple Moving Average helper."""
        return source.rolling_mean(window_size=timeperiod)

    def build(self) -> pl.Expr:
        source = pl.col(self.column)

        # Calculate ROCs
        r1 = self._roc(source, self.roc1)
        r2 = self._roc(source, self.roc2)
        r3 = self._roc(source, self.roc3)
        r4 = self._roc(source, self.roc4)

        # Smooth each ROC
        k1 = self._sma(r1, self.sma1)
        k2 = self._sma(r2, self.sma2)
        k3 = self._sma(r3, self.sma3)
        k4 = self._sma(r4, self.sma4)

        # KST formula
        kst_value = 1 * k1 + 2 * k2 + 3 * k3 + 4 * k4
        kst_final = kst_value / 10

        # Signal line
        signal_line = self._sma(kst_final, self.signal)

        return pl.struct(kst=kst_final, signal=signal_line)

    def _exprs(self) -> List[pl.Expr]:
        struct_expr = self.build()
        return [
            struct_expr.struct.field("kst").alias(self.output_columns_list[0]),
            struct_expr.struct.field("signal").alias(self.output_columns_list[1]),
        ]

    def output_columns(self) -> List[str]:
        return self.output_columns_list

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 2:
                raise ValueError("KST expects exactly 2 output column names")
            if not all(
                isinstance(name, str) and name
                for name in self._requested_output_columns
            ):
                raise ValueError("All output column names must be non-empty strings")
            self.output_columns_list = self._requested_output_columns

    def window_size(self) -> int:
        return max(self.roc1, self.roc2, self.roc3, self.roc4)

    def warmup_size(self) -> int:
        return self.window_size() * 3
