import pandas as pd
from typing import Dict

from indicators import rsi, macd, sma, atr, adx, bollinger_bands
from config import (
    ATR_MULTIPLIER_SL, RR_RATIO_TARGET, SYMBOL_CONFIGS
)
from i18n import get_text


class SignalEngine:

    @staticmethod
    def _normalize_df(df):
        rename = {}
        for c in df.columns:
            if c.lower() in ["open", "high", "low", "close", "volume"]:
                rename[c] = c.capitalize()
        return df.rename(columns=rename) if rename else df

    @staticmethod
    def _valid_df(df, min_len=60):
        required = {"Open", "High", "Low", "Close"}
        return df is not None and not df.empty and required.issubset(df.columns) and len(df) >= min_len

    @staticmethod
    def _wait(lang):
        return {
            "signal": "WAIT",
            "signal_text": get_text(lang, "signal_wait"),
            "reason": get_text(lang, "signal_insufficient_data"),
            "risk_advice": "",
            "teddy_score": 0,
            "confidence": get_text(lang, "confidence_low"),
            "sl": None, "tp": None,
            "tp1": None, "tp2": None,
            "rr_ratio": None,
            "indicators": {}
        }

    @staticmethod
    def analyze(df: pd.DataFrame, lang="en", symbol="") -> Dict:
        symbol = symbol.upper()
        df = SignalEngine._normalize_df(df)

        if not SignalEngine._valid_df(df):
            return SignalEngine._wait(lang)

        cfg = SYMBOL_CONFIGS.get(symbol, SYMBOL_CONFIGS["EURUSD"])

        close, high, low = df["Close"], df["High"], df["Low"]
        last_price = float(close.iloc[-1])

        sma20 = float(sma(close, 20).iloc[-1])
        sma50 = float(sma(close, 50).iloc[-1])

        rsi_val = float(rsi(close, 14).iloc[-1])
        macd_line, macd_sig, hist = macd(close, 12, 26, 9)
        macd_val = float(macd_line.iloc[-1])
        macd_sig_val = float(macd_sig.iloc[-1])
        hist_val = float(hist.iloc[-1])

        adx_val = float(adx(high, low, close, 14)[0].iloc[-1])
        atr_val = float(atr(high, low, close, 14).iloc[-1])

        upper, _, lower = bollinger_bands(close, 20, 2)
        upper = float(upper.iloc[-1])
        lower = float(lower.iloc[-1])

        atr_ratio = atr_val / last_price if last_price else 0

        buy_cond = [
            last_price > sma20 > sma50,
            cfg["rsi_buy_low"] <= rsi_val <= cfg["rsi_buy_high"],
            macd_val > macd_sig_val and hist_val > 0,
            adx_val >= cfg["adx_min"],
            atr_ratio <= cfg["atr_max_pct"] / 100,
        ]

        sell_cond = [
            last_price < sma20 < sma50,
            cfg["rsi_sell_low"] <= rsi_val <= cfg["rsi_sell_high"],
            macd_val < macd_sig_val and hist_val < 0,
            adx_val >= cfg["adx_min"],
            atr_ratio <= cfg["atr_max_pct"] / 100,
        ]

        indicators = {
            "price": last_price, "rsi": rsi_val, "adx": adx_val,
            "sma20": sma20, "sma50": sma50, "atr": atr_val,
            "bb_upper": upper, "bb_lower": lower,
        }

        return SignalEngine._finalize(
            buy_cond, sell_cond, last_price, atr_val, indicators, lang,
            min_cond=cfg["min_cond"], cfg=cfg
        )

    @staticmethod
    def _finalize(buy_cond, sell_cond, price, atr_val, indicators, lang, min_cond=4, cfg=None):
        buy_count = sum(buy_cond)
        sell_count = sum(sell_cond)

        signal = "WAIT"
        if buy_count >= min_cond:
            signal = "BUY"
        elif sell_count >= min_cond:
            signal = "SELL"

        sl = tp = tp1 = tp2 = rr = None

        if signal in ("BUY", "SELL") and atr_val > 0:
            sl_dist = ATR_MULTIPLIER_SL * atr_val
            tp_dist = RR_RATIO_TARGET * atr_val

            if signal == "BUY":
                sl = price - sl_dist
                tp1 = price + tp_dist
                tp2 = price + (tp_dist + atr_val)
            else:
                sl = price + sl_dist
                tp1 = price - tp_dist
                tp2 = price - (tp_dist + atr_val)

            tp = tp1
            rr = round(abs(tp1 - price) / abs(price - sl), 2)

        weights = (cfg or {}).get("weights", {"trend": 20, "rsi": 20, "macd": 20, "adx": 20, "atr": 20})
        weight_list = [weights["trend"], weights["rsi"], weights["macd"], weights["adx"], weights["atr"]]
        buy_score = sum(w for w, c in zip(weight_list, buy_cond) if c)
        sell_score = sum(w for w, c in zip(weight_list, sell_cond) if c)
        score = max(buy_score, sell_score)

        reason = get_text(lang, f"signal_{signal.lower()}_reason") if signal != "WAIT" else get_text(lang, "signal_wait_neutral")
        risk = get_text(lang, f"signal_{signal.lower()}_advice") if signal != "WAIT" else get_text(lang, "signal_wait_advice")

        return {
            "signal": signal,
            "signal_text": get_text(lang, f"signal_{signal.lower()}"),
            "reason": reason,
            "risk_advice": risk,
            "teddy_score": min(score, 95),
            "confidence": get_text(lang, "confidence_high" if score >= 75 else "confidence_medium" if score >= 55 else "confidence_low"),
            "sl": sl,
            "tp": tp,
            "tp1": tp1,
            "tp2": tp2,
            "rr_ratio": rr,
            "indicators": indicators,
        }