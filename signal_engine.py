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
        if df.empty or len(df) < SMA_LONG:
            return {"signal": "ATTENDRE", "reason": "Données insuffisantes", "risk_advice": "", "teddy_score": 0, "indicators": {}}

        close = df['Close']
        high = df['High']
        low = df['Low']

        # Calcul des indicateurs
        rsi_series = rsi(close, RSI_PERIOD)
        rsi_val = rsi_series.iloc[-1]
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
        divergence = detect_divergence(close, rsi_series, DIVERGENCE_LOOKBACK)

        signal = "ATTENDRE"
        reason = ""
        risk_advice = ""

        # 1. Divergence (reste prioritaire)
        if divergence == "bullish":
            signal = "ACHETER"
            reason = "🔥 Divergence haussière"
            risk_advice = "✅ Point d'entrée intéressant"
        elif divergence == "bearish":
            signal = "VENDRE"
            reason = "🔥 Divergence baissière"
            risk_advice = "🔻 Pression vendeuse"

        # 2. RSI extrême + MACD (seuils assouplis)
        elif not pd.isna(rsi_val):
            if rsi_val < 40 and hist_val > -0.1:  # Moins strict
                signal = "ACHETER"
                reason = "RSI survendu et MACD se redresse"
                risk_advice = "📈 Zone de rebond probable"
            elif rsi_val > 60 and hist_val < 0.1:  # Moins strict
                signal = "VENDRE"
                reason = "RSI suracheté et MACD faiblit"
                risk_advice = "🔻 Risque de correction"

        # 3. Support / Résistance (seuils assouplis)
        elif support and resistance:
            if last_price <= support * 1.02 and rsi_val < 50:
                signal = "ACHETER"
                reason = "Proche support et RSI modéré"
                risk_advice = "📈 Support solide"
            elif last_price >= resistance * 0.98 and rsi_val > 50:
                signal = "VENDRE"
                reason = "Proche résistance et RSI modéré"
                risk_advice = "🔻 Résistance testée"

        # 4. Croisement MACD (inchangé)
        if signal == "ATTENDRE" and len(macd_line) >= 2:
            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            if prev_macd < prev_signal and macd_val > signal_val:
                signal = "ACHETER"
                reason = "MACD passe au-dessus du signal"
                risk_advice = "✅ Tendance haussière"
            elif prev_macd > prev_signal and macd_val < signal_val:
                signal = "VENDRE"
                reason = "MACD passe sous le signal"
                risk_advice = "🔻 Tendance baissière"

        # 5. Pullback dans la tendance
        if signal == "ATTENDRE":
            if last_price > sma20 > sma50 and rsi_val < 55:
                signal = "ACHETER"
                reason = "Pullback dans tendance hausse"
                risk_advice = "⚠️ Attendre confirmation"
            elif last_price < sma20 < sma50 and rsi_val > 45:
                signal = "VENDRE"
                reason = "Rebond dans tendance baisse"
                risk_advice = "⚠️ Prudence"

        # Si toujours ATTENDRE, on donne une raison utile
        if signal == "ATTENDRE":
            if rsi_val > 60:
                reason = "Marché suracheté, attendre repli"
            elif rsi_val < 40:
                reason = "Marché survendu, attendre rebond"
            else:
                reason = "Aucun signal clair – phase de consolidation"

        # Teddy Score (inchangé mais peut être amélioré plus tard)
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