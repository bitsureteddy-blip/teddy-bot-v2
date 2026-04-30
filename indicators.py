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

def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Lissage de Wilder : EMA avec alpha = 1/period."""
    return series.ewm(alpha=1/period, adjust=False).mean()

def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calcule l'ADX avec le lissage de Wilder."""
    if len(high) < period + 1:
        zeros = pd.Series([0.0] * len(high), index=high.index)
        return zeros, zeros, zeros

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Mouvements directionnels
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)

    # Lissage de Wilder
    atr_smooth = _wilder_smooth(tr, period)
    plus_dm_smooth = _wilder_smooth(plus_dm, period)
    minus_dm_smooth = _wilder_smooth(minus_dm, period)

    # Indicateurs directionnels
    plus_di = 100 * (plus_dm_smooth / atr_smooth)
    minus_di = 100 * (minus_dm_smooth / atr_smooth)

    # Directional Index
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
    dx = dx.replace([np.inf, -np.inf], 0).fillna(0)

    # ADX final (lissage de Wilder du DX)
    adx_series = _wilder_smooth(dx, period)

    return adx_series, plus_di, minus_di

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