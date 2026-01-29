"""
ProAlgoTrader Indicators - Public API

This module provides all technical analysis indicators for use in your trading strategies.

All indicators follow a unified implementation pattern:
- Consistent parameters (timeperiod, column, output_columns)
- Full type hints for IDE autocomplete
- Comprehensive docstrings with examples
- Pure Polars implementation (no external dependencies)

Quick Start:
-----------

    from proalgotrader_core.indicators import RSI, MACD, BollingerBands, ATR

    # Initialize indicator with default parameters
    rsi = RSI(timeperiod=14)

    # Initialize with custom parameters
    macd = MACD(
        fastperiod=12,
        slowperiod=26,
        signalperiod=9,
        output_columns=["macd", "signal", "histogram"]
    )

    # Use in your strategy
    await rsi.initialize(chart)
    current_rsi = await rsi.last_value()

Indicator Categories:
-------------------

**Momentum Indicators:**
    - RSI: Relative Strength Index
    - MACD: Moving Average Convergence Divergence
    - STOCH: Stochastic Oscillator
    - WILLR: Williams %R
    - CCI: Commodity Channel Index
    - STOCHRSI: Stochastic RSI
    - TRIX: Triple Exponential Moving Average
    - ULTOSC: Ultimate Oscillator

**Overlap Studies (Moving Averages):**
    - SMA: Simple Moving Average
    - EMA: Exponential Moving Average
    - WMA: Weighted Moving Average
    - DEMA: Double Exponential Moving Average
    - TEMA: Triple Exponential Moving Average
    - KAMA: Kaufman Adaptive Moving Average
    - HMA: Hull Moving Average
    - BBANDS: Bollinger Bands
    - SAR: Parabolic SAR

**Volatility Indicators:**
    - ATR: Average True Range
    - NATR: Normalized Average True Range
    - KC: Keltner Channels
    - DONCHIAN: Donchian Channels

**Volume Indicators:**
    - AD: Accumulation/Distribution
    - OBV: On Balance Volume
    - MFI: Money Flow Index
    - VWAP: Volume Weighted Average Price
    - CMF: Chaikin Money Flow

**Trend Indicators:**
    - ADX: Average Directional Movement Index
    - AROON: Aroon Indicator
    - VORTEX: Vortex Indicator
    - HT_TRENDMODE: Hilbert Trend Mode

**Cycle Indicators:**
    - HT_DCPERIOD: Hilbert Dominant Cycle Period
    - HT_DCPHASE: Hilbert Dominant Cycle Phase

**Price Transform:**
    - AVGPRICE: Average Price
    - MEDPRICE: Median Price
    - TYPPRICE: Typical Price
    - WCLPRICE: Weighted Close Price

**Statistics:**
    - BETA: Beta
    - CORREL: Pearson's Correlation
    - STDDEV: Standard Deviation
    - TSF: Time Series Forecast

Usage Examples:
--------------

Example 1: Single Indicator with Default Parameters

    >>> from proalgotrader_core.indicators import RSI
    >>>
    >>> # Create indicator - uses default timeperiod=14, column="close"
    >>> rsi_indicator = RSI()
    >>>
    >>> # Initialize with chart data
    >>> await rsi_indicator.initialize(chart)
    >>>
    >>> # Get current value
    >>> current_value = await rsi_indicator.last_value()
    >>> print(f"RSI: {current_value}")
    RSI: 65.43

Example 2: Custom Parameters

    >>> from proalgotrader_core.indicators import EMA
    >>>
    >>> # Custom period and column
    >>> ema = EMA(timeperiod=20, column="close")
    >>>
    >>> # Custom output column name
    >>> ema = EMA(
    ...     timeperiod=20,
    ...     column="close",
    ...     output_columns=["fast_ema"]
    ... )

Example 3: Multi-Output Indicator

    >>> from proalgotrader_core.indicators import MACD, BollingerBands
    >>>
    >>> # MACD returns 3 outputs: macd, signal, hist
    >>> macd = MACD(
    ...     fastperiod=12,
    ...     slowperiod=26,
    ...     signalperiod=9,
    ...     output_columns=["macd_line", "signal_line", "histogram"]
    ... )
    >>>
    >>> await macd.initialize(chart)
    >>>
    >>> # Access specific outputs
    >>> macd_value = await macd.last_value("macd_line")
    >>> signal_value = await macd.last_value("signal_line")

Example 4: Multiple Input Indicator

    >>> from proalgotrader_core.indicators import ATR, STOCH
    >>>
    >>> # ATR needs high, low, close columns
    >>> atr = ATR(timeperiod=14)
    >>>
    >>> # Stochastic needs high, low, close
    >>> stoch = STOCH(
    ...     fastk_period=14,
    ...     output_columns=["slowk", "slowd"]
    ... )

Example 5: Multiple Indicators in Strategy

    >>> from proalgotrader_core.indicators import (
    ...     RSI, EMA, MACD, ATR, BollingerBands
    ... )
    >>>
    >>> class MyStrategy:
    ...     async def initialize(self, chart):
    ...         # Initialize all indicators
    ...         self.rsi = RSI(timeperiod=14)
    ...         self.ema_fast = EMA(timeperiod=9)
    ...         self.ema_slow = EMA(timeperiod=21)
    ...         self.macd = MACD()
    ...         self.atr = ATR(timeperiod=14)
    ...         self.bbands = BollingerBands(period=20, std_dev=2.0)
    ...
    ...         # Initialize all
    ...         for indicator in [self.rsi, self.ema_fast, self.ema_slow,
    ...                            self.macd, self.atr, self.bbands]:
    ...             await indicator.initialize(chart)
    ...
    ...     async def next(self):
    ...         # Get current values
    ...         rsi_val = await self.rsi.last_value()
    ...         macd_val = await self.macd.last_value("macd")
    ...         atr_val = await self.atr.last_value()
    ...
    ...         # Your trading logic here
    ...         if rsi_val > 70:
    ...             # Overbought - consider selling
    ...         elif rsi_val < 30:
    ...             # Oversold - consider buying

Parameter Reference:
------------------

Common Parameters (available on most indicators):

    timeperiod : int, default: 14
        Number of periods for calculation.
        Typical values: 5-50 depending on indicator.

    column : str, default: "close"
        Input column name from chart data.
        Options: "open", "high", "low", "close", "volume"

    output_columns : list[str] | None, optional
        Custom names for output columns.
        - If None: Uses automatic naming (indicator_period_column)
        - If provided: Must match number of outputs exactly

    high_column : str, default: "high"
        High price column (for multi-input indicators)

    low_column : str, default: "low"
        Low price column (for multi-input indicators)

    close_column : str, default: "close"
        Close price column (for multi-input indicators)

    volume_column : str, default: "volume"
        Volume column (for volume indicators)

Output Methods:
--------------

After calling `await indicator.initialize(chart)`, use these methods:

    # Get all indicator data as DataFrame
    data = indicator.data

    # Get specific column as Series
    series = await indicator.series(column_name)

    # Get latest value
    value = await indicator.last_value()
    value = await indicator.last_value("specific_column")

    # Get row by index
    row_value = await indicator.get_data(row_number=-1)

Auto-Complete:
------------

All indicators have full type hints. Your IDE will show:

    # Parameters autocomplete
    rsi = RSI(
        timeperiod=14,     # int | None = 14
        column="close",    # str = "close"
        output_columns=None # List[str] | None = None
    )

    # Methods autocomplete
    rsi.initialize(chart)       # async method
    rsi.last_value()            # async method -> float | None
    rsi.series()                # async method -> Series | None
    rsi.output_columns()         # -> List[str]
    rsi.required_columns()       # -> List[str]
    rsi.window_size()            # -> int
    rsi.warmup_size()            # -> int

Available Indicators:
--------------------

"""

# Momentum Indicators
from proalgotrader_core.indicators.momentum.rsi import RSI
from proalgotrader_core.indicators.momentum.macd import MACD
from proalgotrader_core.indicators.momentum.macdext import MACDEXT
from proalgotrader_core.indicators.momentum.macdfix import MACDFIX
from proalgotrader_core.indicators.momentum.minus_di import MINUS_DI
from proalgotrader_core.indicators.momentum.minus_dm import MINUS_DM
from proalgotrader_core.indicators.momentum.plus_di import PLUS_DI
from proalgotrader_core.indicators.momentum.plus_dm import PLUS_DM
from proalgotrader_core.indicators.momentum.adx import ADX
from proalgotrader_core.indicators.momentum.adxr import ADXR
from proalgotrader_core.indicators.momentum.apo import APO
from proalgotrader_core.indicators.momentum.dx import DX
from proalgotrader_core.indicators.momentum.stoch import STOCH
from proalgotrader_core.indicators.momentum.stochf import STOCHF
from proalgotrader_core.indicators.momentum.stochrsi import STOCHRSI
from proalgotrader_core.indicators.momentum.cci import CCI
from proalgotrader_core.indicators.momentum.williams_r import WilliamsR
from proalgotrader_core.indicators.momentum.aroon import AROON
from proalgotrader_core.indicators.momentum.mom import MOM
from proalgotrader_core.indicators.momentum.roc import ROC
from proalgotrader_core.indicators.momentum.rocp import ROCP
from proalgotrader_core.indicators.momentum.rocr import ROCR
from proalgotrader_core.indicators.momentum.rocr100 import ROCR100
from proalgotrader_core.indicators.momentum.aroonosc import AROONOSC
from proalgotrader_core.indicators.momentum.bop import BOP
from proalgotrader_core.indicators.momentum.cmo import CMO
from proalgotrader_core.indicators.momentum.trix import TRIX
from proalgotrader_core.indicators.momentum.ultosc import ULTOSC
from proalgotrader_core.indicators.momentum.ppo import PPO
from proalgotrader_core.indicators.momentum.tsi import TSI
from proalgotrader_core.indicators.momentum.kst import KST
from proalgotrader_core.indicators.momentum.fisher import Fisher
from proalgotrader_core.indicators.momentum.stc import STC
from proalgotrader_core.indicators.momentum.coppock import Coppock
from proalgotrader_core.indicators.momentum.qqe import QQE
from proalgotrader_core.indicators.momentum.inertia import Inertia

# Overlap Studies
from proalgotrader_core.indicators.overlap.sma import SMA
from proalgotrader_core.indicators.overlap.ema import EMA
from proalgotrader_core.indicators.overlap.dema import DEMA
from proalgotrader_core.indicators.overlap.tema import TEMA
from proalgotrader_core.indicators.overlap.wma import WMA
from proalgotrader_core.indicators.overlap.bbands import BBANDS
from proalgotrader_core.indicators.overlap.kama import KAMA
from proalgotrader_core.indicators.overlap.trima import TRIMA
from proalgotrader_core.indicators.overlap.t3 import T3
from proalgotrader_core.indicators.overlap.mama import MAMA
from proalgotrader_core.indicators.overlap.hma import HMA
from proalgotrader_core.indicators.overlap.midpoint import MIDPOINT
from proalgotrader_core.indicators.overlap.midprice import MIDPRICE
from proalgotrader_core.indicators.overlap.sar import SAR
from proalgotrader_core.indicators.overlap.sarext import SAREXT
from proalgotrader_core.indicators.overlap.ht_trendline import HT_TRENDLINE
from proalgotrader_core.indicators.overlap.mavp import MAVP
from proalgotrader_core.indicators.overlap.ma import MA
from proalgotrader_core.indicators.overlap.alma import ALMA
from proalgotrader_core.indicators.overlap.zlma import ZLMA
from proalgotrader_core.indicators.overlap.ichimoku import Ichimoku

# Volatility Indicators
from proalgotrader_core.indicators.volatility.atr import ATR
from proalgotrader_core.indicators.volatility.natr import NATR
from proalgotrader_core.indicators.volatility.trange import TRANGE
from proalgotrader_core.indicators.volatility.squeeze_pro import SqueezePro
from proalgotrader_core.indicators.volatility.kc import KC
from proalgotrader_core.indicators.volatility.donchian import Donchian
from proalgotrader_core.indicators.volatility.accbands import AccBands
from proalgotrader_core.indicators.volatility.massi import MassI
from proalgotrader_core.indicators.volatility.vhf import VHF
from proalgotrader_core.indicators.volatility.choppiness import Choppiness

# Volume Indicators
from proalgotrader_core.indicators.volume.ad import AD
from proalgotrader_core.indicators.volume.adosc import ADOSC
from proalgotrader_core.indicators.volume.obv import OBV
from proalgotrader_core.indicators.volume.mfi import MFI
from proalgotrader_core.indicators.volume.vwap import VWAP
from proalgotrader_core.indicators.volume.cmf import CMF
from proalgotrader_core.indicators.volume.eom import EOM
from proalgotrader_core.indicators.volume.kvo import KVO
from proalgotrader_core.indicators.volume.nvi import NVI
from proalgotrader_core.indicators.volume.pvi import PVI
from proalgotrader_core.indicators.volume.pvt import PVT
from proalgotrader_core.indicators.volume.vwma import VWMA

# Trend Indicators
from proalgotrader_core.indicators.trend.supertrend import Supertrend
from proalgotrader_core.indicators.trend.ht_trendmode import HT_TRENDMODE
from proalgotrader_core.indicators.trend.vortex import Vortex
from proalgotrader_core.indicators.trend.alphatrend import AlphaTrend

# Cycle Indicators
from proalgotrader_core.indicators.cycle.ht_dcperiod import HT_DCPERIOD
from proalgotrader_core.indicators.cycle.ht_dcphase import HT_DCPHASE
from proalgotrader_core.indicators.cycle.ht_phasor import HT_PHASOR
from proalgotrader_core.indicators.cycle.ht_sine import HT_SINE

# Price Transform
from proalgotrader_core.indicators.price_transform.avgprice import AVGPRICE
from proalgotrader_core.indicators.price_transform.medprice import MEDPRICE
from proalgotrader_core.indicators.price_transform.typprice import TYPPRICE
from proalgotrader_core.indicators.price_transform.wclprice import WCLPRICE

# Statistics
from proalgotrader_core.indicators.statistic.beta import BETA
from proalgotrader_core.indicators.statistic.correl import CORREL
from proalgotrader_core.indicators.statistic.linearreg import LINEARREG
from proalgotrader_core.indicators.statistic.linearreg_angle import LINEARREG_ANGLE
from proalgotrader_core.indicators.statistic.linearreg_intercept import (
    LINEARREG_INTERCEPT,
)
from proalgotrader_core.indicators.statistic.linearreg_slope import LINEARREG_SLOPE
from proalgotrader_core.indicators.statistic.stddev import STDDEV
from proalgotrader_core.indicators.statistic.tsf import TSF
from proalgotrader_core.indicators.statistic.var import VAR

# Create convenient aliases for common naming conventions
BollingerBands = BBANDS
Stochastic = STOCH
StochasticRSI = STOCHRSI
MoneyFlowIndex = MFI
Donchian = Donchian
KeltnerChannels = KC

__all__ = [
    # Momentum
    "RSI",
    "MACD",
    "MACDEXT",
    "MACDFIX",
    "MINUS_DI",
    "MINUS_DM",
    "PLUS_DI",
    "PLUS_DM",
    "PPO",
    "ADX",
    "ADXR",
    "APO",
    "DX",
    "STOCH",
    "STOCHF",
    "STOCHRSI",
    "CCI",
    "CMO",
    "WilliamsR",
    "AROON",
    "AROONOSC",
    "BOP",
    "MOM",
    "ROC",
    "ROCP",
    "ROCR",
    "ROCR100",
    "TRIX",
    "ULTOSC",
    "TSI",
    "KST",
    "Fisher",
    "STC",
    "Coppock",
    "QQE",
    "Inertia",
    # Overlap
    "SMA",
    "EMA",
    "DEMA",
    "TEMA",
    "WMA",
    "BBANDS",
    "BollingerBands",
    "KAMA",
    "TRIMA",
    "T3",
    "MAMA",
    "HMA",
    "MIDPOINT",
    "MIDPRICE",
    "SAR",
    "SAREXT",
    "HT_TRENDLINE",
    "MAVP",
    "MA",
    "ALMA",
    "ZLMA",
    "Ichimoku",
    # Volatility
    "ATR",
    "NATR",
    "TRANGE",
    "SqueezePro",
    "KC",
    "KeltnerChannels",
    "Donchian",
    "AccBands",
    "MassI",
    "VHF",
    "Choppiness",
    # Volume
    "AD",
    "ADOSC",
    "OBV",
    "MFI",
    "MoneyFlowIndex",
    "VWAP",
    "CMF",
    "EOM",
    "KVO",
    "NVI",
    "PVI",
    "PVT",
    "VWMA",
    # Trend
    "Supertrend",
    "HT_TRENDMODE",
    "Vortex",
    "AlphaTrend",
    # Cycle
    "HT_DCPERIOD",
    "HT_DCPHASE",
    "HT_PHASOR",
    "HT_SINE",
    # Price Transform
    "AVGPRICE",
    "MEDPRICE",
    "TYPPRICE",
    "WCLPRICE",
    # Statistics
    "BETA",
    "CORREL",
    "LINEARREG",
    "LINEARREG_ANGLE",
    "LINEARREG_INTERCEPT",
    "LINEARREG_SLOPE",
    "STDDEV",
    "TSF",
    "VAR",
    # Aliases
    "Stochastic",
    "StochasticRSI",
]

__version__ = "1.0.0"
__author__ = "ProAlgoTrader"
