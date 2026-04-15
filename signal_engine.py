"""
Logique métier : génération des signaux ACHETER/VENDRE/ATTENDRE
et calcul du Teddy Score.
"""

import pandas as pd
from typing import Dict

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
        if df is None or df.empty or len(df) < SMA_LONG:
            return {
                "signal": "ATTENDRE",
                "reason": "Données insuffisantes",
                "risk_advice": "",
                "teddy_score": 0,
                "indicators": {}
            }

        close = df["Close"]
        high = df["High"]
        low = df["Low"]

        # === INDICATEURS ===
        rsi_series = rsi(close, RSI_PERIOD)
        rsi_val = rsi_series.iloc[-1]

        macd_line, macd_signal_line, hist = macd(
            close, MACD_FAST, MACD_SLOW, MACD_SIGNAL
        )

        macd_val = macd_line.iloc[-1]
        macd_sig_val = macd_signal_line.iloc[-1]
        hist_val = hist.iloc[-1]

        upper_bb, mid_bb, lower_bb = bollinger_bands(
            close, BB_PERIOD, BB_STD
        )

        sma20 = sma(close, SMA_SHORT).iloc[-1]
        sma50 = sma(close, SMA_LONG).iloc[-1]

        support, resistance = support_resistance(
            high, low, SUPPORT_RESISTANCE_LOOKBACK
        )

        last_price = close.iloc[-1]

        divergence = detect_divergence(
            close, rsi_series, DIVERGENCE_LOOKBACK
        )

        # === TENDANCE ===
        if last_price > sma50:
            trend = "HAUSSIER"
        elif last_price < sma50:
            trend = "BAISSIER"
        else:
            trend = "NEUTRE"

        # === TEDDY SCORE AMÉLIORÉ ===
        teddy_score = SignalEngine._compute_teddy_score(
            df,
            rsi_val,
            sma20,
            sma50,
            support,
            resistance,
            last_price,
            macd_val,
            macd_sig_val,
            divergence
        )

        # === SIGNAL (SEUILS ASSOUPLIS) ===
        if teddy_score >= 55:
            signal = "ACHETER"
        elif teddy_score <= 45:
            signal = "VENDRE"
        else:
            signal = "ATTENDRE"

        # === FILTRE DE TENDANCE ASSOUPLI ===
        # On autorise un signal contraire si le score est très convaincant
        if trend == "HAUSSIER" and signal == "VENDRE" and teddy_score > 30:
            signal = "ATTENDRE"
        if trend == "BAISSIER" and signal == "ACHETER" and teddy_score < 70:
            signal = "ATTENDRE"

        # === RAISON ===
        if signal == "ACHETER":
            reason = "📈 Signaux haussiers détectés"
            risk_advice = "⚠️ Entrée progressive conseillée"
        elif signal == "VENDRE":
            reason = "📉 Signaux baissiers détectés"
            risk_advice = "⚠️ Risque de continuation"
        else:
            # Raison plus informative
            if teddy_score >= 55:
                reason = "Marché suracheté, attendez une correction"
            elif teddy_score <= 45:
                reason = "Marché survendu, attendez un rebond"
            else:
                reason = "Aucun signal clair – phase de consolidation"
            risk_advice = "⏳ Attendre une confirmation"

        indicators = {
            "price": last_price,
            "rsi": rsi_val,
            "sma20": sma20,
            "sma50": sma50,
            "macd": macd_val,
            "macd_signal": macd_sig_val,
            "bb_upper": upper_bb.iloc[-1],
            "bb_lower": lower_bb.iloc[-1],
            "support": support,
            "resistance": resistance,
            "trend": trend
        }

        return {
            "signal": signal,
            "reason": reason,
            "risk_advice": risk_advice,
            "teddy_score": teddy_score,
            "indicators": indicators
        }

    @staticmethod
    def _compute_teddy_score(
        df,
        rsi_val,
        sma20,
        sma50,
        support,
        resistance,
        price,
        macd,
        macd_signal,
        divergence
    ):
        score = 50

        # RSI – seuils assouplis
        if rsi_val < 40:
            score += 12
        elif rsi_val > 60:
            score -= 12

        # Tendance
        if price > sma50:
            score += 10
        else:
            score -= 10

        if sma20 > sma50:
            score += 10
        else:
            score -= 10

        # Support / Résistance – seuils élargis
        if support is not None and price <= support * 1.03:
            score += 10
        if resistance is not None and price >= resistance * 0.97:
            score -= 10

        # Divergence
        if divergence == "bullish":
            score += 15
        elif divergence == "bearish":
            score -= 15

        # MACD – poids augmenté
        if macd > macd_signal:
            score += 15
        else:
            score -= 15

        # Volume
        if "Volume" in df.columns:
            avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
            current_vol = df["Volume"].iloc[-1]
            if pd.notna(avg_vol) and current_vol > avg_vol * 1.3:
                score += 5

        return max(0, min(100, score))