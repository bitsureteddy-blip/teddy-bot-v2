"""
Logique métier : génération des signaux ACHETER/VENDRE/ATTENDRE
et calcul du Teddy Score.
"""

import pandas as pd
from typing import Dict, Optional

from indicators import (
    rsi, macd, bollinger_bands, sma, support_resistance, detect_divergence
)

from config import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD, SMA_SHORT, SMA_LONG,
    SUPPORT_RESISTANCE_LOOKBACK, DIVERGENCE_LOOKBACK
)
from i18n import get_text


class SignalEngine:
    """
    Moteur d'analyse technique.
    Utilisation :
        engine = SignalEngine(df, timeframe)
        signal = engine.analyze(lang)
    """

    def __init__(self, df: pd.DataFrame, timeframe: str = "1d"):
        self.df = df
        self.timeframe = timeframe
        self.close = df["Close"]
        self.high = df["High"]
        self.low = df["Low"]
        self.volume = df.get("Volume", None)

    def analyze(self, lang: str = "en") -> Dict:
        """Retourne un dictionnaire contenant le signal, le score, les raisons, etc."""
        df = self.df
        if df is None or df.empty or len(df) < SMA_LONG:
            return {
                "action": "ATTENDRE",
                "signal": "ATTENDRE",
                "reason": get_text(lang, "signal_insufficient_data"),
                "risk_advice": "",
                "score": 0,
                "teddy_score": 0,
                "reasons": [get_text(lang, "signal_insufficient_data")]
            }

        close = self.close
        high = self.high
        low = self.low

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

        # === TEDDY SCORE ===
        teddy_score = self._compute_teddy_score(
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

        # === SIGNAL ===
        if teddy_score >= 55:
            action = "ACHETER"
        elif teddy_score <= 45:
            action = "VENDRE"
        else:
            action = "ATTENDRE"

        # Filtre de tendance
        if trend == "HAUSSIER" and action == "VENDRE" and teddy_score > 30:
            action = "ATTENDRE"
        if trend == "BAISSIER" and action == "ACHETER" and teddy_score < 70:
            action = "ATTENDRE"

        # === RAISONS (pour affichage) ===
        reasons = []
        if action == "ACHETER":
            reason = get_text(lang, "signal_buy_reason")
            risk_advice = get_text(lang, "signal_buy_advice")
        elif action == "VENDRE":
            reason = get_text(lang, "signal_sell_reason")
            risk_advice = get_text(lang, "signal_sell_advice")
        else:
            if teddy_score >= 55:
                reason = get_text(lang, "signal_wait_overbought")
            elif teddy_score <= 45:
                reason = get_text(lang, "signal_wait_oversold")
            else:
                reason = get_text(lang, "signal_wait_neutral")
            risk_advice = get_text(lang, "signal_wait_advice")

        # Construction des raisons détaillées
        if rsi_val < 30:
            reasons.append(f"RSI survendu ({rsi_val:.1f})")
        elif rsi_val > 70:
            reasons.append(f"RSI suracheté ({rsi_val:.1f})")
        if macd_val > macd_sig_val:
            reasons.append("MACD haussier")
        elif macd_val < macd_sig_val:
            reasons.append("MACD baissier")
        if last_price > sma20:
            reasons.append(f"Prix > SMA20 ({sma20:.2f})")
        if last_price > sma50:
            reasons.append(f"Prix > SMA50 ({sma50:.2f})")
        if divergence == "bullish":
            reasons.append("Divergence haussière détectée")
        elif divergence == "bearish":
            reasons.append("Divergence baissière détectée")
        if not reasons:
            reasons.append(reason)

        return {
            "action": action,
            "signal": action,  # pour compatibilité
            "reason": reason,
            "risk_advice": risk_advice,
            "score": teddy_score,
            "teddy_score": teddy_score,
            "reasons": reasons,
            "indicators": {
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
        }

    def _compute_teddy_score(
        self,
        rsi_val: float,
        sma20: float,
        sma50: float,
        support: Optional[float],
        resistance: Optional[float],
        price: float,
        macd: float,
        macd_signal: float,
        divergence: str
    ) -> int:
        score = 50

        # RSI
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

        # Support / Résistance
        if support is not None and price <= support * 1.03:
            score += 10
        if resistance is not None and price >= resistance * 0.97:
            score -= 10

        # Divergence
        if divergence == "bullish":
            score += 15
        elif divergence == "bearish":
            score -= 15

        # MACD
        if macd > macd_signal:
            score += 15
        else:
            score -= 15

        # Volume
        if self.volume is not None and not self.volume.empty:
            avg_vol = self.volume.rolling(20).mean().iloc[-1]
            current_vol = self.volume.iloc[-1]
            if pd.notna(avg_vol) and current_vol > avg_vol * 1.3:
                score += 5

        return max(0, min(100, score))

    # =========================
    # 🚀 SCALPING AVANCÉ
    # =========================
    @staticmethod
    def analyze_scalp(ticks: list, price_data: dict, duration: int) -> dict:
        if len(ticks) < 14:
            return {"signal": "ATTENDRE", "reason": "Données insuffisantes"}

        rsi_val = SignalEngine._rsi_from_ticks(ticks, 9)
        macd_line, macd_signal = SignalEngine._macd_from_ticks(ticks)

        price = price_data["price"]
        bid = price_data["bid"]
        ask = price_data["ask"]
        spread = ask - bid
        spread_pct = (spread / price) * 100 if price > 0 else 0

        signal = "ATTENDRE"
        reason = ""

        if rsi_val < 25:
            signal = "ACHETER"
            reason = f"RSI survendu ({rsi_val:.1f})"
        elif rsi_val > 75:
            signal = "VENDRE"
            reason = f"RSI suracheté ({rsi_val:.1f})"

        if len(ticks) >= 15:
            prev_macd, _ = SignalEngine._macd_from_ticks(ticks[:-1])
            if prev_macd < macd_signal and macd_line > macd_signal:
                signal = "ACHETER"
                reason = "MACD croisement haussier"
            elif prev_macd > macd_signal and macd_line < macd_signal:
                signal = "VENDRE"
                reason = "MACD croisement baissier"

        if spread_pct < 0.02:
            if signal == "ATTENDRE":
                if bid > price * 0.9999:
                    signal = "ACHETER"
                    reason = "Spread compressé + pression acheteuse"
                elif ask < price * 1.0001:
                    signal = "VENDRE"
                    reason = "Spread compressé + pression vendeuse"

        if spread_pct > 0.2 and signal != "ATTENDRE":
            signal = "ATTENDRE"
            reason = "Volatilité trop élevée"

        return {
            "signal": signal,
            "reason": reason,
            "price": price,
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "spread_pct": round(spread_pct, 4),
            "rsi": round(rsi_val, 1),
            "duration": duration
        }

    @staticmethod
    def _rsi_from_ticks(ticks: list, period: int = 9) -> float:
        if len(ticks) < period + 1:
            return 50.0
        gains, losses = [], []
        for i in range(1, len(ticks)):
            diff = ticks[i] - ticks[i-1]
            gains.append(diff if diff > 0 else 0)
            losses.append(-diff if diff < 0 else 0)
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _macd_from_ticks(ticks: list, fast: int = 6, slow: int = 13, signal: int = 5):
        if len(ticks) < slow:
            return 0, 0
        series = pd.Series(ticks)
        ema_fast = series.ewm(span=fast, adjust=False).mean().iloc[-1]
        ema_slow = series.ewm(span=slow, adjust=False).mean().iloc[-1]
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.9  # approximation simple
        return macd_line, signal_line

    # Méthodes pour compatibilité avec d'anciens appels
    def rsi(self) -> pd.Series:
        return rsi(self.close, RSI_PERIOD)

    def macd(self):
        return macd(self.close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)

    def atr(self, period: int = 14) -> pd.Series:
        high_low = self.high - self.low
        high_close = (self.high - self.close.shift()).abs()
        low_close = (self.low - self.close.shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()