from __future__ import annotations
from typing import List, Sequence, Union
import asyncio
import polars as pl

from proalgotrader_core.protocols.position import PositionProtocol
from proalgotrader_core.protocols.trade import TradeProtocol

PositionLike = Union[
    PositionProtocol, Sequence[PositionProtocol], List[PositionProtocol]
]

TradeLike = Union[TradeProtocol, Sequence[TradeProtocol], List[TradeProtocol]]

PositionOrTradeLike = Union[PositionLike, TradeLike]


class PnlCalculator:
    """
    High-performance P&L calculator using Polars for vectorized operations.

    Provides scalable calculation of profit/loss metrics from position and trade data.
    - Positions: Unrealized P&L (open positions)
    - Trades: Realized P&L (completed trades)
    Uses lazy evaluation and caching for optimal performance.
    """

    def __init__(self, data: PositionOrTradeLike) -> None:
        # Separate positions and trades
        self._positions: List[PositionProtocol] = []
        self._trades: List[TradeProtocol] = []

        if isinstance(data, (list, tuple)):
            items = list(data)
        else:
            items = [data] if data else []

        # Categorize items as positions or trades
        for item in items:
            if hasattr(item, "position_id"):  # Position
                self._positions.append(item)
            elif hasattr(item, "trade_id"):  # Trade
                self._trades.append(item)

        self._position_df: pl.DataFrame | None = None
        self._trade_df: pl.DataFrame | None = None
        self._base_investment_cache: float | None = None

    async def _position_dataframe(self) -> pl.DataFrame:
        """Lazy-loaded dataframe creation for positions (unrealized P&L)."""
        if self._position_df is None:
            self._position_df = await self._create_position_dataframe()
        return self._position_df

    @property
    def _trade_dataframe(self) -> pl.DataFrame:
        """Lazy-loaded dataframe creation for trades (realized P&L)."""
        if self._trade_df is None:
            self._trade_df = self._create_trade_dataframe()
        return self._trade_df

    async def _create_position_dataframe(self) -> pl.DataFrame:
        """Create optimized Polars DataFrame from positions (unrealized P&L)."""
        if not self._positions:
            return self._empty_position_dataframe()

        # Get LTP values for all positions concurrently
        ltp_values = await asyncio.gather(
            *[p.broker_symbol.get_ltp() for p in self._positions]
        )

        # Extract data for positions (unrealized P&L)
        data = {
            "is_buy": [p.is_buy for p in self._positions],
            "net_price": [float(p.net_price or 0.0) for p in self._positions],
            "net_quantities": [int(p.net_quantities) for p in self._positions],
            "ltp": [float(ltp) for ltp in ltp_values],
        }
        return pl.DataFrame(data)

    def _create_trade_dataframe(self) -> pl.DataFrame:
        """Create optimized Polars DataFrame from trades (realized P&L)."""
        if not self._trades:
            return self._empty_trade_dataframe()

        # Extract data for trades (realized P&L)
        data = {
            "is_buy": [t.position_type == "BUY" for t in self._trades],
            "buy_price": [float(t.buy_price or 0.0) for t in self._trades],
            "sell_price": [float(t.sell_price or 0.0) for t in self._trades],
            "net_quantities": [int(t.net_quantities) for t in self._trades],
        }
        return pl.DataFrame(data)

    def _empty_position_dataframe(self) -> pl.DataFrame:
        """Create empty DataFrame for positions with proper schema."""
        return pl.DataFrame(
            {
                "is_buy": pl.Series([], dtype=pl.Boolean),
                "net_price": pl.Series([], dtype=pl.Float64),
                "net_quantities": pl.Series([], dtype=pl.Int64),
                "ltp": pl.Series([], dtype=pl.Float64),
            }
        )

    def _empty_trade_dataframe(self) -> pl.DataFrame:
        """Create empty DataFrame for trades with proper schema."""
        return pl.DataFrame(
            {
                "is_buy": pl.Series([], dtype=pl.Boolean),
                "buy_price": pl.Series([], dtype=pl.Float64),
                "sell_price": pl.Series([], dtype=pl.Float64),
                "net_quantities": pl.Series([], dtype=pl.Int64),
            }
        )

    async def net_pnl(self) -> float:
        """Calculate total P&L (realized + unrealized)."""
        return await self.realized_pnl() + await self.unrealized_pnl()

    async def realized_pnl(self) -> float:
        """Calculate realized P&L from completed trades."""
        if not self._trades:
            return 0.0

        df = self._trade_dataframe
        if df.is_empty():
            return 0.0

        # Calculate realized P&L from trades
        pnl_df = df.with_columns(
            [
                # Entry price (buy price for buy trades, sell price for sell trades)
                pl.when(pl.col("is_buy"))
                .then(pl.col("buy_price"))
                .otherwise(pl.col("sell_price"))
                .alias("entry_price"),
                # Exit price (sell price for buy trades, buy price for sell trades)
                pl.when(pl.col("is_buy"))
                .then(pl.col("sell_price"))
                .otherwise(pl.col("buy_price"))
                .alias("exit_price"),
            ]
        ).with_columns(
            [
                # Calculate P&L per trade
                pl.when(
                    (pl.col("entry_price") > 0)
                    & (pl.col("exit_price") > 0)
                    & (pl.col("net_quantities") > 0)
                )
                .then(
                    pl.when(pl.col("is_buy"))
                    .then(
                        (pl.col("exit_price") - pl.col("entry_price"))
                        * pl.col("net_quantities")
                    )
                    .otherwise(
                        (pl.col("entry_price") - pl.col("exit_price"))
                        * pl.col("net_quantities")
                    )
                )
                .otherwise(0.0)
                .alias("trade_pnl")
            ]
        )

        total_pnl = pnl_df["trade_pnl"].sum()
        return round(total_pnl, 2) if total_pnl else 0.0

    async def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L from open positions."""
        if not self._positions:
            return 0.0

        df = await self._position_dataframe()
        if df.is_empty():
            return 0.0

        # Calculate unrealized P&L from positions
        pnl_df = df.with_columns(
            [
                # Calculate P&L per position (current LTP vs entry price)
                pl.when(
                    (pl.col("net_price") > 0)
                    & (pl.col("ltp") > 0)
                    & (pl.col("net_quantities") > 0)
                )
                .then(
                    pl.when(pl.col("is_buy"))
                    .then(
                        (pl.col("ltp") - pl.col("net_price")) * pl.col("net_quantities")
                    )
                    .otherwise(
                        (pl.col("net_price") - pl.col("ltp")) * pl.col("net_quantities")
                    )
                )
                .otherwise(0.0)
                .alias("position_pnl")
            ]
        )

        total_pnl = pnl_df["position_pnl"].sum()
        return round(total_pnl, 2) if total_pnl else 0.0

    async def profit(self) -> float:
        """Return total profit amount (positive P&L only)."""
        pnl = await self.net_pnl()
        return round(pnl, 2) if pnl > 0 else 0.0

    async def loss(self) -> float:
        """Return total loss amount (negative P&L as positive value)."""
        pnl = await self.net_pnl()
        return round(-pnl, 2) if pnl < 0 else 0.0

    async def realized_profit(self) -> float:
        """Return realized profit amount (positive realized P&L only)."""
        pnl = await self.realized_pnl()
        return round(pnl, 2) if pnl > 0 else 0.0

    async def realized_loss(self) -> float:
        """Return realized loss amount (negative realized P&L as positive value)."""
        pnl = await self.realized_pnl()
        return round(-pnl, 2) if pnl < 0 else 0.0

    async def unrealized_profit(self) -> float:
        """Return unrealized profit amount (positive unrealized P&L only)."""
        pnl = await self.unrealized_pnl()
        return round(pnl, 2) if pnl > 0 else 0.0

    async def unrealized_loss(self) -> float:
        """Return unrealized loss amount (negative unrealized P&L as positive value)."""
        pnl = await self.unrealized_pnl()
        return round(-pnl, 2) if pnl < 0 else 0.0

    async def _calculate_base_investment(self) -> float:
        """Calculate total investment amount (cached for performance)."""
        if self._base_investment_cache is not None:
            return self._base_investment_cache

        # Calculate investment from positions (unrealized)
        position_investment = 0.0
        if self._positions:
            pos_df = await self._position_dataframe()
            if not pos_df.is_empty():
                pos_investment_df = pos_df.with_columns(
                    [
                        (pl.col("net_price") * pl.col("net_quantities")).alias(
                            "investment"
                        )
                    ]
                )
                position_investment = pos_investment_df["investment"].sum() or 0.0

        # Calculate investment from trades (realized)
        trade_investment = 0.0
        if self._trades:
            trade_df = self._trade_dataframe
            if not trade_df.is_empty():
                trade_investment_df = trade_df.with_columns(
                    [
                        pl.when(pl.col("is_buy"))
                        .then(pl.col("buy_price"))
                        .otherwise(pl.col("sell_price"))
                        .alias("entry_price"),
                    ]
                ).with_columns(
                    [
                        (pl.col("entry_price") * pl.col("net_quantities")).alias(
                            "investment"
                        )
                    ]
                )
                trade_investment = trade_investment_df["investment"].sum() or 0.0

        total_investment = position_investment + trade_investment
        self._base_investment_cache = total_investment
        return self._base_investment_cache

    async def net_pnl_percentage(self) -> float:
        """Calculate total P&L as percentage of total investment."""
        base = await self._calculate_base_investment()
        if base <= 0:
            return 0.0
        return round((await self.net_pnl() * 100.0) / base, 2)

    async def profit_percentage(self) -> float:
        """Calculate total profit as percentage of total investment."""
        base = await self._calculate_base_investment()
        if base <= 0:
            return 0.0
        return round((await self.profit() * 100.0) / base, 2)

    async def loss_percentage(self) -> float:
        """Calculate total loss as percentage of total investment."""
        base = await self._calculate_base_investment()
        if base <= 0:
            return 0.0
        return round((await self.loss() * 100.0) / base, 2)

    async def realized_pnl_percentage(self) -> float:
        """Calculate realized P&L as percentage of trade investment."""
        if not self._trades:
            return 0.0

        trade_df = self._trade_dataframe
        if trade_df.is_empty():
            return 0.0

        # Calculate trade investment
        trade_investment_df = trade_df.with_columns(
            [
                pl.when(pl.col("is_buy"))
                .then(pl.col("buy_price"))
                .otherwise(pl.col("sell_price"))
                .alias("entry_price"),
            ]
        ).with_columns(
            [(pl.col("entry_price") * pl.col("net_quantities")).alias("investment")]
        )

        trade_investment = trade_investment_df["investment"].sum()
        if trade_investment <= 0:
            return 0.0
        return round((await self.realized_pnl() * 100.0) / trade_investment, 2)

    async def unrealized_pnl_percentage(self) -> float:
        """Calculate unrealized P&L as percentage of position investment."""
        if not self._positions:
            return 0.0

        pos_df = await self._position_dataframe()
        if pos_df.is_empty():
            return 0.0

        # Calculate position investment
        pos_investment_df = pos_df.with_columns(
            [(pl.col("net_price") * pl.col("net_quantities")).alias("investment")]
        )

        pos_investment = pos_investment_df["investment"].sum()
        if pos_investment <= 0:
            return 0.0
        return round((await self.unrealized_pnl() * 100.0) / pos_investment, 2)

    def invalidate_cache(self) -> None:
        """Invalidate internal caches when positions or trades change."""
        self._position_df = None
        self._trade_df = None
        self._base_investment_cache = None
