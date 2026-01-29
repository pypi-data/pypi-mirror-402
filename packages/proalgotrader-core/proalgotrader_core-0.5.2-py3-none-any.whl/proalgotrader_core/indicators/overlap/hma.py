import polars as pl
import math

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class HMA(Indicator):
    """
    Hull Moving Average (HMA).

    The Hull Moving Average (HMA) is a fast and smooth moving average that eliminates
    the lag associated with traditional moving averages. It uses weighted moving averages
    to reduce noise while maintaining responsiveness to price changes.

    Formula: HMA = WMA(2 * WMA(price, period/2) - WMA(price, period), sqrt(period))

    Parameters
    - timeperiod (int, default: 14): lookback window length
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `hma_{timeperiod}_{column}` (e.g. `hma_14_close`).

    Output/Response
    - `data` contains `current_candle` plus 1 HMA column.
    - Output column names: `[<hma_column>]`. Default: `hma_{timeperiod}_{column}`.
    """

    def __init__(
        self,
        timeperiod: int = 14,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.timeperiod = timeperiod
        self.column = column
        self.hma_col = f"hma_{timeperiod}_{column}"
        self._requested_output_columns = output_columns

        # Calculate sub-periods for HMA formula
        self.half_period = max(1, self.timeperiod // 2)
        self.sqrt_period = max(1, int(math.sqrt(self.timeperiod)))

    def _create_wma_expr(self, column_expr: pl.Expr, period: int) -> pl.Expr:
        """
        Create a weighted moving average expression using manual calculation.

        WMA = (price1*1 + price2*2 + ... + priceN*N) / (1+2+...+N)
        """
        # Create a list to hold weighted values
        weighted_sum_parts = []

        # Calculate weights and their sum
        weight_sum = (period * (period + 1)) // 2  # Sum of 1+2+...+period

        # Create weighted sum: each value multiplied by its weight
        for i in range(period):
            weight = i + 1
            shifted_value = column_expr.shift(period - 1 - i)
            weighted_sum_parts.append(shifted_value * weight)

        # Sum all weighted parts and divide by weight sum
        weighted_sum = pl.sum_horizontal(weighted_sum_parts)
        return weighted_sum / weight_sum

    def build(self) -> pl.Expr:
        """
        Build the Hull Moving Average expression.
        HMA = WMA(2 * WMA(price, period/2) - WMA(price, period), sqrt(period))
        """
        price_col = pl.col(self.column)

        # Step 1: Calculate WMA with half period and full period
        wma_half = self._create_wma_expr(price_col, self.half_period)
        wma_full = self._create_wma_expr(price_col, self.timeperiod)

        # Step 2: Calculate raw HMA: 2 * WMA(half) - WMA(full)
        raw_hma = 2 * wma_half - wma_full

        # Step 3: Apply final WMA smoothing with sqrt(period)
        hma = self._create_wma_expr(raw_hma, self.sqrt_period)

        return hma

    def expr(self) -> pl.Expr:
        return self.build().alias(self.hma_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        return [self.hma_col]

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "HMA expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("HMA requires a non-empty single output column name")
            self.hma_col = requested

    def window_size(self) -> int:
        return self.timeperiod

    def warmup_size(self) -> int:
        # HMA needs extra warmup due to multiple WMA calculations
        # The sqrt smoothing adds additional lag
        return self.timeperiod * 3 + self.sqrt_period
