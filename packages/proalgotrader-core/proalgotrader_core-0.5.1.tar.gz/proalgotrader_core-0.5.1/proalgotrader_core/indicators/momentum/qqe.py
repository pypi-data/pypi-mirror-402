import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class QQE(Indicator):
    """
    Quantitative Qualitative Estimation (QQE).

    An improved version of RSI with smoothed bands.

    Returns struct with (qqe, rsi, upper_band, lower_band).

    Parameters
    - period (int, default: 14): RSI period
    - smooth (int, default: 5): smoothing period
    - factor (float, default: 4.238): band width factor
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 4 names.

    Output/Response
    - `data` contains `current_candle` plus 4 QQE columns.
    - Output column names: `[<qqe>, <rsi>, <upper_band>, <lower_band>]`.
    """

    def __init__(
        self,
        period: int = 14,
        smooth: int = 5,
        factor: float = 4.238,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.smooth = smooth
        self.factor = factor
        self.column = column
        self.output_columns_list = output_columns or [
            "qqe",
            "rsi",
            "upper_band",
            "lower_band",
        ]

    def build(self) -> pl.Expr:
        source = pl.col(self.column)

        # Calculate RSI
        delta = source.diff()
        gains = pl.when(delta > 0).then(delta).otherwise(0)
        losses = pl.when(delta < 0).then(-delta).otherwise(0)

        alpha = 1.0 / self.period
        avg_gain = gains.ewm_mean(adjust=False, alpha=alpha)
        avg_loss = losses.ewm_mean(adjust=False, alpha=alpha)

        rs = avg_gain / pl.when(avg_loss == 0).then(1).otherwise(avg_loss)
        rsi_val = 100 - (100 / (1 + rs))

        # Calculate Wilder's smoothing of RSI changes
        rsi_diff = rsi_val.diff().abs()
        atr_rsi = rsi_diff.ewm_mean(alpha=alpha)

        # Calculate bands
        upper_band = rsi_val + self.factor * atr_rsi
        lower_band = rsi_val - self.factor * atr_rsi

        # QQE line
        alpha_smooth = 2.0 / (self.smooth + 1)
        qqe_val = rsi_val.ewm_mean(alpha=alpha_smooth)

        return pl.struct(
            qqe=qqe_val,
            rsi=rsi_val,
            upper_band=upper_band,
            lower_band=lower_band,
        )

    def _exprs(self) -> List[pl.Expr]:
        struct_expr = self.build()
        return [
            struct_expr.struct.field("qqe").alias(self.output_columns_list[0]),
            struct_expr.struct.field("rsi").alias(self.output_columns_list[1]),
            struct_expr.struct.field("upper_band").alias(self.output_columns_list[2]),
            struct_expr.struct.field("lower_band").alias(self.output_columns_list[3]),
        ]

    def output_columns(self) -> List[str]:
        return self.output_columns_list

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 4:
                raise ValueError("QQE expects exactly 4 output column names")
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
