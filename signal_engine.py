import pandas as pd
from typing import Dict, Optional, Tuple

from indicators import rsi, macd, sma, atr, adx, bollinger_bands, support_resistance
from config import (
    ATR_MULTIPLIER_SL, RR_RATIO_TARGET, SYMBOL_CONFIGS
)
from i18n import get_text


# =========================================================
# CONFIG STYLES DE TRADING
# =========================================================

STYLE_CONFIG = {
    "day":      {"sl_mult": 1.15, "tp_mult": 2.2},
    "swing":    {"sl_mult": 1.75, "tp_mult": 3.5},
    "position": {"sl_mult": 2.5,  "tp_mult": 5.0},
}

# =========================================================
# SCORING
# =========================================================

SCORE_WEIGHTS = {
    "trend": 30,
    "rr":    25,
    "sr":    20,
    "adx":   15,
    "rsi":   10,
}

# Seuils de rejet par style
REJECTION_THRESHOLDS = {
    "day":      {"min_score": 60, "min_adx": 15, "min_rr": 1.3},
    "swing":    {"min_score": 58, "min_adx": 15, "min_rr": 1.5},
    "position": {"min_score": 55, "min_adx": 15, "min_rr": 1.8},
}

# Buffer S/R par style (multiplicateur de l'ATR)
BUFFER_MULTIPLIERS = {
    "day":      0.15,
    "swing":    0.20,
    "position": 0.25,
}


class SignalEngine:

    @staticmethod
    def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
        """Normalise les noms de colonnes en Capitalize (Open, High, Low, Close, Volume)."""
        rename = {}
        for c in df.columns:
            if c.lower() in ["open", "high", "low", "close", "volume"]:
                rename[c] = c.capitalize()
        return df.rename(columns=rename) if rename else df

    @staticmethod
    def _valid_df(df: pd.DataFrame, min_len: int = 60) -> bool:
        """Vérifie que le DataFrame est valide et suffisamment long."""
        required = {"Open", "High", "Low", "Close"}
        return (
            df is not None
            and not df.empty
            and required.issubset(df.columns)
            and len(df) >= min_len
        )

    @staticmethod
    def _wait(
        lang: str,
        reason_key: str = "signal_insufficient_data",
        indicators: Optional[Dict] = None,
        score_detail: Optional[Dict] = None,
    ) -> Dict:
        """
        Retourne un signal WAIT.

        - reason_key peut être une clé i18n (ex: "signal_insufficient_data")
          ou un texte lisible direct (ex: "RR too low for this style").
        - indicators est conservé pour que le graphique s'affiche même en cas de rejet.
        - score_detail est conservé pour la transparence.
        """
        # Distingue clé i18n vs texte brut
        _KNOWN_REASON_KEYS = {
            "signal_insufficient_data",
            "signal_wait_neutral",
        }
        if reason_key in _KNOWN_REASON_KEYS:
            reason_text = get_text(lang, reason_key)
        else:
            # Texte lisible direct (rejets de filtres)
            reason_text = reason_key

        return {
            "signal": "WAIT",
            "signal_text": get_text(lang, "signal_wait"),
            "reason": reason_text,
            "risk_advice": "",
            "teddy_score": 0,
            "confidence": get_text(lang, "confidence_low"),
            "sl": None,
            "tp": None,
            "tp1": None,
            "tp2": None,
            "rr_ratio": None,
            "indicators": indicators or {},
            "score_detail": score_detail or {},
        }

    @staticmethod
    def analyze(df: pd.DataFrame, lang: str = "en", symbol: str = "", style: str = "day") -> Dict:
        """
        Point d'entrée principal.

        Args:
            df:     DataFrame OHLC (minimum 60 bougies).
            lang:   Code langue ("en" ou "fr").
            symbol: Symbole (ex: "EURUSD", "BTCUSD").
            style:  Style de trading ("day", "swing", "position", ou None pour fallback config.py).

        Returns:
            Dict contenant signal, SL, TP, teddy_score, indicators, score_detail, etc.
        """
        symbol = symbol.upper()
        df = SignalEngine._normalize_df(df)

        if not SignalEngine._valid_df(df):
            return SignalEngine._wait(lang)

        cfg = SYMBOL_CONFIGS.get(symbol, SYMBOL_CONFIGS["BTCUSD"])

        close = df["Close"]
        high  = df["High"]
        low   = df["Low"]
        last_price = float(close.iloc[-1])

        # ── Indicateurs ────────────────────────────────────────────────────────
        sma20 = float(sma(close, 20).iloc[-1])
        sma50 = float(sma(close, 50).iloc[-1])

        rsi_val               = float(rsi(close, 14).iloc[-1])
        macd_line, macd_sig, hist = macd(close, 12, 26, 9)
        macd_val              = float(macd_line.iloc[-1])
        macd_sig_val          = float(macd_sig.iloc[-1])
        hist_val              = float(hist.iloc[-1])

        adx_val  = float(adx(high, low, close, 14)[0].iloc[-1])
        atr_val  = float(atr(high, low, close, 14).iloc[-1])

        upper_bb, _, lower_bb = bollinger_bands(close, 20, 2)
        upper_bb = float(upper_bb.iloc[-1])
        lower_bb = float(lower_bb.iloc[-1])

        atr_ratio = atr_val / last_price if last_price else 0

        # ── Support / Résistance (peut retourner None) ─────────────────────────
        sr_result = support_resistance(high, low, 50)
        if sr_result is not None:
            support, resistance = sr_result
        else:
            support, resistance = None, None

        # ── Tendances ──────────────────────────────────────────────────────────
        trend_bull = last_price > sma20 > sma50
        trend_bear = last_price < sma20 < sma50

        # ── Conditions de signal (seuils config.py intacts) ───────────────────
        buy_cond = [
            trend_bull,
            cfg["rsi_buy_low"] <= rsi_val <= cfg["rsi_buy_high"],
            macd_val > macd_sig_val and hist_val > 0,
            adx_val >= cfg["adx_min"],
            atr_ratio <= cfg["atr_max_pct"] / 100,
        ]

        sell_cond = [
            trend_bear,
            cfg["rsi_sell_low"] <= rsi_val <= cfg["rsi_sell_high"],
            macd_val < macd_sig_val and hist_val < 0,
            adx_val >= cfg["adx_min"],
            atr_ratio <= cfg["atr_max_pct"] / 100,
        ]

        # ── Indicators dict (toujours rempli pour le graphique) ───────────────
        indicators = {
            "price":      last_price,
            "rsi":        rsi_val,
            "adx":        adx_val,
            "sma20":      sma20,
            "sma50":      sma50,
            "atr":        atr_val,
            "bb_upper":   upper_bb,
            "bb_lower":   lower_bb,
            "support":    support,
            "resistance": resistance,
        }

        return SignalEngine._finalize(
            buy_cond=buy_cond,
            sell_cond=sell_cond,
            price=last_price,
            atr_val=atr_val,
            indicators=indicators,
            lang=lang,
            min_cond=cfg["min_cond"],
            cfg=cfg,
            support=support,
            resistance=resistance,
            rsi_val=rsi_val,
            adx_val=adx_val,
            trend_bull=trend_bull,
            trend_bear=trend_bear,
            style=style,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # MÉTHODES INTERNES
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_sl_tp(
        signal: str,
        price: float,
        atr_val: float,
        style: Optional[str],
    ) -> Tuple[float, float]:
        """
        Calcule SL et TP bruts selon le style de trading.

        Fallback : ATR_MULTIPLIER_SL / RR_RATIO_TARGET (config.py) si style=None.
        """
        if style and style in STYLE_CONFIG:
            sl_mult = STYLE_CONFIG[style]["sl_mult"]
            tp_mult = STYLE_CONFIG[style]["tp_mult"]
        else:
            sl_mult = ATR_MULTIPLIER_SL
            tp_mult = RR_RATIO_TARGET

        if signal == "BUY":
            sl  = price - sl_mult * atr_val
            tp1 = price + tp_mult * atr_val
        else:  # SELL
            sl  = price + sl_mult * atr_val
            tp1 = price - tp_mult * atr_val

        return sl, tp1

    @staticmethod
    def _adjust_sl_tp_with_sr(
        signal: str,
        price: float,
        sl: float,
        tp1: float,
        atr_val: float,
        support: Optional[float],
        resistance: Optional[float],
        style: Optional[str],
    ) -> Tuple[float, float]:
        """
        Ajuste SL et TP en fonction des niveaux Support/Résistance.

        Si support_resistance() a retourné None, les valeurs ATR sont conservées.
        Buffer = BUFFER_MULTIPLIERS[style] × ATR.
        """
        # Aucun niveau disponible → pas d'ajustement
        if support is None and resistance is None:
            return sl, tp1

        buffer = BUFFER_MULTIPLIERS.get(style, 0.20) * atr_val if style else 0.20 * atr_val

        if signal == "BUY":
            # SL : si un support est EN DESSOUS du SL ATR → l'utiliser
            if support is not None and support < sl:
                sl = support - buffer

            # TP : si une résistance est AVANT le TP → ramener le TP juste en dessous
            if resistance is not None and resistance < tp1:
                tp1 = resistance - buffer

        elif signal == "SELL":
            # SL : si une résistance est AU-DESSUS du SL ATR → l'utiliser
            if resistance is not None and resistance > sl:
                sl = resistance + buffer

            # TP : si un support est AVANT le TP → ramener le TP juste au-dessus
            if support is not None and support > tp1:
                tp1 = support + buffer

        return sl, tp1

    @staticmethod
    def _compute_score(
        signal: str,
        price: float,
        tp1: float,
        rr: Optional[float],
        adx_val: float,
        rsi_val: float,
        trend_bull: bool,
        trend_bear: bool,
        support: Optional[float],
        resistance: Optional[float],
        style: Optional[str],
    ) -> Tuple[int, Dict]:
        """
        Calcule le teddy_score pondéré (0-100) et retourne le détail par critère.

        Barème :
          Trend  30  SMA20 > SMA50 (BUY) ou inverse (SELL)
          RR     25  RR ≥ 2.0 = 25, RR ≥ min_rr_style = 15
          S/R    20  graduel selon position du S/R par rapport au TP
          ADX    15  ADX ≥ 30 = 15, ADX ≥ 25 = 10
          RSI    10  RSI 40-60 = 10, RSI 30-70 = 5
        """
        detail = {"trend": 0, "rr": 0, "sr": 0, "adx": 0, "rsi": 0}

        if signal == "WAIT":
            return 0, detail

        # ── Trend (30) ────────────────────────────────────────────────────────
        if (signal == "BUY" and trend_bull) or (signal == "SELL" and trend_bear):
            detail["trend"] = SCORE_WEIGHTS["trend"]
        elif trend_bull or trend_bear:
            detail["trend"] = 15  # tendance présente mais pas alignée

        # ── RR (25) ───────────────────────────────────────────────────────────
        min_rr = REJECTION_THRESHOLDS.get(style or "day", {}).get("min_rr", 1.5)
        if rr is not None:
            if rr >= 2.0:
                detail["rr"] = SCORE_WEIGHTS["rr"]
            elif rr >= min_rr:
                detail["rr"] = 15

        # ── S/R (20) — graduel ────────────────────────────────────────────────
        if signal == "BUY":
            if resistance is not None and resistance > price and tp1 > price:
                dist_to_tp = tp1 - price
                dist_to_sr = resistance - price
                ratio = dist_to_sr / dist_to_tp if dist_to_tp > 0 else 0
                if ratio >= 0.8:
                    detail["sr"] = 20
                elif ratio >= 0.5:
                    detail["sr"] = 10
                # else 0 : résistance trop proche, bloque le TP
            else:
                # Pas de résistance gênante connue → bonus complet
                detail["sr"] = 20 if (support is not None or resistance is not None) else 0

        elif signal == "SELL":
            if support is not None and support < price and tp1 < price:
                dist_to_tp = price - tp1
                dist_to_sr = price - support
                ratio = dist_to_sr / dist_to_tp if dist_to_tp > 0 else 0
                if ratio >= 0.8:
                    detail["sr"] = 20
                elif ratio >= 0.5:
                    detail["sr"] = 10
            else:
                detail["sr"] = 20 if (support is not None or resistance is not None) else 0

        # ── ADX (15) ─────────────────────────────────────────────────────────
        if adx_val >= 30:
            detail["adx"] = SCORE_WEIGHTS["adx"]
        elif adx_val >= 25:
            detail["adx"] = 10

        # ── RSI (10) ─────────────────────────────────────────────────────────
        if 40 <= rsi_val <= 60:
            detail["rsi"] = SCORE_WEIGHTS["rsi"]
        elif 30 <= rsi_val <= 70:
            detail["rsi"] = 5

        return sum(detail.values()), detail

    @staticmethod
    def _finalize(
        buy_cond: list,
        sell_cond: list,
        price: float,
        atr_val: float,
        indicators: Dict,
        lang: str,
        min_cond: int = 4,
        cfg: Optional[Dict] = None,
        support: Optional[float] = None,
        resistance: Optional[float] = None,
        rsi_val: float = 50,
        adx_val: float = 20,
        trend_bull: bool = False,
        trend_bear: bool = False,
        style: Optional[str] = "day",
    ) -> Dict:
        """
        Finalise le signal : SL/TP, scoring pondéré, filtres de rejet.

        Toutes les étapes sont indépendantes et testables séparément.
        """
        buy_count  = sum(buy_cond)
        sell_count = sum(sell_cond)

        # ── 1. Détermination du signal brut ───────────────────────────────────
        signal = "WAIT"
        if buy_count >= min_cond:
            signal = "BUY"
        elif sell_count >= min_cond:
            signal = "SELL"

        # Signal WAIT direct (pas assez de conditions)
        if signal == "WAIT":
            return SignalEngine._wait(
                lang,
                reason_key="signal_wait_neutral",
                indicators=indicators,
                score_detail={},
            )

        # ── 2. Calcul SL/TP selon le style ────────────────────────────────────
        sl, tp1 = SignalEngine._compute_sl_tp(signal, price, atr_val, style)

        # ── 3. Ajustement S/R ─────────────────────────────────────────────────
        if atr_val > 0:
            sl, tp1 = SignalEngine._adjust_sl_tp_with_sr(
                signal, price, sl, tp1, atr_val, support, resistance, style
            )

        tp  = tp1
        tp2 = tp1 + (atr_val if signal == "BUY" else -atr_val)

        # ── 4. Ratio RR ───────────────────────────────────────────────────────
        rr: Optional[float] = None
        if sl is not None and tp1 is not None and abs(price - sl) > 0:
            rr = round(abs(tp1 - price) / abs(price - sl), 2)

        # ── 5. Score pondéré ─────────────────────────────────────────────────
        total_score, score_detail = SignalEngine._compute_score(
            signal=signal,
            price=price,
            tp1=tp1,
            rr=rr,
            adx_val=adx_val,
            rsi_val=rsi_val,
            trend_bull=trend_bull,
            trend_bear=trend_bear,
            support=support,
            resistance=resistance,
            style=style,
        )

        # ── 6. Filtres de rejet (retourne WAIT avec indicateurs conservés) ────
        thresholds = REJECTION_THRESHOLDS.get(style or "day", REJECTION_THRESHOLDS["day"])

        if adx_val < thresholds["min_adx"]:
            return SignalEngine._wait(
                lang,
                reason_key=f"Trend too weak — ADX {adx_val:.1f} < {thresholds['min_adx']}",
                indicators=indicators,
                score_detail=score_detail,
            )

        if rr is not None and rr < thresholds["min_rr"]:
            return SignalEngine._wait(
                lang,
                reason_key=f"RR too low — {rr:.2f} < {thresholds['min_rr']} required for {style or 'default'} style",
                indicators=indicators,
                score_detail=score_detail,
            )

        if total_score < thresholds["min_score"]:
            return SignalEngine._wait(
                lang,
                reason_key=f"Score too low — {total_score}/100 < {thresholds['min_score']} required",
                indicators=indicators,
                score_detail=score_detail,
            )

        # ── 7. Textes i18n ────────────────────────────────────────────────────
        reason   = get_text(lang, f"signal_{signal.lower()}_reason")
        risk     = get_text(lang, f"signal_{signal.lower()}_advice")
        conf_key = (
            "confidence_high"   if total_score >= 75 else
            "confidence_medium" if total_score >= 55 else
            "confidence_low"
        )

        # ── 8. Retour final ───────────────────────────────────────────────────
        return {
            "signal":      signal,
            "signal_text": get_text(lang, f"signal_{signal.lower()}"),
            "reason":      reason,
            "risk_advice": risk,
            "teddy_score": min(total_score, 95),
            "confidence":  get_text(lang, conf_key),
            "sl":          sl,
            "tp":          tp,
            "tp1":         tp1,
            "tp2":         tp2,
            "rr_ratio":    rr,
            "indicators":  indicators,
            "score_detail": score_detail,
        }