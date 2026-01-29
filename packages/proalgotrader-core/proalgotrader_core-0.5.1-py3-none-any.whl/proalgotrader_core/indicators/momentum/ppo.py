import polars as pl
from typing import List, Optional

from proalgotrader_core.indicators.indicator import Indicator


class PPO(Indicator):
    """
    PPO - Percentage Price Oscillator

    The Percentage Price Oscillator (PPO) is a momentum oscillator that measures
    the percentage difference between two exponential moving averages. It is
    essentially the MACD indicator expressed in percentage terms, making it more
    suitable for comparing momentum across securities with different price levels.

    The PPO is calculated as:
    PPO = ((Fast EMA - Slow EMA) / Slow EMA) * 100

    Where:
    - Fast EMA: Exponential Moving Average of the faster period (default: 12)
    - Slow EMA: Exponential Moving Average of the slower period (default: 26)
    - Signal Line: EMA of PPO values (default: 9 periods)

    Key characteristics:
    - Range: Unbounded but typically oscillates around zero
    - Percentage-based calculation allows cross-security comparison
    - More suitable than MACD for securities with different price levels
    - Zero line crossings indicate momentum changes
    - Signal line crossovers generate buy/sell signals

    The PPO addresses a key limitation of MACD - its absolute values make it
    difficult to compare momentum between securities with vastly different prices.
    For example, a stock trading at $10 vs. $100 will have very different MACD
    values even with identical percentage movements. PPO normalizes this by
    expressing the difference as a percentage.

    Interpretation:
    - PPO > 0: Fast EMA above slow EMA (bullish momentum)
    - PPO < 0: Fast EMA below slow EMA (bearish momentum)
    - PPO crossing above zero: Potential bullish signal
    - PPO crossing below zero: Potential bearish signal
    - PPO above signal line: Bullish momentum strengthening
    - PPO below signal line: Bearish momentum strengthening

    Common applications:
    - Cross-security momentum comparison
    - Trend identification and confirmation
    - Signal generation through zero line crossings
    - Signal line crossovers for entry/exit points
    - Divergence analysis between PPO and price
    - Portfolio screening for momentum-based selection

    Trading signals:
    - Buy signal: PPO crosses above signal line while both are below zero
    - Sell signal: PPO crosses below signal line while both are above zero
    - Bullish divergence: Price makes lower lows while PPO makes higher lows
    - Bearish divergence: Price makes higher highs while PPO makes lower highs

    Advantages over MACD:
    - Normalized values allow cross-security comparison
    - Better for portfolio-wide momentum analysis
    - More meaningful for securities with different price ranges
    - Easier to set universal thresholds and alerts
    - Superior for relative strength analysis

    Advantages over simple moving average crossovers:
    - More responsive due to exponential smoothing
    - Signal line provides additional confirmation
    - Histogram shows momentum changes more clearly
    - Better divergence signals

    Limitations:
    - Lagging indicator due to moving average basis
    - Can generate false signals in choppy markets
    - Requires confirmation from other indicators
    - Less effective in strongly trending markets without pullbacks

    Parameters:
    - fastperiod: Period for fast EMA (default: 12)
    - slowperiod: Period for slow EMA (default: 26)
    - matype: Moving average type (default: 0 = EMA)
    - column: The price column to use (default: "close")
    - output_columns: Optional list to override default output column names

    Example:
        ppo = PPO()  # Default periods: 12, 26
        ppo_fast = PPO(fastperiod=8, slowperiod=21)
        ppo_custom = PPO(fastperiod=12, slowperiod=26, output_columns=["ppo_percentage"])
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
        self.ppo_col = f"ppo_{fastperiod}_{slowperiod}_{column}"
        self._requested_output_columns = output_columns

    def build(self) -> pl.Expr:
        """Build the PPO expression."""
        source = pl.col(self.column)

        # Calculate EMAs
        alpha_fast = 2.0 / (self.fastperiod + 1)
        alpha_slow = 2.0 / (self.slowperiod + 1)

        fast_ma = source.ewm_mean(alpha=alpha_fast, adjust=False)
        slow_ma = source.ewm_mean(alpha=alpha_slow, adjust=False)

        # Calculate PPO as percentage
        return 100 * (fast_ma - slow_ma) / slow_ma

    def expr(self) -> pl.Expr:
        """Return the PPO expression with proper column alias."""
        return self.build().alias(self.ppo_col)

    def _exprs(self) -> List[pl.Expr]:
        """Return list of expressions for this indicator."""
        return [self.expr()]

    def output_columns(self) -> List[str]:
        """Return the output column names."""
        return [self.ppo_col]

    def required_columns(self) -> List[str]:
        """Return the required input column names."""
        return [self.column]

    def validate_output_columns(self) -> None:
        """Validate and apply custom output column names if provided."""
        if self._requested_output_columns is not None:
            if len(self._requested_output_columns) != 1:
                raise ValueError(
                    "PPO expects exactly 1 output column name in 'output_columns'"
                )

            requested = self._requested_output_columns[0]
            if not isinstance(requested, str) or not requested:
                raise ValueError("PPO requires a non-empty single output column name")

            self.ppo_col = requested

    def window_size(self) -> int:
        """Return the minimum window size needed for PPO calculation."""
        return max(self.fastperiod, self.slowperiod)

    def warmup_size(self) -> int:
        """Return the warmup size needed for stable PPO calculation."""
        # PPO needs warmup for both EMAs
        # Using 3x longest period for stable calculation
        return max(self.fastperiod, self.slowperiod) * 3
