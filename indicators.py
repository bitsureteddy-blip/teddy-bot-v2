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
    """
    Détecte une divergence haussière ou baissière sur les N dernières périodes.
    Bullish: prix fait plus bas, RSI fait plus haut.
    Bearish: prix fait plus haut, RSI fait plus bas.
    Retourne "bullish", "bearish" ou None.
    """
    if len(close) < lookback + 1 or len(rsi_series) < lookback + 1:
        return None
    # Prendre les derniers points
    price_segment = close.iloc[-lookback-1:]
    rsi_segment = rsi_series.iloc[-lookback-1:]

    price_min_idx = price_segment.idxmin()
    price_max_idx = price_segment.idxmax()
    rsi_min_idx = rsi_segment.idxmin()
    rsi_max_idx = rsi_segment.idxmax()

    # Bullish: prix fait un plus bas récent, RSI fait un plus haut
    if price_min_idx == price_segment.index[-1] and rsi_min_idx != price_min_idx:
        # Vérifier que RSI est plus haut que précédent bas
        if rsi_segment.iloc[-1] > rsi_segment.iloc[rsi_min_idx]:
            return "bullish"
    # Bearish: prix fait un plus haut récent, RSI fait un plus bas
    if price_max_idx == price_segment.index[-1] and rsi_max_idx != price_max_idx:
        if rsi_segment.iloc[-1] < rsi_segment.iloc[rsi_max_idx]:
            return "bearish"
    return None