"""
Calculs manuels des indicateurs techniques (pas de librairie externe)
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
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
    """
    Stochastic Oscillator %K and %D.
    Retourne (%K, %D)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    stoch_k_smooth = stoch_k.rolling(window=smooth).mean()
    stoch_d = stoch_k_smooth.rolling(window=d_period).mean()
    return stoch_k_smooth, stoch_d

def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Average Directional Index.
    Retourne (ADX, +DI, -DI)
    """
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

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=period).mean()
    return adx, plus_di, minus_di

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Retourne MACD line, Signal line, Histogram"""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def bollinger_bands(close: pd.Series, period: int = 20, std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Retourne upper, middle (SMA), lower"""
    sma = close.rolling(window=period).mean()
    rolling_std = close.rolling(window=period).std()
    upper = sma + (rolling_std * std)
    lower = sma - (rolling_std * std)
    return upper, sma, lower

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def support_resistance(high: pd.Series, low: pd.Series, lookback: int = 50) -> Tuple[float, float]:
    """Retourne (support, resistance) sur les lookback dernières périodes"""
    if len(high) < lookback:
        return None, None
    recent_high = high.iloc[-lookback:]
    recent_low = low.iloc[-lookback:]
    resistance = recent_high.max()
    support = recent_low.min()
    return support, resistance

def detect_divergence(close: pd.Series, rsi_series: pd.Series, lookback: int = 5) -> Optional[str]:
    if len(close) < lookback + 1 or len(rsi_series) < lookback + 1:
        return None
    price_segment = close.iloc[-lookback-1:]
    rsi_segment = rsi_series.iloc[-lookback-1:]

    price_min_pos = price_segment.argmin()
    price_max_pos = price_segment.argmax()
    rsi_min_pos = rsi_segment.argmin()
    rsi_max_pos = rsi_segment.argmax()

    # Bullish: prix fait un plus bas récent, RSI fait un plus haut
    if price_min_pos == len(price_segment) - 1 and rsi_min_pos != price_min_pos:
        if rsi_segment.iloc[-1] > rsi_segment.iloc[rsi_min_pos]:
            return "bullish"
    # Bearish: prix fait un plus haut récent, RSI fait un plus bas
    if price_max_pos == len(price_segment) - 1 and rsi_max_pos != price_max_pos:
        if rsi_segment.iloc[-1] < rsi_segment.iloc[rsi_max_pos]:
            return "bearish"
    return None

def fibonacci_levels(high: float, low: float) -> dict:
    """Calcule les niveaux de retracement Fibonacci."""
    diff = high - low
    return {
        "0.382": round(high - diff * 0.382, 5),
        "0.500": round(high - diff * 0.500, 5),
        "0.618": round(high - diff * 0.618, 5)
    }