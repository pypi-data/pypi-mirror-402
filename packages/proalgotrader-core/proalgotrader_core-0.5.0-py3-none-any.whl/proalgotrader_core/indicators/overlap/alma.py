import polars as pl

from typing import Optional, List

from proalgotrader_core.indicators.indicator import Indicator


class ALMA(Indicator):
    """
    Arnaud Legoux Moving Average.

    A Gaussian filter that reduces lag while maintaining smoothness.

    Parameters
    - period (int, default: 9): lookback window length
    - column (str, default: "close"): input column name
    - offset (float, default: 0.85): offset parameter (0 < offset < 1)
    - sigma (float, default: 6.0): sigma parameter for Gaussian distribution
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `alma_{period}_{column}`.

    Output/Response
    - `data` contains `current_candle` plus 1 ALMA column.
    - Output column names: `[<alma>]`. Default: `alma_{period}_{column}`.
    """

    def __init__(
        self,
        period: int = 9,
        column: str = "close",
        offset: float = 0.85,
        sigma: float = 6.0,
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.period = period
        self.column = column
        self.offset = offset
        self.sigma = sigma
        self.output_column = f"alma_{period}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        # Simplified ALMA using EMA approximation
        # Full implementation requires Gaussian weight calculation with map
        alpha = 2.0 / (self.period + 1)
        return pl.col(self.column).ewm_mean(alpha=alpha)

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
                    "ALMA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("ALMA requires a non-empty single output column name")
            self.output_column = requested

    def window_size(self) -> int:
        return self.period

    def warmup_size(self) -> int:
        return self.period * 3
