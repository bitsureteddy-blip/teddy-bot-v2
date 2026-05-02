import pandas as pd
from typing import Dict

from indicators import rsi, macd, sma, atr, adx, bollinger_bands, rsi_from_ticks, macd_from_ticks
from config import (
    ATR_MULTIPLIER_SL, RR_RATIO_TARGET,
    ADX_THRESHOLDS, ATR_PRICE_MAX,
    RSI_BUY_LOW, RSI_BUY_HIGH, RSI_SELL_LOW, RSI_SELL_HIGH
)
from i18n import get_text


class SignalEngine:
    @staticmethod
    def _asset_type(symbol: str) -> str:
        symbol = symbol.upper()
        forex = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD"}
        metals = {"XAUUSD", "XAGUSD"}
        crypto = {"BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "ADAUSD"}

        if symbol in forex:
            return "forex"
        if symbol in metals:
            return "metal"
        if symbol in crypto:
            return "crypto"
        return "stock"

    @staticmethod
    def analyze(df: pd.DataFrame, lang: str = "en", symbol: str = "") -> Dict:
        if symbol.upper() == "BTCUSD":
            return SignalEngine.analyze_btc(df, lang)
        if symbol.upper() == "XAUUSD":
            return SignalEngine.analyze_xau(df, lang)
        asset = SignalEngine._asset_type(symbol) if symbol else "forex"
        # Seuils spécifiques BTCUSD (après asset = "crypto")
        if symbol.upper() == "BTCUSD":
            adx_threshold = 25
            atr_price_max_val = 0.04
            rsi_buy_low_val = 48
            rsi_buy_high_val = 75
            rsi_sell_low_val = 25
            rsi_sell_high_val = 52
        else:
            adx_threshold = ADX_THRESHOLDS[asset]
            atr_price_max_val = ATR_PRICE_MAX[asset]
            rsi_buy_low_val = RSI_BUY_LOW[asset]
            rsi_buy_high_val = RSI_BUY_HIGH[asset]
            rsi_sell_low_val = RSI_SELL_LOW[asset]
            rsi_sell_high_val = RSI_SELL_HIGH[asset]

        # Normaliser les colonnes (minuscules -> Majuscules)
        rename = {}
        for c in df.columns:
            if c.lower() in ["open", "high", "low", "close", "volume"]:
                rename[c] = c.capitalize()
        if rename:
            df = df.rename(columns=rename)

        required = {"Open", "High", "Low", "Close"}
        if df is None or df.empty or not required.issubset(set(df.columns)) or len(df) < 60:
            return {
                "signal": "WAIT", "signal_text": get_text(lang, "signal_wait"),
                "reason": get_text(lang, "signal_insufficient_data"), "risk_advice": "",
                "teddy_score": 0, "confidence": get_text(lang, "confidence_low"),
                "sl": None, "tp": None, "tp1": None, "tp2": None, "rr_ratio": None, "indicators": {}
            }

        close, high, low = df["Close"], df["High"], df["Low"]
        last_price = float(close.iloc[-1])
        sma20_val = float(sma(close, 20).iloc[-1])
        sma50_val = float(sma(close, 50).iloc[-1])
        rsi_val = float(rsi(close, 14).iloc[-1])
        macd_line, signal_line, hist = macd(close, 12, 26, 9)
        macd_val, macd_sig_val, hist_val = float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(hist.iloc[-1])
        adx_series, _, _ = adx(high, low, close, 14)
        adx_val = float(adx_series.iloc[-1]) if pd.notna(adx_series.iloc[-1]) else 0.0
        atr_val = float(atr(high, low, close, 14).iloc[-1])
        upper_bb, _, lower_bb = bollinger_bands(close, 20, 2.0)
        trend = "BULLISH" if last_price > sma20_val > sma50_val else "BEARISH" if last_price < sma20_val < sma50_val else "NEUTRAL"
        # Condition volume (BTC uniquement)
        if "Volume" in df.columns:
            avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
            current_vol = df["Volume"].iloc[-1]
            volume_ok = current_vol > avg_vol
        else:
            volume_ok = True

        buy_cond = [
            last_price > sma20_val > sma50_val,
            rsi_buy_low_val <= rsi_val <= rsi_buy_high_val,
            macd_val > macd_sig_val and hist_val > 0,
            adx_val >= adx_threshold,
            abs(sma20_val - sma50_val) >= 0.25 * atr_val,
            (atr_val / last_price) <= atr_price_max_val,
        ]
        sell_cond = [
            last_price < sma20_val < sma50_val,
            rsi_sell_low_val <= rsi_val <= rsi_sell_high_val,
            macd_val < macd_sig_val and hist_val < 0,
            adx_val >= adx_threshold,
            abs(sma20_val - sma50_val) >= 0.25 * atr_val,
            (atr_val / last_price) <= atr_price_max_val,
        ]
        if symbol.upper() == "BTCUSD":
            buy_cond.append(volume_ok)
            sell_cond.append(volume_ok)

        buy_count, sell_count = sum(buy_cond), sum(sell_cond)
        condition_count = 7 if symbol.upper() == "BTCUSD" else 6
        teddy_score = min(int(max(buy_count, sell_count) / condition_count * 100), 95)

        signal = "WAIT"
        if buy_count == 6:
            signal = "BUY"
        elif sell_count == 6:
            signal = "SELL"

        if symbol.upper() == "BTCUSD" and not volume_ok:
            signal = "WAIT"

        sl = tp = tp1 = tp2 = rr_ratio = None
        if signal in ("BUY", "SELL") and atr_val > 0:
            sl_distance = ATR_MULTIPLIER_SL * atr_val
            tp1_distance = RR_RATIO_TARGET * atr_val
            tp2_distance = (RR_RATIO_TARGET + 1.0) * atr_val
            if signal == "BUY":
                sl, tp1, tp2 = last_price - sl_distance, last_price + tp1_distance, last_price + tp2_distance
            else:
                sl, tp1, tp2 = last_price + sl_distance, last_price - tp1_distance, last_price - tp2_distance
            tp = tp1
            rr_ratio = round(abs(tp1 - last_price) / abs(last_price - sl), 2)

        confidence = get_text(lang, "confidence_high") if teddy_score >= 80 else get_text(lang, "confidence_medium") if teddy_score >= 60 else get_text(lang, "confidence_low")
        reason = get_text(lang, "signal_buy_reason") if signal == "BUY" else get_text(lang, "signal_sell_reason") if signal == "SELL" else get_text(lang, "signal_wait_neutral")
        risk_advice = get_text(lang, "signal_buy_advice") if signal == "BUY" else get_text(lang, "signal_sell_advice") if signal == "SELL" else get_text(lang, "signal_wait_advice")

        return {
            "signal": signal,
            "signal_text": get_text(lang, f"signal_{signal.lower()}"),
            "reason": reason,
            "risk_advice": risk_advice,
            "teddy_score": teddy_score,
            "confidence": confidence,
            "sl": sl,
            "tp": tp,
            "tp1": tp1,
            "tp2": tp2,
            "rr_ratio": rr_ratio,
            "indicators": {
                "price": last_price, "rsi": rsi_val, "adx": adx_val,
                "sma20": sma20_val, "sma50": sma50_val,
                "macd": macd_val, "macd_signal": macd_sig_val, "atr": atr_val,
                "bb_upper": upper_bb, "bb_lower": lower_bb, "trend": trend
            },
        }

    @staticmethod
    def analyze_scalp(symbol: str, ticks: list, price_data: dict, duration: int, lang: str = "en") -> dict:
        if not ticks or len(ticks) < 14:
            return {
                "symbol": symbol, "signal": "WAIT", "price": price_data["price"], "bid": price_data["bid"], "ask": price_data["ask"],
                "spread": price_data["ask"] - price_data["bid"], "spread_pct": 0.0, "rsi": 50.0,
                "reason": get_text(lang, "signal_insufficient_data")
            }

        rsi_val = float(rsi_from_ticks(ticks, 14).iloc[-1])
        macd_line, macd_signal, hist = macd_from_ticks(ticks)
        macd_v, macd_sig_v, hist_v = float(macd_line.iloc[-1]), float(macd_signal.iloc[-1]), float(hist.iloc[-1])
        bid, ask, price = float(price_data["bid"]), float(price_data["ask"]), float(price_data["price"])
        spread = ask - bid
        spread_pct = round((spread / price) * 100, 4) if price else 0.0

        signal = "WAIT"
        reason = get_text(lang, "scalp_wait_reason")
        if spread_pct <= 0.15:
            if rsi_val <= 42 and macd_v > macd_sig_v and hist_v > 0:
                signal = "BUY"
                reason = get_text(lang, "signal_buy_reason")
            elif rsi_val >= 58 and macd_v < macd_sig_v and hist_v < 0:
                signal = "SELL"
                reason = get_text(lang, "signal_sell_reason")
            elif rsi_val < 35:
                signal = "BUY"
                reason = get_text(lang, "scalp_fallback_buy")
            elif rsi_val > 65:
                signal = "SELL"
                reason = get_text(lang, "scalp_fallback_sell")

        return {
            "symbol": symbol,
            "signal": signal,
            "price": price,
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "spread_pct": spread_pct,
            "rsi": rsi_val,
            "reason": reason,
        }

    @staticmethod
    def analyze_btc(df: pd.DataFrame, lang: str = "en") -> Dict:
        # Normaliser colonnes
        rename = {}
        for c in df.columns:
            if c.lower() in ["open", "high", "low", "close", "volume"]:
                rename[c] = c.capitalize()
        if rename:
            df = df.rename(columns=rename)

        required = {"Open", "High", "Low", "Close"}
        if df is None or df.empty or not required.issubset(set(df.columns)) or len(df) < 200:
            return {
                "signal": "WAIT", "signal_text": get_text(lang, "signal_wait"),
                "reason": get_text(lang, "signal_insufficient_data"), "risk_advice": "",
                "teddy_score": 0, "confidence": get_text(lang, "confidence_low"),
                "sl": None, "tp": None, "tp1": None, "tp2": None, "rr_ratio": None, "indicators": {}
            }

        from config import BTC_ADX_MIN, BTC_RSI_BUY_LOW, BTC_RSI_BUY_HIGH, BTC_RSI_SELL_LOW, BTC_RSI_SELL_HIGH, BTC_ATR_MIN_RATIO, BTC_ATR_MAX_RATIO

        close, high, low = df["Close"], df["High"], df["Low"]
        last_price = float(close.iloc[-1])
        sma20_val = float(sma(close, 20).iloc[-1])
        sma50_val = float(sma(close, 50).iloc[-1])
        sma200_val = float(sma(close, 200).iloc[-1])
        rsi_val = float(rsi(close, 14).iloc[-1])
        macd_line, signal_line, hist = macd(close, 12, 26, 9)
        macd_val, macd_sig_val, hist_val = float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(hist.iloc[-1])
        adx_series, _, _ = adx(high, low, close, 14)
        adx_val = float(adx_series.iloc[-1]) if pd.notna(adx_series.iloc[-1]) else 0.0
        atr_val = float(atr(high, low, close, 14).iloc[-1])
        upper_bb, mid_bb, lower_bb = bollinger_bands(close, 20, 2.0)
        atr_ratio = atr_val / last_price

        trend_bullish = sma50_val > sma200_val
        trend_bearish = sma50_val < sma200_val
        atr_ok = BTC_ATR_MIN_RATIO <= atr_ratio <= BTC_ATR_MAX_RATIO
        breakout_up = last_price > float(upper_bb.iloc[-1])
        breakout_down = last_price < float(lower_bb.iloc[-1])

        buy_cond = [
            trend_bullish,
            adx_val >= BTC_ADX_MIN,
            last_price > sma20_val and sma20_val > sma50_val,
            breakout_up,
            BTC_RSI_BUY_LOW <= rsi_val <= BTC_RSI_BUY_HIGH,
            atr_ok,
        ]
        sell_cond = [
            trend_bearish,
            adx_val >= BTC_ADX_MIN,
            last_price < sma20_val and sma20_val < sma50_val,
            breakout_down,
            BTC_RSI_SELL_LOW <= rsi_val <= BTC_RSI_SELL_HIGH,
            atr_ok,
        ]

        buy_count, sell_count = sum(buy_cond), sum(sell_cond)
        teddy_score = min(int(max(buy_count, sell_count) / 6 * 100), 95)

        signal = "WAIT"
        if buy_count == 6:
            signal = "BUY"
        elif sell_count == 6:
            signal = "SELL"

        sl = tp = tp1 = tp2 = rr_ratio = None
        if signal in ("BUY", "SELL") and atr_val > 0:
            sl_distance = 1.2 * atr_val
            tp_distance = 2.0 * atr_val
            if signal == "BUY":
                sl, tp1, tp2 = last_price - sl_distance, last_price + tp_distance, last_price + tp_distance + atr_val
            else:
                sl, tp1, tp2 = last_price + sl_distance, last_price - tp_distance, last_price - tp_distance - atr_val
            tp = tp1
            rr_ratio = round(abs(tp1 - last_price) / abs(last_price - sl), 2)

        confidence = get_text(lang, "confidence_high") if teddy_score >= 80 else get_text(lang, "confidence_medium") if teddy_score >= 60 else get_text(lang, "confidence_low")
        reason = get_text(lang, "signal_buy_reason") if signal == "BUY" else get_text(lang, "signal_sell_reason") if signal == "SELL" else get_text(lang, "signal_wait_neutral")
        risk_advice = get_text(lang, "signal_buy_advice") if signal == "BUY" else get_text(lang, "signal_sell_advice") if signal == "SELL" else get_text(lang, "signal_wait_advice")

        return {
            "signal": signal, "signal_text": get_text(lang, f"signal_{signal.lower()}"),
            "reason": reason, "risk_advice": risk_advice,
            "teddy_score": teddy_score, "confidence": confidence,
            "sl": sl, "tp": tp, "tp1": tp1, "tp2": tp2, "rr_ratio": rr_ratio,
            "indicators": {
                "price": last_price, "rsi": rsi_val, "adx": adx_val,
                "sma20": sma20_val, "sma50": sma50_val, "sma200": sma200_val,
                "macd": macd_val, "macd_signal": macd_sig_val, "atr": atr_val,
                "bb_upper": upper_bb, "bb_lower": lower_bb, "trend": "BULLISH" if trend_bullish else "BEARISH" if trend_bearish else "NEUTRAL"
            },
        }

    @staticmethod
    def analyze_xau(df: pd.DataFrame, lang: str = "en") -> Dict:
        # Normaliser colonnes
        rename = {}
        for c in df.columns:
            if c.lower() in ["open", "high", "low", "close", "volume"]:
                rename[c] = c.capitalize()
        if rename:
            df = df.rename(columns=rename)

        required = {"Open", "High", "Low", "Close"}
        if df is None or df.empty or not required.issubset(set(df.columns)) or len(df) < 60:
            return {
                "signal": "WAIT", "signal_text": get_text(lang, "signal_wait"),
                "reason": get_text(lang, "signal_insufficient_data"), "risk_advice": "",
                "teddy_score": 0, "confidence": get_text(lang, "confidence_low"),
                "sl": None, "tp": None, "tp1": None, "tp2": None, "rr_ratio": None, "indicators": {}
            }

        from config import XAU_ADX_MAX, XAU_RSI_BUY_MAX, XAU_RSI_SELL_MIN, XAU_ATR_MAX_RATIO

        close, high, low = df["Close"], df["High"], df["Low"]
        last_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])
        sma20_val = float(sma(close, 20).iloc[-1])
        sma50_val = float(sma(close, 50).iloc[-1])
        rsi_val = float(rsi(close, 14).iloc[-1])
        adx_series, _, _ = adx(high, low, close, 14)
        adx_val = float(adx_series.iloc[-1]) if pd.notna(adx_series.iloc[-1]) else 0.0
        atr_val = float(atr(high, low, close, 14).iloc[-1])
        upper_bb, mid_bb, lower_bb = bollinger_bands(close, 20, 2.0)
        atr_ratio = atr_val / last_price

        near_lower_bb = last_price <= float(lower_bb.iloc[-1]) * 1.005
        near_upper_bb = last_price >= float(upper_bb.iloc[-1]) * 0.995
        bullish_candle = last_price > prev_price
        bearish_candle = last_price < prev_price
        atr_ok = atr_ratio <= XAU_ATR_MAX_RATIO
        trend_light_bull = sma50_val > sma(close, 200).iloc[-1] if len(close) >= 200 else True

        buy_cond = [
            trend_light_bull,
            adx_val <= XAU_ADX_MAX,
            near_lower_bb,
            rsi_val <= XAU_RSI_BUY_MAX,
            bullish_candle,
            atr_ok,
        ]
        sell_cond = [
            not trend_light_bull if len(close) >= 200 else False,
            adx_val <= XAU_ADX_MAX,
            near_upper_bb,
            rsi_val >= XAU_RSI_SELL_MIN,
            bearish_candle,
            atr_ok,
        ]

        buy_count, sell_count = sum(buy_cond), sum(sell_cond)
        teddy_score = min(int(max(buy_count, sell_count) / 6 * 100), 95)

        signal = "WAIT"
        if buy_count == 6:
            signal = "BUY"
        elif sell_count == 6:
            signal = "SELL"

        sl = tp = tp1 = tp2 = rr_ratio = None
        if signal in ("BUY", "SELL") and atr_val > 0:
            sl_distance = 1.0 * atr_val
            tp_distance = 1.5 * atr_val
            if signal == "BUY":
                sl, tp1 = last_price - sl_distance, last_price + tp_distance
            else:
                sl, tp1 = last_price + sl_distance, last_price - tp_distance
            tp = tp1
            rr_ratio = round(abs(tp1 - last_price) / abs(last_price - sl), 2)

        confidence = get_text(lang, "confidence_high") if teddy_score >= 80 else get_text(lang, "confidence_medium") if teddy_score >= 60 else get_text(lang, "confidence_low")
        reason = get_text(lang, "signal_buy_reason") if signal == "BUY" else get_text(lang, "signal_sell_reason") if signal == "SELL" else get_text(lang, "signal_wait_neutral")
        risk_advice = get_text(lang, "signal_buy_advice") if signal == "BUY" else get_text(lang, "signal_sell_advice") if signal == "SELL" else get_text(lang, "signal_wait_advice")

        return {
            "signal": signal, "signal_text": get_text(lang, f"signal_{signal.lower()}"),
            "reason": reason, "risk_advice": risk_advice,
            "teddy_score": teddy_score, "confidence": confidence,
            "sl": sl, "tp": tp, "tp1": tp1, "tp2": tp2, "rr_ratio": rr_ratio,
            "indicators": {
                "price": last_price, "rsi": rsi_val, "adx": adx_val,
                "sma20": sma20_val, "sma50": sma50_val,
                "atr": atr_val, "bb_upper": upper_bb, "bb_lower": lower_bb,
                "trend": "BULLISH" if trend_light_bull else "BEARISH"
            },
        }
