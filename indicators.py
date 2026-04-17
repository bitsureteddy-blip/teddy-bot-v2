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
    # Éviter division par zéro
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # Valeur neutre par défaut

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

def support_resistance(high: pd.Series, low: pd.Series, lookback: int = 50) -> Tuple[Optional[float], Optional[float]]:
    """Retourne (support, resistance) sur les lookback dernières périodes"""
    if len(high) < lookback or len(low) < lookback:
        return None, None
    recent_high = high.iloc[-lookback:]
    recent_low = low.iloc[-lookback:]
    resistance = recent_high.max()
    support = recent_low.min()
    return support, resistance

def detect_divergence(close: pd.Series, rsi_series: pd.Series, lookback: int = 5) -> Optional[str]:
    """
    Détecte une divergence haussière ou baissière.
    Retourne 'bullish', 'bearish' ou None.
    """
    if len(close) < lookback + 1 or len(rsi_series) < lookback + 1:
        return None

    price_segment = close.iloc[-lookback-1:].reset_index(drop=True)
    rsi_segment = rsi_series.iloc[-lookback-1:].reset_index(drop=True)

    # Positions des extremums dans le segment
    price_min_idx = price_segment.idxmin()
    price_max_idx = price_segment.idxmax()
    rsi_min_idx = rsi_segment.idxmin()
    rsi_max_idx = rsi_segment.idxmax()

    # Divergence haussière : prix fait un plus bas, RSI fait un plus haut
    if price_min_idx == len(price_segment) - 1:  # le plus bas est à la fin
        if rsi_min_idx != price_min_idx and rsi_segment.iloc[-1] > rsi_segment.iloc[rsi_min_idx]:
            return "bullish"

    # Divergence baissière : prix fait un plus haut, RSI fait un plus bas
    if price_max_idx == len(price_segment) - 1:  # le plus haut est à la fin
        if rsi_max_idx != price_max_idx and rsi_segment.iloc[-1] < rsi_segment.iloc[rsi_max_idx]:
            return "bearish"

    return None