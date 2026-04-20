"""
Calculs manuels des indicateurs techniques.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
               k_period: int = 14, d_period: int = 3, smooth: int = 3) -> Tuple[pd.Series, pd.Series]:
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    stoch_k_smooth = stoch_k.rolling(window=smooth).mean()
    stoch_d = stoch_k_smooth.rolling(window=d_period).mean()
    return stoch_k_smooth, stoch_d

def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    if len(high) < period + 1:
        zeros = pd.Series([0.0] * len(high), index=high.index)
        return zeros, zeros, zeros

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    up_move = high - high.shift()
    down_move = low.shift() - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr)

    plus_di = plus_di.fillna(0)
    minus_di = minus_di.fillna(0)

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    dx = dx.replace([np.inf, -np.inf], 0).fillna(0)

    adx = dx.rolling(window=period).mean().fillna(0)
    return adx, plus_di, minus_di

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def bollinger_bands(close: pd.Series, period: int = 20, std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = close.rolling(window=period).mean()
    rolling_std = close.rolling(window=period).std()
    upper = sma + (rolling_std * std)
    lower = sma - (rolling_std * std)
    return upper, sma, lower

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def support_resistance(high: pd.Series, low: pd.Series, lookback: int = 50) -> Tuple[Optional[float], Optional[float]]:
    if len(high) < lookback:
        return None, None
    recent_high = high.iloc[-lookback:]
    recent_low = low.iloc[-lookback:]
    resistance = recent_high.max()
    support = recent_low.min()
    return support, resistance

def detect_divergence(close: pd.Series, rsi_series: pd.Series, lookback: int = 5) -> Optional[str]:
    if len(close) < lookback + 2 or len(rsi_series) < lookback + 2:
        return None
    
    # Recherche des plus bas récents
    price_segment = close.iloc[-lookback-2:]
    rsi_segment = rsi_series.iloc[-lookback-2:]
    
    price_min_idx = price_segment.idxmin()
    rsi_min_idx = rsi_segment.idxmin()
    
    # Divergence haussière : prix fait un nouveau plus bas, RSI non
    if price_segment.iloc[-1] <= price_segment.min() and rsi_segment.iloc[-1] > rsi_segment.min():
        return "bullish"
    # Divergence baissière : prix fait un nouveau plus haut, RSI non
    if price_segment.iloc[-1] >= price_segment.max() and rsi_segment.iloc[-1] < rsi_segment.max():
        return "bearish"
    return None

def fibonacci_levels(high: float, low: float) -> dict:
    if high <= low:
        return {"0.382": low, "0.500": low, "0.618": low}
    diff = high - low
    return {
        "0.382": round(high - diff * 0.382, 5),
        "0.500": round(high - diff * 0.500, 5),
        "0.618": round(high - diff * 0.618, 5)
    }