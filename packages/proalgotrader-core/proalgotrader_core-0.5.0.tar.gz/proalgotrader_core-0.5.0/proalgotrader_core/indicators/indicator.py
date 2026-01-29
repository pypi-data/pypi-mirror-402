import polars as pl

from typing import List, Optional, Any, TYPE_CHECKING

from proalgotrader_core.algo_session import AlgoSession
from proalgotrader_core._helpers.data_validation import get_dataframe_row

if TYPE_CHECKING:
    from proalgotrader_core.chart import Chart
    from proalgotrader_core.protocols.tick import TickProtocol


class Indicator:
    """
    Base class for indicators built on Polars expressions.

    Subclasses must implement `_exprs()` to return a list of `pl.Expr` that
    will be added to a DataFrame via `with_columns`. They should also provide
    `output_columns` to list column names produced.
    """

    def __init__(self) -> None:
        self._df: Optional[pl.DataFrame] = None
        self.algo_session: Optional[AlgoSession] = None
        self.chart: Optional["Chart"] = None

        self._output_validated: bool = False
        # Child classes can set this to capture user-desired output names
        self._requested_output_columns: Optional[List[str]] = None

    @property
    def data(self) -> pl.DataFrame | None:
        """Return the last computed DataFrame containing the indicator columns."""
        if self._df is None:
            return None

        if self.algo_session is None:
            return None

        return self._df.filter(
            pl.col("current_candle") <= self.algo_session.current_datetime
        )

    async def get_data(
        self, row_number: int = 0, column_name: Optional[str] = None
    ) -> Any:
        return get_dataframe_row(self.data, row_number, column_name)

    async def initialize(
        self,
        chart: Optional["Chart"] = None,
    ) -> None:
        """One-time preparation and initial computation for historical data."""
        # Always attach the chart during initialization
        self.chart = chart
        # Access algo_session through chart
        if chart:
            self.algo_session = chart.algo_session

        if not self._output_validated:
            self.validate_output_columns()
            self._output_validated = True

        # Validate required input columns once at initialization
        if self.chart is None:
            raise ValueError(
                f"Chart is required for {self.__class__.__name__} initialization"
            )

        chart_df = self.chart.df
        missing = [c for c in self.required_columns() if c not in chart_df.columns]

        if missing:
            raise ValueError(
                f"Input columns missing for {self.__class__.__name__}: {missing}. Available: {chart_df.columns}"
            )

        # Initial compute over historical data; store only indicator columns + current_candle + current_timestamp+ current_datetime + symbol
        self._df = chart_df.select(
            pl.col("current_candle"),
            pl.col("current_timestamp"),
            pl.col("current_datetime"),
            pl.col("symbol"),
            # Round all indicator outputs to 2 decimals
            *(expr.round(2) for expr in self._exprs()),
        )

        # Subscribe to broker symbol for real-time updates if chart is available
        if self.chart and self.chart.broker_symbol and self.chart.order_broker_manager:
            await self.chart.order_broker_manager.subscribe(
                self.chart.broker_symbol, self.on_tick
            )

    async def next(self, chart_df: Optional[pl.DataFrame] = None) -> None:
        """Compute only for the latest tick using a trailing window for performance."""
        # Use chart.df if no chart_df is provided
        if chart_df is None:
            if self.chart is None:
                raise ValueError(
                    f"Chart is required for {self.__class__.__name__} next() method"
                )
            chart_df = self.chart.df

        total_window = max(1, self.window_size() + self.warmup_size())

        # Compute only over a trailing slice
        tail_df = chart_df.tail(total_window)
        partial = tail_df.select(
            pl.col("current_candle"),
            pl.col("current_timestamp"),
            pl.col("current_datetime"),
            pl.col("symbol"),
            # Round all indicator outputs to 2 decimals
            *(expr.round(2) for expr in self._exprs()),
        )

        # If no existing data, seed with the partial window
        if self._df is None or self._df.height == 0:
            self._df = partial
            return

        # Merge only the latest row for minimal update
        latest_row = partial.tail(1)
        latest_candle = latest_row.get_column("current_candle").item()
        existing_last_candle = self._df.get_column("current_candle").last()

        if existing_last_candle == latest_candle:
            # Replace last row
            self._df = pl.concat([self._df[:-1], latest_row])
        else:
            # Append new row
            self._df = pl.concat([self._df, latest_row])

    async def on_tick(self, tick: "TickProtocol") -> None:
        """Handle real-time tick updates for the indicator."""
        # Update indicator calculations with latest chart data
        await self.next()

    async def series(self, column: Optional[str] = None) -> Optional[pl.Series]:
        """
        Convenience accessor for a single indicator series from the last
        computed `data` frame. If the indicator defines exactly one output
        column, `column` can be omitted. Otherwise, pass a specific column name.
        Returns `None` if no computed data is available yet.
        """
        df = self.data
        if df is None:
            return None

        outputs = self.output_columns()
        if column is None:
            if len(outputs) != 1:
                raise ValueError(
                    "Indicator produces multiple columns; specify 'column' explicitly"
                )
            column = outputs[0]

        return df.get_column(column)

    async def last_value(self, column: Optional[str] = None) -> Optional[float]:
        """Return the latest value from a given output column, if available."""
        s = await self.series(column=column)
        return None if s is None or s.len() == 0 else s.tail(1).item()

    # Methods to be implemented by subclasses
    def _exprs(self) -> List[pl.Expr]:
        raise NotImplementedError

    def output_columns(self) -> List[str]:
        raise NotImplementedError

    def required_columns(self) -> List[str]:
        return []

    # Design contract: every indicator must validate its output columns
    def validate_output_columns(self) -> None:
        raise NotImplementedError

    # Window configuration (can be overridden by subclasses)
    def window_size(self) -> int:
        """Minimum lookback required for exact last-value computation."""
        return 0

    def warmup_size(self) -> int:
        """Extra lookback to stabilize recursive indicators."""
        return 0
