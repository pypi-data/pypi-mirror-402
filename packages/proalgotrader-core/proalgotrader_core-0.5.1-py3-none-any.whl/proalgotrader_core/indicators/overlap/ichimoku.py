import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class Ichimoku(Indicator):
    """
    Ichimoku Cloud.

    Returns struct with (tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span).

    Parameters
    - tenkan_period (int, default: 9): conversion line period
    - kijun_period (int, default: 26): base line period
    - senkou_span_b_period (int, default: 52): leading span B period
    - displacement (int, default: 26): displacement for cloud
    - high_column (str, default: "high"): high price column
    - low_column (str, default: "low"): low price column
    - close_column (str, default: "close"): close price column
    - output_columns (list[str] | None): optional; must contain exactly 5 names.

    Output/Response
    - `data` contains `current_candle` plus 5 Ichimoku columns.
    - Output column names: `[tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span]`.
    """

    def __init__(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_span_b_period: int = 52,
        displacement: int = 26,
        high_column: str = "high",
        low_column: str = "low",
        close_column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_span_b_period = senkou_span_b_period
        self.displacement = displacement
        self.high_column = high_column
        self.low_column = low_column
        self.close_column = close_column
        self.output_columns_list = output_columns or [
            "tenkan_sen",
            "kijun_sen",
            "senkou_span_a",
            "senkou_span_b",
            "chikou_span",
        ]

    def build(self) -> pl.Expr:
        high = pl.col(self.high_column)
        low = pl.col(self.low_column)
        close = pl.col(self.close_column)

        # Tenkan-sen (Conversion Line)
        tenkan_sen = (
            high.rolling_max(self.tenkan_period) + low.rolling_min(self.tenkan_period)
        ) / 2

        # Kijun-sen (Base Line)
        kijun_sen = (
            high.rolling_max(self.kijun_period) + low.rolling_min(self.kijun_period)
        ) / 2

        # Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(self.displacement)

        # Senkou Span B (Leading Span B)
        senkou_span_b = (
            (
                high.rolling_max(self.senkou_span_b_period)
                + low.rolling_min(self.senkou_span_b_period)
            )
            / 2
        ).shift(self.displacement)

        # Chikou Span (Lagging Span)
        chikou_span = close.shift(-self.displacement)

        return pl.struct(
            tenkan_sen=tenkan_sen,
            kijun_sen=kijun_sen,
            senkou_span_a=senkou_span_a,
            senkou_span_b=senkou_span_b,
            chikou_span=chikou_span,
        )

    def _exprs(self) -> List[pl.Expr]:
        struct_expr = self.build()
        return [
            struct_expr.struct.field("tenkan_sen").alias(self.output_columns_list[0]),
            struct_expr.struct.field("kijun_sen").alias(self.output_columns_list[1]),
            struct_expr.struct.field("senkou_span_a").alias(
                self.output_columns_list[2]
            ),
            struct_expr.struct.field("senkou_span_b").alias(
                self.output_columns_list[3]
            ),
            struct_expr.struct.field("chikou_span").alias(self.output_columns_list[4]),
        ]

    def output_columns(self) -> List[str]:
        return self.output_columns_list

    def required_columns(self) -> List[str]:
        return [self.high_column, self.low_column, self.close_column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 5:
                raise ValueError("Ichimoku expects exactly 5 output column names")
            if not all(
                isinstance(name, str) and name
                for name in self._requested_output_columns
            ):
                raise ValueError("All output column names must be non-empty strings")
            self.output_columns_list = self._requested_output_columns

    def window_size(self) -> int:
        return max(self.tenkan_period, self.kijun_period, self.senkou_span_b_period)

    def warmup_size(self) -> int:
        return self.window_size() * 3
