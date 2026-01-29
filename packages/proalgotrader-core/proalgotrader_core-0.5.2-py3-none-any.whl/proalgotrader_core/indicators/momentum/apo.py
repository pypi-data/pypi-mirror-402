import polars as pl

from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class APO(Indicator):
    """
    Absolute Price Oscillator (APO).

    The Absolute Price Oscillator is a momentum oscillator that shows the difference
    between two moving averages of different periods. It provides information about
    the momentum and trend direction of the price.

    Unlike percentage-based oscillators, APO shows the absolute difference between
    the fast and slow moving averages, making it useful for comparing momentum
    across different price levels.

    Parameters
    - fastperiod (int, default: 12): fast moving average period
    - slowperiod (int, default: 26): slow moving average period
    - matype (int, default: 0): moving average type (0=SMA, 1=EMA, etc.)
    - column (str, default: "close"): input column name
    - output_columns (list[str] | None): optional; must contain exactly 1 name.
      If omitted, the default name is `apo_{fastperiod}_{slowperiod}_{column}` (e.g. `apo_12_26_close`).

    Output/Response
    - `data` contains `current_candle` plus 1 APO column.
    - Output column names: `[<apo>]`. Default: `apo_{fastperiod}_{slowperiod}_{column}`.
    """

    def __init__(
        self,
        fastperiod: int = 12,
        slowperiod: int = 26,
        matype: int = 0,
        column: str = "close",
        output_columns: Optional[List[str]] = None,
    ) -> None:
        super().__init__()
        self.fastperiod = fastperiod
        self.slowperiod = slowperiod
        self.matype = matype
        self.column = column
        self.apo_col = f"apo_{fastperiod}_{slowperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        source = pl.col(self.column)

        # Calculate MA based on matype (0=SMA, 1=EMA)
        if self.matype == 0:
            fast_ma = source.rolling_mean(window_size=self.fastperiod)
            slow_ma = source.rolling_mean(window_size=self.slowperiod)
        elif self.matype == 1:
            alpha_fast = 2.0 / (self.fastperiod + 1)
            alpha_slow = 2.0 / (self.slowperiod + 1)
            fast_ma = source.ewm_mean(alpha=alpha_fast, adjust=False)
            slow_ma = source.ewm_mean(alpha=alpha_slow, adjust=False)
        else:
            # Default to SMA for other types
            fast_ma = source.rolling_mean(window_size=self.fastperiod)
            slow_ma = source.rolling_mean(window_size=self.slowperiod)

        return fast_ma - slow_ma

    def _exprs(self) -> List[pl.Expr]:
        return [self.build().alias(self.apo_col)]

    def output_columns(self) -> List[str]:
        return [self.apo_col]

    def required_columns(self) -> List[str]:
        return [self.column]

    def validate_output_columns(self) -> None:
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "APO expects exactly 1 output column name in 'output_columns'"
                )
            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("APO requires a non-empty single output column name")
            self.apo_col = requested

    def window_size(self) -> int:
        return max(self.fastperiod, self.slowperiod)

    def warmup_size(self) -> int:
        return self.window_size() * 3
