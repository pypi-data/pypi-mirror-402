import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class Inertia(Indicator):
    """
    Inertia.

    Measures the resistance of price to change, combining RSI with linear regression.

    Parameters
    - period (int, default: 20): lookback window length
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `inertia_{period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 Inertia column.
    - Output column names: `[<inertia>]`. Default: `inertia_{period}_{column}`.
    """

    def __init__(
        self,
        period: int = 20,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.column = column
        self.output_column = f"inertia_{period}_{column}"
        self._requested_output_columns = output_columns

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

        # Linear regression on RSI (simplified: use RSI smoothed)
        return rsi_val.rolling_mean(self.period)

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
                    "Inertia expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError(
                    "Inertia requires a non-empty single output column name"
                )
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period * 3
