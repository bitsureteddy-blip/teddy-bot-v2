#!/usr/bin/env python3
"""
Bitsure Teddy - Professional Trading Signals Bot
v2.5 - STABLE DAILY ANALYSIS
Deploy on Railway with environment variables and /data volume.
"""

import os
import re
import time
import json
import logging
import asyncio
import threading
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any, Set

import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from websocket import WebSocketApp

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("BitsureTeddy")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FCS_API_KEY = os.environ.get("FCS_API_KEY")
REALMARKET_API_KEY = os.environ.get("REALMARKET_API_KEY")

# DAILY DATA ONLY - RELIABLE
HISTORY_PERIOD = "2mo"
HISTORY_INTERVAL = "1d"
PRICE_CACHE_TTL = 15
HISTORY_CACHE_TTL = 300
MAX_WEBSOCKET_RETRY_DELAY = 30

FREE_DAILY_LIMIT = 10

DATA_DIR = os.environ.get("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlists.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
USAGE_FILE = os.path.join(DATA_DIR, "usage.json")

ADMIN_IDS = {8376348929}

# ------------------------------------------------------------------
# Global State
# ------------------------------------------------------------------

realtime_prices: Dict[str, Dict[str, Any]] = {}
realtime_lock = threading.Lock()
_price_cache: Dict[str, Dict[str, Any]] = {}
_history_cache: Dict[str, Dict[str, Any]] = {}
_started_ws_symbols: Set[str] = set()
_ws_lock = threading.Lock()
tick_history: Dict[str, List[Dict[str, Any]]] = {}
tick_lock = threading.Lock()

user_alerts: Dict[str, List[Dict[str, Any]]] = {}
user_watchlists: Dict[str, List[str]] = {}
user_settings: Dict[str, Dict[str, Any]] = {}
user_usage: Dict[str, Dict[str, Any]] = {}

# ------------------------------------------------------------------
# JSON Helpers
# ------------------------------------------------------------------

def load_json(path: str, default: Any) -> Any:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return default

def save_json(path: str, data: Any):
    try:
        with open(path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Save failed {path}: {e}")

def load_all_user_data():
    global user_alerts, user_watchlists, user_settings, user_usage
    user_alerts = load_json(ALERTS_FILE, {})
    user_watchlists = load_json(WATCHLIST_FILE, {})
    user_settings = load_json(SETTINGS_FILE, {})
    user_usage = load_json(USAGE_FILE, {})

# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def now_ts() -> float:
    return time.time()

def clean_symbol(raw: str) -> str:
    return re.sub(r"\s+", "", raw.strip().upper())

def safe_float(val: Any) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except:
        return None

def realmarket_symbol(symbol: str) -> str:
    return clean_symbol(symbol).replace("=X", "").replace("-", "").replace("/", "")

# ------------------------------------------------------------------
# FCS API - UNIQUE DATA SOURCE
# ------------------------------------------------------------------

def get_fcs_history(symbol: str) -> pd.DataFrame:
    """Fetch daily history from FCS API."""
    if not FCS_API_KEY:
        return pd.DataFrame()
    
    params = {
        "access_key": FCS_API_KEY,
        "symbol": realmarket_symbol(symbol),
        "period": "1D"
    }
    
    # Detect market type
    s = clean_symbol(symbol)
    if s in {"XAUUSD", "XAGUSD"} or s.startswith("X"):
        params["type"] = "commodity"
    elif any(c in s for c in ["BTC", "ETH", "USDT"]):
        params["type"] = "crypto"
    else:
        params["synthetic"] = "1"  # forex
    
    try:
        resp = requests.get("https://fcsapi.com/api-v4/forex/history", params=params, timeout=15)
        if resp.status_code != 200:
            return pd.DataFrame()
        data = resp.json()
        if data.get("code") != 200:
            return pd.DataFrame()
        
        records = data.get("response", [])
        if not records:
            return pd.DataFrame()
        
        rows = []
        for item in records:
            c = safe_float(item.get("c"))
            if c:
                rows.append({
                    "Open": safe_float(item.get("o")) or c,
                    "High": safe_float(item.get("h")) or c,
                    "Low": safe_float(item.get("l")) or c,
                    "Close": c,
                    "Volume": 0
                })
        
        if rows:
            df = pd.DataFrame(rows)
            return df[["Open","High","Low","Close","Volume"]].dropna()
    except Exception as e:
        logger.warning(f"FCS history error: {e}")
    
    return pd.DataFrame()

def get_history(symbol: str) -> pd.DataFrame:
    symbol_clean = clean_symbol(symbol)
    cached = _history_cache.get(symbol_clean)
    if cached and now_ts() - cached["ts"] <= HISTORY_CACHE_TTL:
        return cached["df"].copy()
    
    df = get_fcs_history(symbol_clean)
    if not df.empty and len(df) >= 20:
        _history_cache[symbol_clean] = {"ts": now_ts(), "df": df.copy()}
        return df
    
    return pd.DataFrame()

def get_fcs_price(symbol: str) -> Optional[float]:
    if not FCS_API_KEY:
        return None
    
    params = {"access_key": FCS_API_KEY, "symbol": realmarket_symbol(symbol)}
    s = clean_symbol(symbol)
    if s in {"XAUUSD", "XAGUSD"}:
        params["type"] = "commodity"
    elif any(c in s for c in ["BTC", "ETH"]):
        params["type"] = "crypto"
    else:
        params["synthetic"] = "1"
    
    try:
        resp = requests.get("https://fcsapi.com/api-v4/forex/latest", params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                for item in data.get("response", []):
                    p = safe_float(item.get("c"))
                    if p:
                        return p
    except Exception as e:
        logger.warning(f"FCS price error: {e}")
    return None

def get_current_price(symbol: str) -> Tuple[Optional[float], str]:
    symbol_clean = clean_symbol(symbol)
    cached = _price_cache.get(symbol_clean)
    if cached and now_ts() - cached["ts"] <= PRICE_CACHE_TTL:
        return cached["price"], cached.get("source", "cache")
    
    # Try WebSocket
    with realtime_lock:
        data = realtime_prices.get(realmarket_symbol(symbol_clean))
        if data and now_ts() - data["ts"] <= 120:
            p = data["price"]
            _price_cache[symbol_clean] = {"ts": now_ts(), "price": p, "source": "real-time"}
            return p, "real-time"
    
    # Try FCS
    p = get_fcs_price(symbol_clean)
    if p:
        _price_cache[symbol_clean] = {"ts": now_ts(), "price": p, "source": "fcs"}
        return p, "fcs"
    
    return None, "none"

# ------------------------------------------------------------------
# WebSocket
# ------------------------------------------------------------------

def start_realtime_feed(symbol: str):
    if not REALMARKET_API_KEY:
        return
    sym = realmarket_symbol(symbol)
    with _ws_lock:
        if sym in _started_ws_symbols:
            return
        _started_ws_symbols.add(sym)
    threading.Thread(target=_realtime_worker, args=(sym,), daemon=True).start()

def _realtime_worker(symbol: str):
    delay = 1.0
    while True:
        try:
            ws = WebSocketApp(
                f"wss://api.realmarketapi.com/price?apiKey={REALMARKET_API_KEY}&symbolCode={symbol}&timeFrame=M1",
                on_message=lambda w, m: _on_ws_message(symbol, m)
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except:
            pass
        time.sleep(delay)
        delay = min(delay * 2, MAX_WEBSOCKET_RETRY_DELAY)

def _on_ws_message(symbol: str, msg: str):
    try:
        data = json.loads(msg)
        candle = data[0] if isinstance(data, list) else data
        price = safe_float(candle.get("ClosePrice") or candle.get("close") or candle.get("c"))
        if price:
            ts = now_ts()
            with realtime_lock:
                realtime_prices[symbol] = {"price": price, "ts": ts}
            with tick_lock:
                if symbol not in tick_history:
                    tick_history[symbol] = []
                tick_history[symbol].append({"ts": ts, "price": price})
                tick_history[symbol] = [t for t in tick_history[symbol] if ts - t["ts"] <= 120]
    except:
        pass

# ------------------------------------------------------------------
# Technical Indicators
# ------------------------------------------------------------------

def compute_sma(series: pd.Series, w: int) -> pd.Series:
    return series.rolling(w).mean()

def compute_rsi(series: pd.Series, p: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/p, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/p, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series):
    e12 = series.ewm(span=12, adjust=False).mean()
    e26 = series.ewm(span=26, adjust=False).mean()
    macd = e12 - e26
    sig = macd.ewm(span=9, adjust=False).mean()
    return macd, sig, macd - sig

def compute_bollinger(series: pd.Series, w: int = 20):
    sma = series.rolling(w).mean()
    std = series.rolling(w).std()
    return sma + 2*std, sma, sma - 2*std

def detect_divergence(prices: pd.Series, rsi: pd.Series, lookback: int = 5) -> Optional[str]:
    if len(prices) < lookback:
        return None
    p = prices.iloc[-lookback:].values
    r = rsi.iloc[-lookback:].values
    if p[-1] < p[0] and r[-1] > r[0]:
        return "bullish"
    if p[-1] > p[0] and r[-1] < r[0]:
        return "bearish"
    return None

def generate_signal(df: pd.DataFrame) -> Tuple[str, str, Dict[str, Any], int]:
    close = df["Close"]
    rsi = compute_rsi(close)
    macd, sig, hist = compute_macd(close)
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    
    last = close.iloc[-1]
    last_rsi = rsi.iloc[-1]
    last_macd = macd.iloc[-1]
    last_sig = sig.iloc[-1]
    last_hist = hist.iloc[-1]
    prev_macd = macd.iloc[-2] if len(macd) > 1 else last_macd
    prev_sig = sig.iloc[-2] if len(sig) > 1 else last_sig
    
    support = close.tail(50).min()
    resistance = close.tail(50).max()
    div = detect_divergence(close, rsi)
    
    signal_out = "ATTENDRE"
    advice = "📊 No clear signal – wait for better setup"
    extra_tip = ""
    
    if div == "bullish":
        signal_out, advice = "ACHETER", "🔥 Bullish divergence"
    elif div == "bearish":
        signal_out, advice = "VENDRE", "🔥 Bearish divergence"
    elif last_rsi < 30 and last_hist > 0:
        signal_out, advice = "ACHETER", "RSI oversold & MACD turning up"
    elif last_rsi > 70 and last_hist < 0:
        signal_out, advice = "VENDRE", "RSI overbought & MACD turning down"
    elif last <= support * 1.01 and last_rsi < 40:
        signal_out, advice = "ACHETER", "Price near support, RSI low"
    elif last >= resistance * 0.99 and last_rsi > 60:
        signal_out, advice = "VENDRE", "Price near resistance, RSI high"
    elif prev_macd < prev_sig and last_macd > last_sig:
        signal_out, advice = "ACHETER", "MACD bullish crossover"
    elif prev_macd > prev_sig and last_macd < last_sig:
        signal_out, advice = "VENDRE", "MACD bearish crossover"
    elif last > sma20.iloc[-1] > sma50.iloc[-1] and last_rsi < 50:
        signal_out, advice = "ACHETER", "Bullish trend pullback"
    elif last < sma20.iloc[-1] < sma50.iloc[-1] and last_rsi > 50:
        signal_out, advice = "VENDRE", "Bearish trend pullback"
    
    if signal_out != "ATTENDRE":
        extra_tip = "✅ Good entry point" if 40 <= last_rsi <= 60 else ("📈 Bounce zone likely" if last_rsi < 30 else "⚠️ Wait for pullback")
    
    # Teddy Score
    score = 50
    if last_rsi < 30: score += 15
    elif last_rsi > 70: score -= 15
    if last > sma20.iloc[-1] > sma50.iloc[-1]: score += 10
    elif last < sma20.iloc[-1] < sma50.iloc[-1]: score -= 10
    if div: score += 15 if signal_out == "ACHETER" else -15
    score = max(0, min(100, score))
    
    details = {
        "price": last, "rsi": round(last_rsi, 2),
        "macd": round(last_macd, 4), "signal": round(last_sig, 4),
        "histogram": round(last_hist, 4),
        "sma20": round(sma20.iloc[-1], 4), "sma50": round(sma50.iloc[-1], 4),
        "support": round(support, 4), "resistance": round(resistance, 4)
    }
    
    return signal_out, f"{advice}\n📌 {extra_tip}", details, score

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
    ax.set_ylabel("Price")
    ax.legend(loc='upper left')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

# ------------------------------------------------------------------
# Telegram Handlers
# ------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🤖 **Bitsure Teddy**\nDaily analysis. /help for commands.\n⚠️ Free: {FREE_DAILY_LIMIT}/day", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 **Commands**\n\n"
        "/analyse SYMBOL – Full analysis + chart\n/price SYMBOL – Real-time price\n"
        "/trend SYMBOL – Trend\n/volatility SYMBOL – ATR\n/levels SYMBOL – S/R levels\n"
        "/scalp SYMBOL SECONDS – Micro trend (3,5,10,20)\n/tick SYMBOL\n\n"
        "/alert SYMBOL above/below PRICE\n/alerts\n/delalert ID\n/clearalerts\n\n"
        "/watchlist\n/addwatch SYMBOL\n/removewatch SYMBOL\n/scan\n\n"
        "/settings\n/usage\n/status\n/about\n/myid"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /price SYMBOL")
        return
    symbol = context.args[0].strip()
    price, source = get_current_price(symbol)
    if price:
        await update.message.reply_text(f"💰 {symbol.upper()}: {price:.4f} ({source})")
    else:
        await update.message.reply_text(f"❌ {symbol} not found")

async def analyse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /analyse SYMBOL")
        return
    symbol = context.args[0].strip()
    await update.message.chat.send_action("typing")
    
    df = get_history(symbol)
    if df.empty or len(df) < 20:
        await update.message.reply_text(f"❌ {symbol} not found or insufficient data")
        return
    
    signal, advice, details, score = generate_signal(df)
    live_price, source = get_current_price(symbol)
    if not live_price:
        live_price = details["price"]
        source = "close"
    
    msg = (
        f"📊 **{symbol.upper()}**\n💰 {live_price:.4f} ({source})\n"
        f"📈 RSI: {details['rsi']}\n📉 MACD: {details['macd']} | Sig: {details['signal']}\n"
        f"📊 SMA20: {details['sma20']} | SMA50: {details['sma50']}\n"
        f"🛡️ S: {details['support']} | R: {details['resistance']}\n\n"
        f"🚦 **{signal}**\n💡 {advice}\n\n🏆 Teddy Score: {score}/100"
    )
    
    chart = generate_chart(df, symbol)
    await update.message.reply_photo(chart, caption=msg, parse_mode="Markdown")

async def trend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    df = get_history(context.args[0])
    if df.empty:
        await update.message.reply_text("❌ Not found")
        return
    close = df["Close"]
    sma20 = compute_sma(close, 20).iloc[-1]
    sma50 = compute_sma(close, 50).iloc[-1]
    last = close.iloc[-1]
    trend = "📈 Uptrend" if last > sma20 > sma50 else "📉 Downtrend" if last < sma20 < sma50 else "↔️ Neutral"
    await update.message.reply_text(f"{trend}")

async def scalp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return
    symbol = context.args[0]
    try:
        dur = int(context.args[1])
    except:
        return
    start_realtime_feed(symbol)
    await asyncio.sleep(1)
    with tick_lock:
        ticks = [t for t in tick_history.get(realmarket_symbol(symbol), []) if now_ts() - t["ts"] <= dur]
    if len(ticks) < 3:
        await update.message.reply_text("⚠️ Not enough ticks")
        return
    prices = [t["price"] for t in ticks]
    var = ((prices[-1] - prices[0]) / prices[0]) * 100
    await update.message.reply_text(f"⚡ {symbol}: {var:+.2f}% in {dur}s")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        return
    sym, cond, target = context.args[0].upper(), context.args[1].lower(), float(context.args[2])
    chat_id = str(update.effective_chat.id)
    alert = {"id": int(time.time()*1000)%1000000, "symbol": sym, "condition": cond, "target": target}
    user_alerts.setdefault(chat_id, []).append(alert)
    save_json(ALERTS_FILE, user_alerts)
    await update.message.reply_text(f"✅ Alert set: {sym} {cond} {target}")

async def list_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alerts = user_alerts.get(str(update.effective_chat.id), [])
    if not alerts:
        await update.message.reply_text("📭 No alerts")
        return
    msg = "\n".join(f"ID {a['id']}: {a['symbol']} {a['condition']} {a['target']}" for a in alerts)
    await update.message.reply_text(msg)

async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, alerts in list(user_alerts.items()):
        for alert in alerts[:]:
            price, _ = get_current_price(alert["symbol"])
            if price and ((alert["condition"]=="above" and price>=alert["target"]) or (alert["condition"]=="below" and price<=alert["target"])):
                try:
                    await context.bot.send_message(int(chat_id), f"🚨 {alert['symbol']} {alert['condition']} {alert['target']} @ {price:.4f}")
                except:
                    pass
                user_alerts[chat_id].remove(alert)
                save_json(ALERTS_FILE, user_alerts)

async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wl = user_watchlists.get(str(update.effective_chat.id), [])
    if not wl:
        await update.message.reply_text("📭 Empty")
        return
    msg = "\n".join(f"{s}: {get_current_price(s)[0]:.4f}" if get_current_price(s)[0] else f"{s}: N/A" for s in wl)
    await update.message.reply_text(msg)

async def addwatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    chat_id = str(update.effective_chat.id)
    sym = context.args[0].upper()
    user_watchlists.setdefault(chat_id, []).append(sym)
    save_json(WATCHLIST_FILE, user_watchlists)
    await update.message.reply_text(f"✅ {sym} added")

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = f"🆔 `{user.id}`"
    if user.id in ADMIN_IDS:
        msg += "\n👑 Admin"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ Online | WS: {len(_started_ws_symbols)} symbols")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("**Bitsure Teddy** v2.5\nStable daily analysis.\nFCS API + RealMarketAPI")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN missing")
        return
    
    load_all_user_data()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyse", analyse_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("trend", trend_command))
    app.add_handler(CommandHandler("scalp", scalp_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("alerts", list_alerts_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("addwatch", addwatch_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("about", about_command))
    
    app.job_queue.run_repeating(check_alerts_job, interval=30, first=10)
    
    logger.info("Bitsure Teddy v2.5 starting...")
    app.run_polling()

if __name__ == "__main__":
    main()