"""
Logique métier : génération des signaux ACHETER/VENDRE/ATTENDRE
et calcul du Teddy Score.
"""
import pandas as pd
from typing import Dict, Optional, Tuple
from indicators import (
    rsi, macd, bollinger_bands, sma, support_resistance, detect_divergence
)
from config import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD, SMA_SHORT, SMA_LONG,
    SUPPORT_RESISTANCE_LOOKBACK, DIVERGENCE_LOOKBACK
)

class SignalEngine:
    @staticmethod
    def analyze(df: pd.DataFrame) -> Dict:
        """
        Retourne un dictionnaire avec:
        - signal: "ACHETER", "VENDRE", "ATTENDRE"
        - reason: explication
        - risk_advice: conseil de risque
        - teddy_score: 0-100
        - indicators: dict des valeurs actuelles
        """
        if df.empty or len(df) < SMA_LONG:
            return {"signal": "ATTENDRE", "reason": "Insufficient data", "risk_advice": "", "teddy_score": 0, "indicators": {}}

        close = df['Close']
        high = df['High']
        low = df['Low']

        # Calcul des indicateurs
        rsi_val = rsi(close, RSI_PERIOD).iloc[-1]
        macd_line, signal_line, hist = macd(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
        macd_val = macd_line.iloc[-1]
        signal_val = signal_line.iloc[-1]
        hist_val = hist.iloc[-1]
        upper_bb, mid_bb, lower_bb = bollinger_bands(close, BB_PERIOD, BB_STD)
        bb_upper = upper_bb.iloc[-1]
        bb_lower = lower_bb.iloc[-1]
        sma20 = sma(close, SMA_SHORT).iloc[-1]
        sma50 = sma(close, SMA_LONG).iloc[-1]
        support, resistance = support_resistance(high, low, SUPPORT_RESISTANCE_LOOKBACK)

        last_price = close.iloc[-1]

        # Divergence
        divergence = detect_divergence(close, rsi(close, RSI_PERIOD), DIVERGENCE_LOOKBACK)

        # Règles dans l'ordre de priorité
        signal = "ATTENDRE"
        reason = ""
        risk_advice = ""

        # 1. Divergence
        if divergence == "bullish":
            signal = "ACHETER"
            reason = "🔥 Bullish divergence"
            risk_advice = "✅ Good entry point"
        elif divergence == "bearish":
            signal = "VENDRE"
            reason = "🔥 Bearish divergence"
            risk_advice = "🔻 Selling pressure, downside risk"

        # 2. RSI extrême + MACD
        elif not pd.isna(rsi_val):
            if rsi_val < 30 and hist_val > 0:
                signal = "ACHETER"
                reason = "RSI oversold + MACD histogram positive"
                risk_advice = "📈 Bounce zone likely"
            elif rsi_val > 70 and hist_val < 0:
                signal = "VENDRE"
                reason = "RSI overbought + MACD histogram negative"
                risk_advice = "🔻 Selling pressure, downside risk"

        # 3. Support / Résistance
        elif support and resistance:
            if last_price <= support * 1.01 and rsi_val < 40:
                signal = "ACHETER"
                reason = "Price near support + RSI < 40"
                risk_advice = "📈 Bounce zone likely"
            elif last_price >= resistance * 0.99 and rsi_val > 60:
                signal = "VENDRE"
                reason = "Price near resistance + RSI > 60"
                risk_advice = "🔻 Selling pressure, downside risk"

        # 4. Croisement MACD (vérifier la veille)
        if signal == "ATTENDRE" and len(macd_line) >= 2:
            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            if prev_macd < prev_signal and macd_val > signal_val:
                signal = "ACHETER"
                reason = "MACD crossed above signal line"
                risk_advice = "✅ Good entry point"
            elif prev_macd > prev_signal and macd_val < signal_val:
                signal = "VENDRE"
                reason = "MACD crossed below signal line"
                risk_advice = "🔻 Selling pressure, downside risk"

        # 5. Pullback dans la tendance
        if signal == "ATTENDRE":
            if last_price > sma20 > sma50 and rsi_val < 50:
                signal = "ACHETER"
                reason = "Uptrend pullback (price > SMA20 > SMA50, RSI < 50)"
                risk_advice = "⚠️ Wait for a pullback before buying"
            elif last_price < sma20 < sma50 and rsi_val > 50:
                signal = "VENDRE"
                reason = "Downtrend pullback (price < SMA20 < SMA50, RSI > 50)"
                risk_advice = "🔻 Selling pressure, downside risk"

        # Sinon
        if signal == "ATTENDRE":
            reason = "📊 No clear signal – wait for better setup"
            risk_advice = ""

        # Calcul du Teddy Score
        teddy_score = SignalEngine._compute_teddy_score(
            close, rsi_val, sma20, sma50, support, resistance, last_price,
            macd_val, signal_val, divergence, df['Volume'].iloc[-1] if 'Volume' in df else 0
        )

        indicators = {
            "price": last_price,
            "rsi": rsi_val,
            "macd": macd_val,
            "macd_signal": signal_val,
            "macd_hist": hist_val,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "sma20": sma20,
            "sma50": sma50,
            "support": support,
            "resistance": resistance
        }

        return {
            "signal": signal,
            "reason": reason,
            "risk_advice": risk_advice,
            "teddy_score": teddy_score,
            "indicators": indicators
        }

    @staticmethod
    def _compute_teddy_score(close, rsi_val, sma20, sma50, support, resistance, price,
                             macd, macd_signal, divergence, volume) -> int:
        score = 50
        if not pd.isna(rsi_val):
            if rsi_val < 30:
                score += 15
            elif rsi_val > 70:
                score -= 15
            elif rsi_val < 50:
                score += 5
            else:
                score -= 5
        if price > sma20:
            score += 10
        else:
            score -= 10
        if sma20 > sma50:
            score += 10
        else:
            score -= 10
        if support and price <= support * 1.02:
            score += 10
        if resistance and price >= resistance * 0.98:
            score -= 10
        if divergence == "bullish":
            score += 20
        elif divergence == "bearish":
            score -= 20
        if macd > macd_signal:
            score += 10
        else:
            score -= 10
        # Volume (si disponible)
        if volume > 0:
            avg_vol = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else volume
            if volume > avg_vol * 1.5:
                score += 5
        return max(0, min(100, score))