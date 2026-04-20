"""
Logique métier : génération des signaux ACHETER/VENDRE/ATTENDRE
et calcul du Teddy Score.
"""

import pandas as pd
from typing import Dict

from indicators import (
    rsi, macd, bollinger_bands, sma, support_resistance, detect_divergence,
    stochastic, adx, atr, fibonacci_levels
)

from config import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD, SMA_SHORT, SMA_LONG,
    SUPPORT_RESISTANCE_LOOKBACK, DIVERGENCE_LOOKBACK,
    STOCH_K_PERIOD, STOCH_D_PERIOD, STOCH_SMOOTH,
    ADX_PERIOD, ATR_PERIOD, ATR_MULTIPLIER_SL, RR_RATIO_TARGET
)
from i18n import get_text


class SignalEngine:

    @staticmethod
    def analyze(df: pd.DataFrame, lang: str = "en") -> Dict:
        if df is None or df.empty or len(df) < SMA_LONG:
            return {
                "signal": "WAIT",
                "signal_text": get_text(lang, "signal_wait"),
                "reason": get_text(lang, "signal_insufficient_data"),
                "risk_advice": "",
                "teddy_score": 0,
                "confidence": get_text(lang, "confidence_low"),
                "sl": None,
                "tp": None,
                "rr_ratio": None,
                "indicators": {}
            }

        close = df["Close"]
        high = df["High"]
        low = df["Low"]

        # === INDICATEURS ===
        rsi_series = rsi(close, RSI_PERIOD)
        rsi_val = rsi_series.iloc[-1]

        stoch_k, stoch_d = stochastic(high, low, close,
                                      STOCH_K_PERIOD, STOCH_D_PERIOD, STOCH_SMOOTH)
        stoch_k_val = stoch_k.iloc[-1]
        stoch_d_val = stoch_d.iloc[-1]

        adx_series, plus_di, minus_di = adx(high, low, close, ADX_PERIOD)
        adx_val = adx_series.iloc[-1]
        if pd.isna(adx_val):
            adx_val = 0.0

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

        atr_val = atr(high, low, close, ATR_PERIOD).iloc[-1]

        last_price = close.iloc[-1]

        divergence = detect_divergence(
            close, rsi_series, DIVERGENCE_LOOKBACK
        )

        # Niveaux de Fibonacci sur le dernier swing
        recent_high = high.iloc[-50:].max()
        recent_low = low.iloc[-50:].min()
        fib_levels = fibonacci_levels(recent_high, recent_low)

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
            stoch_k_val,
            stoch_d_val,
            adx_val,
            plus_di.iloc[-1],
            minus_di.iloc[-1],
            sma20,
            sma50,
            support,
            resistance,
            last_price,
            macd_val,
            macd_sig_val,
            divergence
        )

        # === NIVEAU DE CONFIANCE ===
        if teddy_score >= 70 or teddy_score <= 30:
            confidence = get_text(lang, "confidence_high")
        elif teddy_score >= 55 or teddy_score <= 45:
            confidence = get_text(lang, "confidence_medium")
        else:
            confidence = get_text(lang, "confidence_low")

        # === SIGNAL (clé interne) ===
        if teddy_score >= 55:
            signal_key = "BUY"
        elif teddy_score <= 45:
            signal_key = "SELL"
        else:
            signal_key = "WAIT"

        # === FILTRE DE TENDANCE ===
        if trend == "HAUSSIER" and signal_key == "SELL" and teddy_score > 30:
            signal_key = "WAIT"
        if trend == "BAISSIER" and signal_key == "BUY" and teddy_score < 70:
            signal_key = "WAIT"

        # === CALCUL SL / TP ===
        sl = None
        tp = None
        rr_ratio = None
        if signal_key in ("BUY", "SELL") and atr_val is not None:
            sl_distance = atr_val * ATR_MULTIPLIER_SL
            if signal_key == "BUY":
                sl = last_price - sl_distance
                if resistance and resistance > last_price:
                    tp = resistance
                else:
                    tp = last_price + (sl_distance * RR_RATIO_TARGET)
            else:  # SELL
                sl = last_price + sl_distance
                if support and support < last_price:
                    tp = support
                else:
                    tp = last_price - (sl_distance * RR_RATIO_TARGET)

            rr_ratio = abs(tp - last_price) / abs(last_price - sl) if sl != last_price else 0
            rr_ratio = round(rr_ratio, 2)

        # === RAISON (BILINGUE) ===
        if signal_key == "BUY":
            reason = get_text(lang, "signal_buy_reason")
            risk_advice = get_text(lang, "signal_buy_advice")
        elif signal_key == "SELL":
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

        indicators = {
            "price": last_price,
            "rsi": rsi_val,
            "stoch_k": stoch_k_val,
            "stoch_d": stoch_d_val,
            "adx": adx_val,
            "sma20": sma20,
            "sma50": sma50,
            "macd": macd_val,
            "macd_signal": macd_sig_val,
            "bb_upper": upper_bb.iloc[-1],
            "bb_lower": lower_bb.iloc[-1],
            "support": support,
            "resistance": resistance,
            "trend": trend,
            "atr": atr_val,
            "fib_levels": fib_levels
        }

        return {
            "signal": signal_key,
            "signal_text": get_text(lang, f"signal_{signal_key.lower()}"),
            "reason": reason,
            "risk_advice": risk_advice,
            "teddy_score": teddy_score,
            "confidence": confidence,
            "sl": sl,
            "tp": tp,
            "rr_ratio": rr_ratio,
            "indicators": indicators
        }

    @staticmethod
    def _compute_teddy_score(
        df,
        rsi_val,
        stoch_k,
        stoch_d,
        adx_val,
        plus_di,
        minus_di,
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

        # RSI
        if rsi_val < 40:
            score += 10
        elif rsi_val > 60:
            score -= 10

        # Stochastic
        if stoch_k < 20 and stoch_d < 20:
            score += 8
        elif stoch_k > 80 and stoch_d > 80:
            score -= 8
        if stoch_k > stoch_d:
            score += 4
        else:
            score -= 4

        # ADX
        if adx_val > 25:
            if plus_di > minus_di:
                score += 10
            else:
                score -= 10

        # Tendance
        if price > sma50:
            score += 8
        else:
            score -= 8

        if sma20 > sma50:
            score += 8
        else:
            score -= 8

        # Support / Résistance
        if support is not None and price <= support * 1.02:
            score += 8
        if resistance is not None and price >= resistance * 0.98:
            score -= 8

        # Divergence
        if divergence == "bullish":
            score += 12
        elif divergence == "bearish":
            score -= 12

        # MACD
        if macd > macd_signal:
            score += 10
        else:
            score -= 10

        # Volume
        if "Volume" in df.columns:
            avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
            current_vol = df["Volume"].iloc[-1]
            if pd.notna(avg_vol) and current_vol > avg_vol * 1.2:
                score += 5

        return max(0, min(100, score))

    # =========================
    # 🚀 SCALPING AVANCÉ
    # =========================
    @staticmethod
    def analyze_scalp(ticks: list, price_data: dict, duration: int) -> dict:
        if len(ticks) < 14:
            return {"signal": "WAIT", "signal_text": "WAIT", "reason": "Insufficient data"}

        rsi_val = SignalEngine._rsi_from_ticks(ticks, 9)
        macd_line, macd_signal = SignalEngine._macd_from_ticks(ticks)

        price = price_data["price"]
        bid = price_data["bid"]
        ask = price_data["ask"]
        spread = ask - bid
        spread_pct = (spread / price) * 100 if price > 0 else 0

        signal_key = "WAIT"
        reason = ""

        if rsi_val < 25:
            signal_key = "BUY"
            reason = f"RSI oversold ({rsi_val:.1f})"
        elif rsi_val > 75:
            signal_key = "SELL"
            reason = f"RSI overbought ({rsi_val:.1f})"

        if len(ticks) >= 15:
            prev_macd, _ = SignalEngine._macd_from_ticks(ticks[:-1])
            if prev_macd < macd_signal and macd_line > macd_signal:
                signal_key = "BUY"
                reason = "MACD bullish crossover"
            elif prev_macd > macd_signal and macd_line < macd_signal:
                signal_key = "SELL"
                reason = "MACD bearish crossover"

        if spread_pct < 0.02:
            if signal_key == "WAIT":
                if bid > price * 0.9999:
                    signal_key = "BUY"
                    reason = "Compressed spread + buying pressure"
                elif ask < price * 1.0001:
                    signal_key = "SELL"
                    reason = "Compressed spread + selling pressure"

        if spread_pct > 0.2 and signal_key != "WAIT":
            signal_key = "WAIT"
            reason = "Volatility too high"

        return {
            "signal": signal_key,
            "signal_text": signal_key,  # sera traduit dans le handler
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
        import pandas as pd
        series = pd.Series(ticks)
        ema_fast = series.ewm(span=fast, adjust=False).mean().iloc[-1]
        ema_slow = series.ewm(span=slow, adjust=False).mean().iloc[-1]
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.9
        return macd_line, signal_line