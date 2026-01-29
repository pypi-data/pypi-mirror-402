"""
Indicators Utility Class

This module provides a centralized class with static methods for all technical
analysis indicators. These are the building blocks used by indicator classes
and can be used directly in custom indicators.

Usage:
    import polars as pl
    from proalgotrader_core.indicators.indicators import Indicators

    # In your custom indicator class
    class MyCustomIndicator(Indicator):
        def build(self) -> pl.Expr:
            return Indicators.build_sma(
                Indicators.build_rsi(pl.col("close"), 14),
                timeperiod=20
            )

    # Or use directly with Polars expressions
    df.select(
        sma=Indicators.build_sma(pl.col("close"), 20),
        rsi=Indicators.build_rsi(pl.col("close"), 14),
        macd=Indicators.build_macd(pl.col("close"))
    )
"""

import polars as pl


class Indicators:
    """
    Centralized utility class containing all technical analysis indicator builders.

    All methods are prefixed with 'build_' and return Polars expressions that
    can be composed together to create custom indicators.
    """

    # ============================================================================
    # OVERLAP STUDIES
    # ============================================================================

    @staticmethod
    def build_sma(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Simple Moving Average."""
        return source.rolling_mean(window_size=timeperiod)

    @staticmethod
    def build_ema(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Exponential Moving Average."""
        alpha = 2.0 / (timeperiod + 1)
        return source.ewm_mean(alpha=alpha, adjust=False)

    @staticmethod
    def build_wma(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Weighted Moving Average."""
        return source.rolling_mean(window_size=timeperiod)

    @staticmethod
    def build_dema(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Double Exponential Moving Average. DEMA = 2 * EMA - EMA(EMA)"""
        ema1 = Indicators.build_ema(source, timeperiod)
        ema2 = Indicators.build_ema(ema1, timeperiod)
        return (2 * ema1) - ema2

    @staticmethod
    def build_tema(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Triple Exponential Moving Average. TEMA = 3*EMA1 - 3*EMA2 + EMA3"""
        ema1 = Indicators.build_ema(source, timeperiod)
        ema2 = Indicators.build_ema(ema1, timeperiod)
        ema3 = Indicators.build_ema(ema2, timeperiod)
        return (3 * ema1) - (3 * ema2) + ema3

    @staticmethod
    def build_trima(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Triangular Moving Average."""
        return source.rolling_mean(window_size=timeperiod)

    @staticmethod
    def build_kama(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Kaufman Adaptive Moving Average."""
        return source.ewm_mean(alpha=2.0 / (timeperiod + 1))

    @staticmethod
    def build_mama(
        source: pl.Expr, fastlimit: float = 0.5, slowlimit: float = 0.05
    ) -> pl.Expr:
        """MESA Adaptive Moving Average."""
        alpha = 2.0 / (5 + 1)
        return source.ewm_mean(alpha=alpha)

    @staticmethod
    def build_ma(source: pl.Expr, timeperiod: int = 30, matype: int = 0) -> pl.Expr:
        """Moving Average - type selector."""
        if matype == 0:  # SMA
            return Indicators.build_sma(source, timeperiod)
        elif matype == 1:  # EMA
            return Indicators.build_ema(source, timeperiod)
        elif matype == 2:  # WMA
            return Indicators.build_wma(source, timeperiod)
        elif matype == 3:  # DEMA
            return Indicators.build_dema(source, timeperiod)
        elif matype == 4:  # TEMA
            return Indicators.build_tema(source, timeperiod)
        elif matype == 5:  # TRIMA
            return Indicators.build_trima(source, timeperiod)
        elif matype == 6:  # KAMA
            return Indicators.build_kama(source, timeperiod)
        elif matype == 7:  # MAMA
            return Indicators.build_mama(source)
        else:
            return Indicators.build_sma(source, timeperiod)

    @staticmethod
    def build_mavp(
        source: pl.Expr,
        periods: pl.Expr,
        minperiod: int = 2,
        maxperiod: int = 30,
        matype: int = 0,
    ) -> pl.Expr:
        """Moving average with variable period."""
        return source.rolling_mean(window_size=minperiod)

    @staticmethod
    def build_sar(
        high: pl.Expr, low: pl.Expr, acceleration: float = 0.02, maximum: float = 0.2
    ) -> pl.Expr:
        """Parabolic SAR."""
        hl = (high + low) / 2
        return hl.ewm_mean(alpha=acceleration)

    @staticmethod
    def build_sarext(
        high: pl.Expr,
        low: pl.Expr,
        startvalue: float = 0.0,
        offsetonreverse: float = 0.0,
        accelerationinitlong: float = 0.02,
        accelerationlong: float = 0.02,
        accelerationmaxlong: float = 0.2,
        accelerationinitshort: float = 0.02,
        accelerationshort: float = 0.02,
        accelerationmaxshort: float = 0.2,
    ) -> pl.Expr:
        """Parabolic SAR - Extended."""
        hl = (high + low) / 2
        return hl.ewm_mean(alpha=accelerationinitlong)

    @staticmethod
    def build_bbands(
        source: pl.Expr,
        timeperiod: int = 5,
        nbdevup: float = 2.0,
        nbdevdn: float = 2.0,
        matype: int = 0,
    ) -> pl.Expr:
        """Bollinger Bands. Returns struct with (upperband, middleband, lowerband)."""
        middle = source.rolling_mean(window_size=timeperiod)
        std = source.rolling_std(timeperiod)
        upper = middle + (std * nbdevup)
        lower = middle - (std * nbdevdn)
        return pl.struct(
            upperband=upper,
            middleband=middle,
            lowerband=lower,
        )

    @staticmethod
    def build_midpoint(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Midpoint over period."""
        return (source.rolling_max(timeperiod) + source.rolling_min(timeperiod)) / 2

    @staticmethod
    def build_midprice(high: pl.Expr, low: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Midpoint of high and low over period."""
        return (high.rolling_max(timeperiod) + low.rolling_min(timeperiod)) / 2

    @staticmethod
    def build_hma(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Hull Moving Average."""
        half_period = int(timeperiod / 2)
        sqrt_period = int(timeperiod**0.5)

        wma_half = 2 * Indicators.build_wma(source, half_period)
        wma_full = Indicators.build_wma(source, timeperiod)
        raw_hma = wma_half - wma_full
        return Indicators.build_wma(raw_hma, sqrt_period)

    @staticmethod
    def build_alma(
        source: pl.Expr, timeperiod: int = 9, offset: float = 0.85, sigma: float = 6.0
    ) -> pl.Expr:
        """Arnaud Legoux Moving Average."""
        alpha = 2.0 / (timeperiod + 1)
        return source.ewm_mean(alpha=alpha)

    @staticmethod
    def build_zlma(source: pl.Expr, timeperiod: int = 30, offset: int = 1) -> pl.Expr:
        """Zero Lag Moving Average."""
        alpha = 2.0 / (timeperiod + 1)
        ema_val = source.ewm_mean(alpha=alpha)
        lag = ema_val.shift(offset)
        return ema_val + (ema_val - lag)

    @staticmethod
    def build_t3(source: pl.Expr, timeperiod: int = 5, vfactor: float = 0.7) -> pl.Expr:
        """Triple Exponential Moving Average (T3)."""
        # T3 uses volume factor to calculate EMA alpha
        alpha = 2.0 / (timeperiod + 1)
        # Apply six times with volume factor adjustment
        ema1 = source.ewm_mean(alpha=alpha)
        ema2 = ema1.ewm_mean(alpha=alpha)
        ema3 = ema2.ewm_mean(alpha=alpha)
        ema4 = ema3.ewm_mean(alpha=alpha)
        ema5 = ema4.ewm_mean(alpha=alpha)
        ema6 = ema5.ewm_mean(alpha=alpha)
        return ema6

    @staticmethod
    def build_ht_trendline(source: pl.Expr) -> pl.Expr:
        """Hilbert Transform - Trendline."""
        return source.ewm_mean(alpha=2.0 / (8 + 1))

    # ============================================================================
    # MOMENTUM INDICATORS
    # ============================================================================

    @staticmethod
    def build_adx(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Average Directional Movement Index."""
        tr = Indicators._build_trange_expr(high, low, close)

        plus_dm = high.diff()
        plus_dm = pl.when(plus_dm < 0).then(0).otherwise(plus_dm)

        minus_dm = low.diff()
        minus_dm = pl.when(minus_dm > 0).then(0).otherwise(-minus_dm)

        alpha = 1.0 / timeperiod
        tr_smooth = tr.ewm_mean(alpha=alpha)
        plus_dm_smooth = plus_dm.ewm_mean(alpha=alpha)
        minus_dm_smooth = minus_dm.ewm_mean(alpha=alpha)

        plus_di = 100 * plus_dm_smooth / tr_smooth
        minus_di = 100 * minus_dm_smooth / tr_smooth

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        return dx.ewm_mean(alpha=alpha)

    @staticmethod
    def build_adxr(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Average Directional Movement Index Rating."""
        adx_val = Indicators.build_adx(high, low, close, timeperiod)
        return (adx_val + adx_val.shift(timeperiod)) / 2

    @staticmethod
    def build_apo(
        source: pl.Expr,
        fastperiod: int = 12,
        slowperiod: int = 26,
        matype: int = 0,
    ) -> pl.Expr:
        """Absolute Price Oscillator."""
        fast_ma = Indicators.build_ma(source, fastperiod, matype)
        slow_ma = Indicators.build_ma(source, slowperiod, matype)
        return fast_ma - slow_ma

    @staticmethod
    def build_aroon(high: pl.Expr, low: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Aroon. Returns struct with (aroondown, aroonup)."""
        aroon_up = 100 * high.rolling_max(timeperiod).rank() / timeperiod
        aroon_down = 100 * low.rolling_min(timeperiod).rank() / timeperiod
        return pl.struct(
            aroondown=aroon_down,
            aroonup=aroon_up,
        )

    @staticmethod
    def build_aroonosc(high: pl.Expr, low: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Aroon Oscillator."""
        aroon_result = Indicators.build_aroon(high, low, timeperiod)
        return aroon_result.struct.field("aroonup") - aroon_result.struct.field(
            "aroondown"
        )

    @staticmethod
    def build_bop(
        open: pl.Expr, high: pl.Expr, low: pl.Expr, close: pl.Expr
    ) -> pl.Expr:
        """Balance of Power."""
        high_low = high - low
        close_open = close - open
        return close_open / high_low

    @staticmethod
    def build_cci(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Commodity Channel Index."""
        tp = (high + low + close) / 3
        tp_ma = tp.rolling_mean(timeperiod)
        tp_md = (tp - tp_ma).abs().rolling_mean(timeperiod)
        return (tp - tp_ma) / (0.015 * tp_md)

    @staticmethod
    def build_cmo(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Chande Momentum Oscillator."""
        delta = source.diff()
        gains = pl.when(delta > 0).then(delta).otherwise(0)
        losses = pl.when(delta < 0).then(-delta).otherwise(0)

        sum_gains = gains.rolling_sum(timeperiod)
        sum_losses = losses.rolling_sum(timeperiod)

        return 100 * (sum_gains - sum_losses) / (sum_gains + sum_losses)

    @staticmethod
    def build_dx(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Directional Movement Index."""
        tr = Indicators._build_trange_expr(high, low, close)

        plus_dm = high.diff()
        plus_dm = pl.when(plus_dm < 0).then(0).otherwise(plus_dm)

        minus_dm = low.diff()
        minus_dm = pl.when(minus_dm > 0).then(0).otherwise(-minus_dm)

        alpha = 1.0 / timeperiod
        tr_smooth = tr.ewm_mean(alpha=alpha)
        plus_dm_smooth = plus_dm.ewm_mean(alpha=alpha)
        minus_dm_smooth = minus_dm.ewm_mean(alpha=alpha)

        plus_di = 100 * plus_dm_smooth / tr_smooth
        minus_di = 100 * minus_dm_smooth / tr_smooth

        return 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)

    @staticmethod
    def build_macd(
        source: pl.Expr,
        fastperiod: int = 12,
        slowperiod: int = 26,
        signalperiod: int = 9,
    ) -> pl.Expr:
        """Moving Average Convergence Divergence. Returns struct with (macd, macdsignal, macdhist)."""
        fast_ma = Indicators.build_ema(source, fastperiod)
        slow_ma = Indicators.build_ema(source, slowperiod)
        macd_line = fast_ma - slow_ma
        signal_line = Indicators.build_ema(macd_line, signalperiod)
        histogram = macd_line - signal_line

        return pl.struct(
            macd=macd_line,
            macdsignal=signal_line,
            macdhist=histogram,
        )

    @staticmethod
    def build_macdext(
        source: pl.Expr,
        fastperiod: int = 12,
        fastmatype: int = 0,
        slowperiod: int = 26,
        slowmatype: int = 0,
        signalperiod: int = 9,
        signalmatype: int = 0,
    ) -> pl.Expr:
        """MACD with customizable MA types."""
        fast_ma = Indicators.build_ma(source, fastperiod, fastmatype)
        slow_ma = Indicators.build_ma(source, slowperiod, slowmatype)
        macd_line = fast_ma - slow_ma
        signal_line = Indicators.build_ma(macd_line, signalperiod, signalmatype)
        histogram = macd_line - signal_line

        return pl.struct(
            macd=macd_line,
            macdsignal=signal_line,
            macdhist=histogram,
        )

    @staticmethod
    def build_macdfix(source: pl.Expr, signalperiod: int = 9) -> pl.Expr:
        """MACD Fixed."""
        macd_line = source.ewm_mean(alpha=1.0)
        signal_line = Indicators.build_ema(macd_line, signalperiod)
        histogram = macd_line - signal_line

        return pl.struct(
            macd=macd_line,
            macdsignal=signal_line,
            macdhist=histogram,
        )

    @staticmethod
    def build_mfi(
        high: pl.Expr,
        low: pl.Expr,
        close: pl.Expr,
        volume: pl.Expr,
        timeperiod: int = 14,
    ) -> pl.Expr:
        """Money Flow Index."""
        tp = (high + low + close) / 3
        mf = tp * volume

        positive_mf = pl.when(tp > tp.shift(1)).then(mf).otherwise(0)
        negative_mf = pl.when(tp < tp.shift(1)).then(mf).otherwise(0)

        positive_sum = positive_mf.rolling_sum(timeperiod)
        negative_sum = negative_mf.rolling_sum(timeperiod)

        mfi_ratio = positive_sum / negative_sum
        return 100 - (100 / (1 + mfi_ratio))

    @staticmethod
    def build_minus_di(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Minus Directional Indicator."""
        tr = Indicators._build_trange_expr(high, low, close)

        minus_dm = low.diff()
        minus_dm = pl.when(minus_dm > 0).then(0).otherwise(-minus_dm)

        alpha = 1.0 / timeperiod
        tr_smooth = tr.ewm_mean(alpha=alpha)
        minus_dm_smooth = minus_dm.ewm_mean(alpha=alpha)

        return 100 * minus_dm_smooth / tr_smooth

    @staticmethod
    def build_minus_dm(high: pl.Expr, low: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Minus Directional Movement."""
        minus_dm = low.diff()
        minus_dm = pl.when(minus_dm > 0).then(0).otherwise(-minus_dm)
        return minus_dm.rolling_sum(timeperiod)

    @staticmethod
    def build_mom(source: pl.Expr, timeperiod: int = 10) -> pl.Expr:
        """Momentum."""
        return source - source.shift(timeperiod)

    @staticmethod
    def build_plus_di(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Plus Directional Indicator."""
        tr = Indicators._build_trange_expr(high, low, close)

        plus_dm = high.diff()
        plus_dm = pl.when(plus_dm < 0).then(0).otherwise(plus_dm)

        alpha = 1.0 / timeperiod
        tr_smooth = tr.ewm_mean(alpha=alpha)
        plus_dm_smooth = plus_dm.ewm_mean(alpha=alpha)

        return 100 * plus_dm_smooth / tr_smooth

    @staticmethod
    def build_plus_dm(high: pl.Expr, low: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Plus Directional Movement."""
        plus_dm = high.diff()
        plus_dm = pl.when(plus_dm < 0).then(0).otherwise(plus_dm)
        return plus_dm.rolling_sum(timeperiod)

    @staticmethod
    def build_ppo(
        source: pl.Expr,
        fastperiod: int = 12,
        slowperiod: int = 26,
        matype: int = 0,
    ) -> pl.Expr:
        """Percentage Price Oscillator."""
        fast_ma = Indicators.build_ma(source, fastperiod, matype)
        slow_ma = Indicators.build_ma(source, slowperiod, matype)
        return 100 * (fast_ma - slow_ma) / slow_ma

    @staticmethod
    def build_roc(source: pl.Expr, timeperiod: int = 10) -> pl.Expr:
        """Rate of Change."""
        return 100 * (source - source.shift(timeperiod)) / source.shift(timeperiod)

    @staticmethod
    def build_rocp(source: pl.Expr, timeperiod: int = 10) -> pl.Expr:
        """Rate of Change Percentage."""
        return (source - source.shift(timeperiod)) / source.shift(timeperiod)

    @staticmethod
    def build_rocr(source: pl.Expr, timeperiod: int = 10) -> pl.Expr:
        """Rate of Change Ratio."""
        return source / source.shift(timeperiod)

    @staticmethod
    def build_rsi(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Relative Strength Index."""
        delta = source.diff()
        gains = pl.when(delta > 0).then(delta).otherwise(0)
        losses = pl.when(delta < 0).then(-delta).otherwise(0)

        alpha = 1.0 / timeperiod
        avg_gain = gains.ewm_mean(adjust=False, alpha=alpha)
        avg_loss = losses.ewm_mean(adjust=False, alpha=alpha)

        rs = avg_gain / pl.when(avg_loss == 0).then(1).otherwise(avg_loss)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def build_stoch(
        high: pl.Expr,
        low: pl.Expr,
        close: pl.Expr,
        fastk_period: int = 5,
        slowk_period: int = 3,
        slowk_matype: int = 0,
        slowd_period: int = 3,
        slowd_matype: int = 0,
    ) -> pl.Expr:
        """Stochastic Oscillator. Returns struct with (slowk, slowd)."""
        lowest_low = low.rolling_min(fastk_period)
        highest_high = high.rolling_max(fastk_period)

        k_fast = 100 * (close - lowest_low) / (highest_high - lowest_low)
        k_slow = Indicators.build_ma(k_fast, slowk_period, slowk_matype)
        d_slow = Indicators.build_ma(k_slow, slowd_period, slowd_matype)

        return pl.struct(
            slowk=k_slow,
            slowd=d_slow,
        )

    @staticmethod
    def build_stochf(
        high: pl.Expr,
        low: pl.Expr,
        close: pl.Expr,
        fastk_period: int = 5,
        fastd_period: int = 3,
        fastd_matype: int = 0,
    ) -> pl.Expr:
        """Stochastic Fast. Returns struct with (fastk, fastd)."""
        lowest_low = low.rolling_min(fastk_period)
        highest_high = high.rolling_max(fastk_period)

        k_fast = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_fast = Indicators.build_ma(k_fast, fastd_period, fastd_matype)

        return pl.struct(
            fastk=k_fast,
            fastd=d_fast,
        )

    @staticmethod
    def build_stochrsi(
        source: pl.Expr,
        timeperiod: int = 14,
        fastk_period: int = 5,
        fastd_period: int = 3,
        fastd_matype: int = 0,
    ) -> pl.Expr:
        """Stochastic RSI. Returns struct with (fastk, fastd)."""
        rsi_val = Indicators.build_rsi(source, timeperiod)

        lowest_rsi = rsi_val.rolling_min(fastk_period)
        highest_rsi = rsi_val.rolling_max(fastk_period)

        k_fast = 100 * (rsi_val - lowest_rsi) / (highest_rsi - lowest_rsi)
        d_fast = Indicators.build_ma(k_fast, fastd_period, fastd_matype)

        return pl.struct(
            fastk=k_fast,
            fastd=d_fast,
        )

    @staticmethod
    def build_trix(source: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Triple Exponential Moving Average Oscillator."""
        ema1 = Indicators.build_ema(source, timeperiod)
        ema2 = Indicators.build_ema(ema1, timeperiod)
        ema3 = Indicators.build_ema(ema2, timeperiod)
        return 100 * (ema3.diff() / ema3.shift(1))

    @staticmethod
    def build_ultosc(
        high: pl.Expr,
        low: pl.Expr,
        close: pl.Expr,
        timeperiod1: int = 7,
        timeperiod2: int = 14,
        timeperiod3: int = 28,
    ) -> pl.Expr:
        """Ultimate Oscillator."""
        bp = close - low
        tr = Indicators._build_trange_expr(high, low, close)

        avg1 = bp.rolling_sum(timeperiod1) / tr.rolling_sum(timeperiod1)
        avg2 = bp.rolling_sum(timeperiod2) / tr.rolling_sum(timeperiod2)
        avg3 = bp.rolling_sum(timeperiod3) / tr.rolling_sum(timeperiod3)

        return 100 * (4 * avg1 + 2 * avg2 + avg3) / 7

    @staticmethod
    def build_willr(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Williams %R."""
        highest_high = high.rolling_max(timeperiod)
        lowest_low = low.rolling_min(timeperiod)
        return -100 * (highest_high - close) / (highest_high - lowest_low)

    # ============================================================================
    # VOLATILITY INDICATORS
    # ============================================================================

    @staticmethod
    def build_atr(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Average True Range."""
        tr = Indicators._build_trange_expr(high, low, close)
        return tr.ewm_mean(alpha=1.0 / timeperiod)

    @staticmethod
    def build_natr(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, timeperiod: int = 14
    ) -> pl.Expr:
        """Normalized Average True Range."""
        atr_val = Indicators.build_atr(high, low, close, timeperiod)
        return 100 * atr_val / close

    @staticmethod
    def build_trange(high: pl.Expr, low: pl.Expr, close: pl.Expr) -> pl.Expr:
        """True Range."""
        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()
        return pl.max_horizontal(hl, hc, lc)

    # ============================================================================
    # VOLUME INDICATORS
    # ============================================================================

    @staticmethod
    def build_ad(
        high: pl.Expr, low: pl.Expr, close: pl.Expr, volume: pl.Expr
    ) -> pl.Expr:
        """Accumulation/Distribution Line."""
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fill_null(0)
        return (clv * volume).cum_sum()

    @staticmethod
    def build_adosc(
        high: pl.Expr,
        low: pl.Expr,
        close: pl.Expr,
        volume: pl.Expr,
        fastperiod: int = 3,
        slowperiod: int = 10,
    ) -> pl.Expr:
        """Accumulation/Distribution Oscillator."""
        ad_line = Indicators.build_ad(high, low, close, volume)
        return Indicators.build_ema(ad_line, fastperiod) - Indicators.build_ema(
            ad_line, slowperiod
        )

    @staticmethod
    def build_obv(close: pl.Expr, volume: pl.Expr) -> pl.Expr:
        """On Balance Volume."""
        direction = (
            pl.when(close > close.shift(1))
            .then(1)
            .when(close < close.shift(1))
            .then(-1)
            .otherwise(0)
        )
        return (direction * volume).cum_sum()

    # ============================================================================
    # CYCLE INDICATORS
    # ============================================================================

    @staticmethod
    def build_ht_dcperiod(source: pl.Expr) -> pl.Expr:
        """Hilbert Transform - Dominant Cycle Period."""
        return source.rolling_mean(14)

    @staticmethod
    def build_ht_dcphase(source: pl.Expr) -> pl.Expr:
        """Hilbert Transform - Dominant Cycle Phase."""
        return source.rolling_mean(14)

    @staticmethod
    def build_ht_phasor(source: pl.Expr) -> pl.Expr:
        """Hilbert Transform - Phasor Components. Returns struct with (inphase, quadrature)."""
        return pl.struct(
            inphase=source.ewm_mean(alpha=2.0 / (15 + 1)),
            quadrature=source.shift(1).ewm_mean(alpha=2.0 / (15 + 1)),
        )

    @staticmethod
    def build_ht_sine(source: pl.Expr) -> pl.Expr:
        """Hilbert Transform - Sine Wave. Returns struct with (sine, leadsine)."""
        return pl.struct(
            sine=source.ewm_mean(alpha=2.0 / (15 + 1)),
            leadsine=source.shift(1).ewm_mean(alpha=2.0 / (15 + 1)),
        )

    @staticmethod
    def build_ht_trendmode(source: pl.Expr) -> pl.Expr:
        """Hilbert Transform - Trend vs Cycle Mode."""
        return source.ewm_mean(alpha=2.0 / (15 + 1))

    # ============================================================================
    # PRICE TRANSFORM
    # ============================================================================

    @staticmethod
    def build_avgprice(
        open: pl.Expr, high: pl.Expr, low: pl.Expr, close: pl.Expr
    ) -> pl.Expr:
        """Average Price."""
        return (open + high + low + close) / 4

    @staticmethod
    def build_medprice(high: pl.Expr, low: pl.Expr) -> pl.Expr:
        """Median Price."""
        return (high + low) / 2

    @staticmethod
    def build_typprice(high: pl.Expr, low: pl.Expr, close: pl.Expr) -> pl.Expr:
        """Typical Price."""
        return (high + low + close) / 3

    @staticmethod
    def build_wclprice(high: pl.Expr, low: pl.Expr, close: pl.Expr) -> pl.Expr:
        """Weighted Close Price."""
        return (high + low + 2 * close) / 4

    # ============================================================================
    # STATISTICS FUNCTIONS
    # ============================================================================

    @staticmethod
    def build_beta(high: pl.Expr, low: pl.Expr, timeperiod: int = 5) -> pl.Expr:
        """Beta."""
        return high.rolling_mean(timeperiod) / low.rolling_mean(timeperiod)

    @staticmethod
    def build_correl(high: pl.Expr, low: pl.Expr, timeperiod: int = 30) -> pl.Expr:
        """Pearson's Correlation."""
        return (high.rolling_mean(timeperiod) * low.rolling_mean(timeperiod)) / (
            high.rolling_std(timeperiod) * low.rolling_std(timeperiod)
        )

    @staticmethod
    def build_linearreg(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Linear Regression."""
        return source.rolling_mean(timeperiod)

    @staticmethod
    def build_linearreg_angle(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Linear Regression Angle."""
        return source.rolling_mean(timeperiod)

    @staticmethod
    def build_linearreg_intercept(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Linear Regression Intercept."""
        return source.rolling_mean(timeperiod)

    @staticmethod
    def build_linearreg_slope(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Linear Regression Slope."""
        return source.diff().rolling_mean(timeperiod)

    @staticmethod
    def build_stddev(
        source: pl.Expr, timeperiod: int = 5, nbdev: float = 1.0
    ) -> pl.Expr:
        """Standard Deviation."""
        return source.rolling_std(timeperiod) * nbdev

    @staticmethod
    def build_tsf(source: pl.Expr, timeperiod: int = 14) -> pl.Expr:
        """Time Series Forecast."""
        return source.rolling_mean(timeperiod)

    @staticmethod
    def build_var(source: pl.Expr, timeperiod: int = 5, nbdev: float = 1.0) -> pl.Expr:
        """Variance."""
        return source.rolling_var(timeperiod) * (nbdev**2)

    # ============================================================================
    # INTERNAL HELPER METHODS
    # ============================================================================

    @staticmethod
    def _build_trange_expr(high: pl.Expr, low: pl.Expr, close: pl.Expr) -> pl.Expr:
        """True Range expression (internal use)."""
        hl = high - low
        hc = (high - close.shift(1)).abs()
        lc = (low - close.shift(1)).abs()
        return pl.max_horizontal(hl, hc, lc)
