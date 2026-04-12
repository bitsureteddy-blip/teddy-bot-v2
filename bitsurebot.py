#!/usr/bin/env python3
"""
Bitsure Teddy - Professional Trading Signals Bot
Version finale stable - Données quotidiennes, FCS + Yahoo fallback.
Déploiement Railway : TELEGRAM_TOKEN, FCS_API_KEY, REALMARKET_API_KEY
"""

import os
import re
import time
import json
import logging
import threading
from io import BytesIO
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd
import requests
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from websocket import WebSocketApp
except Exception:
    WebSocketApp = None

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("BitsureTeddy")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FCS_API_KEY = os.environ.get("FCS_API_KEY")
REALMARKET_API_KEY = os.environ.get("REALMARKET_API_KEY")
FCS_BASE_URL = "https://fcsapi.com/api-v4"

HISTORY_PERIOD = "2mo"
HISTORY_INTERVAL = "1d"
REALTIME_FRESH_SECONDS = 120
PRICE_CACHE_TTL = 15
HISTORY_CACHE_TTL = 300
MAX_WEBSOCKET_RETRY_DELAY = 30

ADMIN_IDS = {8376348929}

COMMON_CRYPTO_BASES = {"BTC", "ETH", "XRP", "LTC", "BCH", "ADA", "SOL", "DOGE", "AVAX", "LINK", "MATIC"}
COMMON_FOREX_QUOTES = {"USD", "JPY", "EUR", "GBP", "CHF", "CAD", "AUD", "NZD", "BIF"}
COMMODITY_CODES = {"XAUUSD", "XAGUSD", "WTI", "BRENT", "OIL", "USOIL", "UKOIL"}

# ------------------------------------------------------------------
# Global State
# ------------------------------------------------------------------

realtime_prices: Dict[str, Dict[str, Any]] = {}
realtime_lock = threading.Lock()
_price_cache: Dict[str, Dict[str, Any]] = {}
_history_cache: Dict[str, Dict[str, Any]] = {}
_started_ws_symbols: set = set()
_ws_lock = threading.Lock()

# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def now_ts() -> float:
    return time.time()

def clean_symbol(raw: str) -> str:
    return re.sub(r"\s+", "", raw.strip().upper())

def safe_float(val: Any) -> Optional[float]:
    try:
        return float(val) if val and (not isinstance(val, str) or val.strip()) else None
    except:
        return None

def is_forex_like(symbol: str) -> bool:
    s = clean_symbol(symbol).replace("=X", "")
    return len(s) == 6 and s[:3].isalpha() and s[3:] in COMMON_FOREX_QUOTES

def is_crypto_like(symbol: str) -> bool:
    s = clean_symbol(symbol).replace("-", "").replace("_", "").replace("USD", "")
    return s in COMMON_CRYPTO_BASES

def is_commodity_like(symbol: str) -> bool:
    s = clean_symbol(symbol)
    return s in COMMODITY_CODES or s.startswith("XAU") or s.startswith("XAG")

def market_class(symbol: str) -> str:
    if is_forex_like(symbol): return "forex"
    if is_commodity_like(symbol): return "commodity"
    if is_crypto_like(symbol): return "crypto"
    return "stock"

def realmarket_symbol(symbol: str) -> str:
    return clean_symbol(symbol).replace("=X", "").replace("-", "").replace("/", "")

# ------------------------------------------------------------------
# Data Sources
# ------------------------------------------------------------------

def get_fcs_history(symbol: str) -> pd.DataFrame:
    if not FCS_API_KEY: return pd.DataFrame()
    params = {"access_key": FCS_API_KEY, "symbol": realmarket_symbol(symbol), "period": "1D"}
    cls = market_class(symbol)
    if cls == "commodity": params["type"] = "commodity"
    elif cls == "crypto": params["type"] = "crypto"
    elif cls == "forex": params["synthetic"] = "1"
    try:
        resp = requests.get(f"{FCS_BASE_URL}/forex/history", params=params, timeout=15)
        if resp.status_code != 200: return pd.DataFrame()
        data = resp.json()
        if data.get("code") != 200: return pd.DataFrame()
        rows = []
        for item in data.get("response", []):
            c = safe_float(item.get("c"))
            if c:
                rows.append({
                    "Open": safe_float(item.get("o")) or c,
                    "High": safe_float(item.get("h")) or c,
                    "Low": safe_float(item.get("l")) or c,
                    "Close": c,
                    "Volume": 0
                })
        return pd.DataFrame(rows).dropna() if rows else pd.DataFrame()
    except Exception as e:
        logger.warning(f"FCS history error: {e}")
        return pd.DataFrame()

def get_yahoo_history(symbol: str) -> pd.DataFrame:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=HISTORY_PERIOD, interval=HISTORY_INTERVAL)
        if df.empty: return pd.DataFrame()
        df = df.rename(columns={"Open": "Open", "High": "High", "Low": "Low", "Close": "Close", "Volume": "Volume"})
        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except:
        return pd.DataFrame()

def get_history(symbol: str) -> pd.DataFrame:
    symbol_clean = clean_symbol(symbol)
    cached = _history_cache.get(symbol_clean)
    if cached and now_ts() - cached["ts"] <= HISTORY_CACHE_TTL:
        return cached["df"].copy()
    
    # Essayer FCS d'abord pour forex/commodities/crypto
    if market_class(symbol_clean) != "stock":
        df = get_fcs_history(symbol_clean)
        if not df.empty and len(df) >= 20:
            _history_cache[symbol_clean] = {"ts": now_ts(), "df": df.copy()}
            return df
    
    # Fallback Yahoo
    df = get_yahoo_history(symbol_clean)
    if not df.empty and len(df) >= 20:
        _history_cache[symbol_clean] = {"ts": now_ts(), "df": df.copy()}
        return df
    
    return pd.DataFrame()

def get_fcs_price(symbol: str) -> Optional[float]:
    if not FCS_API_KEY: return None
    params = {"access_key": FCS_API_KEY, "symbol": realmarket_symbol(symbol)}
    cls = market_class(symbol)
    if cls == "commodity": params["type"] = "commodity"
    elif cls == "crypto": params["type"] = "crypto"
    elif cls == "forex": params["synthetic"] = "1"
    try:
        resp = requests.get(f"{FCS_BASE_URL}/forex/latest", params=params, timeout=10)
        if resp.status_code != 200: return None
        data = resp.json()
        if data.get("code") != 200: return None
        for item in data.get("response", []):
            p = safe_float(item.get("c"))
            if p: return p
    except:
        pass
    return None

def get_yahoo_price(symbol: str) -> Optional[float]:
    try:
        ticker = yf.Ticker(symbol)
        return safe_float(ticker.fast_info.last_price) or safe_float(ticker.history(period="1d")["Close"].iloc[-1])
    except:
        return None

def get_current_price(symbol: str) -> Tuple[Optional[float], str]:
    symbol_clean = clean_symbol(symbol)
    cached = _price_cache.get(symbol_clean)
    if cached and now_ts() - cached["ts"] <= PRICE_CACHE_TTL:
        return cached["price"], cached.get("source", "cache")
    
    # WebSocket
    with realtime_lock:
        data = realtime_prices.get(realmarket_symbol(symbol_clean))
        if data and now_ts() - data["ts"] <= REALTIME_FRESH_SECONDS:
            p = data["price"]
            _price_cache[symbol_clean] = {"ts": now_ts(), "price": p, "source": "real-time"}
            return p, "real-time"
    
    # FCS
    p = get_fcs_price(symbol_clean)
    if p:
        _price_cache[symbol_clean] = {"ts": now_ts(), "price": p, "source": "fcs"}
        return p, "fcs"
    
    # Yahoo
    p = get_yahoo_price(symbol_clean)
    if p:
        _price_cache[symbol_clean] = {"ts": now_ts(), "price": p, "source": "yahoo"}
        return p, "yahoo"
    
    return None, "none"

# ------------------------------------------------------------------
# WebSocket
# ------------------------------------------------------------------

def start_realtime_feed(symbol: str):
    if not REALMARKET_API_KEY or WebSocketApp is None: return
    sym = realmarket_symbol(symbol)
    with _ws_lock:
        if sym in _started_ws_symbols: return
        _started_ws_symbols.add(sym)
    threading.Thread(target=_ws_worker, args=(sym,), daemon=True).start()

def _ws_worker(symbol: str):
    delay = 1.0
    while True:
        try:
            def on_message(ws, msg):
                try:
                    data = json.loads(msg)
                    candle = data[0] if isinstance(data, list) else data
                    p = safe_float(candle.get("ClosePrice") or candle.get("close") or candle.get("c"))
                    if p:
                        with realtime_lock:
                            realtime_prices[symbol] = {"price": p, "ts": now_ts()}
                except: pass
            ws = WebSocketApp(
                f"wss://api.realmarketapi.com/price?apiKey={REALMARKET_API_KEY}&symbolCode={symbol}&timeFrame=M1",
                on_message=on_message
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except: pass
        time.sleep(delay)
        delay = min(delay * 2, MAX_WEBSOCKET_RETRY_DELAY)

# ------------------------------------------------------------------
# Indicators
# ------------------------------------------------------------------

def compute_sma(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w).mean()

def compute_rsi(s: pd.Series, p: int = 14) -> pd.Series:
    delta = s.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/p, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/p, adjust=False).mean()
    return 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

def compute_macd(s: pd.Series):
    e12 = s.ewm(span=12, adjust=False).mean()
    e26 = s.ewm(span=26, adjust=False).mean()
    macd = e12 - e26
    sig = macd.ewm(span=9, adjust=False).mean()
    return macd, sig, macd - sig

def compute_bollinger(s: pd.Series, w: int = 20):
    sma = s.rolling(w).mean()
    std = s.rolling(w).std()
    return sma + 2*std, sma, sma - 2*std

def detect_divergence(p: pd.Series, r: pd.Series, lb: int = 5) -> Optional[str]:
    if len(p) < lb: return None
    pv, rv = p.iloc[-lb:].values, r.iloc[-lb:].values
    if pv[-1] < pv[0] and rv[-1] > rv[0]: return "bullish"
    if pv[-1] > pv[0] and rv[-1] < rv[0]: return "bearish"
    return None

def generate_signal(df: pd.DataFrame) -> Tuple[str, str, Dict[str, Any]]:
    close = df["Close"]
    rsi = compute_rsi(close)
    macd, sig, hist = compute_macd(close)
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    upper, mid, lower = compute_bollinger(close)
    
    last = close.iloc[-1]
    last_rsi = rsi.iloc[-1]
    last_macd, prev_macd = macd.iloc[-1], macd.iloc[-2]
    last_sig, prev_sig = sig.iloc[-1], sig.iloc[-2]
    last_hist = hist.iloc[-1]
    
    support, resistance = close.tail(50).min(), close.tail(50).max()
    div = detect_divergence(close, rsi)
    
    signal = "ATTENDRE"
    advice = "📊 No clear signal – wait for better setup"
    
    if div == "bullish":
        signal, advice = "ACHETER", "🔥 Bullish divergence"
    elif div == "bearish":
        signal, advice = "VENDRE", "🔥 Bearish divergence"
    elif last_rsi < 30 and last_hist > 0:
        signal, advice = "ACHETER", "RSI oversold & MACD turning up"
    elif last_rsi > 70 and last_hist < 0:
        signal, advice = "VENDRE", "RSI overbought & MACD turning down"
    elif last <= support * 1.01 and last_rsi < 40:
        signal, advice = "ACHETER", "Price near support, RSI low"
    elif last >= resistance * 0.99 and last_rsi > 60:
        signal, advice = "VENDRE", "Price near resistance, RSI high"
    elif prev_macd < prev_sig and last_macd > last_sig:
        signal, advice = "ACHETER", "MACD bullish crossover"
    elif prev_macd > prev_sig and last_macd < last_sig:
        signal, advice = "VENDRE", "MACD bearish crossover"
    elif last > sma20.iloc[-1] > sma50.iloc[-1] and last_rsi < 50:
        signal, advice = "ACHETER", "Bullish trend pullback"
    elif last < sma20.iloc[-1] < sma50.iloc[-1] and last_rsi > 50:
        signal, advice = "VENDRE", "Bearish trend pullback"
    
    details = {
        "price": last, "rsi": round(last_rsi, 2),
        "macd": round(last_macd, 4), "signal": round(last_sig, 4),
        "histogram": round(last_hist, 4),
        "sma20": round(sma20.iloc[-1], 4), "sma50": round(sma50.iloc[-1], 4),
        "support": round(support, 4), "resistance": round(resistance, 4)
    }
    return signal, advice, details

def generate_chart(df: pd.DataFrame, symbol: str) -> BytesIO:
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5))
    close = df["Close"]
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    upper, mid, lower = compute_bollinger(close)
    x = range(len(close))
    ax.plot(x, close, 'white', linewidth=1.5, label='Price')
    ax.plot(x, sma20, 'orange', linestyle='--', alpha=0.8, label='SMA20')
    ax.plot(x, sma50, 'cyan', linestyle='--', alpha=0.8, label='SMA50')
    ax.plot(x, upper, 'gray', linestyle=':', alpha=0.5)
    ax.plot(x, lower, 'gray', linestyle=':', alpha=0.5)
    ax.fill_between(x, lower, upper, color='gray', alpha=0.1)
    ax.set_title(f"{symbol} – Daily Chart", color='white')
    ax.set_xlabel("Days ago")
    ax.legend(loc='upper left')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    return buf

# ------------------------------------------------------------------
# Telegram Handlers
# ------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 **Bitsure Teddy**\n/help for commands", parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "**Commands**\n"
        "/analyse SYMBOL – Full analysis + chart\n"
        "/price SYMBOL – Real-time price\n"
        "/trend SYMBOL – Trend direction\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /price SYMBOL")
        return
    symbol = context.args[0].strip()
    price, source = get_current_price(symbol)
    if price:
        await update.message.reply_text(f"💰 {symbol.upper()}: {price:.4f} ({source})")
    else:
        await update.message.reply_text(f"❌ {symbol} not found")

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /analyse SYMBOL")
        return
    symbol = context.args[0].strip()
    await update.message.chat.send_action("typing")
    
    df = get_history(symbol)
    if df.empty or len(df) < 20:
        await update.message.reply_text(f"❌ {symbol} not found or insufficient data")
        return
    
    signal, advice, details = generate_signal(df)
    live_price, source = get_current_price(symbol)
    if not live_price:
        live_price, source = details["price"], "close"
    
    msg = (
        f"📊 **{symbol.upper()}**\n"
        f"💰 {live_price:.4f} ({source})\n"
        f"📈 RSI: {details['rsi']}\n"
        f"📉 MACD: {details['macd']} | Sig: {details['signal']}\n"
        f"📊 SMA20: {details['sma20']} | SMA50: {details['sma50']}\n"
        f"🛡️ S: {details['support']} | R: {details['resistance']}\n\n"
        f"🚦 **{signal}**\n💡 {advice}"
    )
    
    chart = generate_chart(df, symbol)
    await update.message.reply_photo(chart, caption=msg, parse_mode="Markdown")

async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    symbol = context.args[0].strip()
    df = get_history(symbol)
    if df.empty:
        await update.message.reply_text(f"❌ {symbol} not found")
        return
    close = df["Close"]
    sma20 = compute_sma(close, 20).iloc[-1]
    sma50 = compute_sma(close, 50).iloc[-1]
    last = close.iloc[-1]
    if last > sma20 > sma50:
        t = "📈 Strong Uptrend"
    elif last < sma20 < sma50:
        t = "📉 Strong Downtrend"
    else:
        t = "↔️ Neutral"
    await update.message.reply_text(f"**{symbol}**: {t}", parse_mode="Markdown")

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = f"🆔 `{uid}`"
    if uid in ADMIN_IDS:
        msg += "\n👑 Admin"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN missing")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("analyse", analyse))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("trend", trend))
    app.add_handler(CommandHandler("myid", myid))
    
    logger.info("Bitsure Teddy starting...")
    app.run_polling()

if __name__ == "__main__":
    main()