#!/usr/bin/env python3
"""
Bitsure Teddy - Professional Trading Signals Bot
v2.4 - DAILY ANALYSIS (reliable for forex, crypto, stocks)
Enhanced with:
- Rate limiting (10 free requests/day/user)
- Teddy Score (0-100 confidence indicator)
- CoinGecko fallback for crypto prices
- Automatic degraded mode when FCS API quota exceeded
- Consistent JSON persistence
- Admin unlimited access
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
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from websocket import WebSocketApp

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

# ------------------------------------------------------------------
# Configuration & Logging
# ------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("BitsureTeddy")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
FCS_API_KEY = os.environ.get("FCS_API_KEY")
REALMARKET_API_KEY = os.environ.get("REALMARKET_API_KEY")

# Constants - DAILY ANALYSIS
HISTORY_PERIOD = "2mo"
HISTORY_INTERVAL = "1d"
REALTIME_FRESH_SECONDS = 120
PRICE_CACHE_TTL = 15
HISTORY_CACHE_TTL = 300
MAX_WEBSOCKET_RETRY_DELAY = 30

# Rate limiting
FREE_DAILY_LIMIT = 10

# Data storage paths
DATA_DIR = os.environ.get("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)
ALERTS_FILE = os.path.join(DATA_DIR, "alerts.json")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlists.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
USAGE_FILE = os.path.join(DATA_DIR, "usage.json")

# Recognized assets
COMMON_CRYPTO_BASES = {
    "BTC", "ETH", "XRP", "LTC", "BCH", "ADA", "SOL", "DOT", "DOGE", "AVAX",
    "LINK", "MATIC", "XLM", "ATOM", "UNI", "ETC", "TRX", "NEAR", "FIL", "ARB",
    "OP", "APT", "HBAR", "ALGO", "VET", "ICP", "SUI", "INJ", "SEI", "PEPE",
    "TON", "SHIB", "BNB"
}
COMMON_FOREX_QUOTES = {"USD", "JPY", "EUR", "GBP", "CHF", "CAD", "AUD", "NZD", "BIF", "ZAR", "NOK", "SEK", "DKK"}
COMMODITY_CODES = {
    "XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD", "SILVER", "OSX", "WTI", "BRENT",
    "NGAS", "OIL", "USOIL", "UKOIL", "XCUUSD", "COPPER", "PLATINUM"
}

# Admin IDs - unlimited access
ADMIN_IDS = {8376348929}

# ------------------------------------------------------------------
# Global Caches & Realtime Prices
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

fcs_degraded_mode = False
fcs_degraded_lock = threading.Lock()

alert_job_queue: Optional[JobQueue] = None

# ------------------------------------------------------------------
# Data Persistence
# ------------------------------------------------------------------

def load_json(path: str, default: Any) -> Any:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: str, data: Any) -> None:
    try:
        with open(path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Failed to save {path}: {e}")

def load_all_user_data():
    global user_alerts, user_watchlists, user_settings, user_usage
    user_alerts = load_json(ALERTS_FILE, {})
    user_watchlists = load_json(WATCHLIST_FILE, {})
    user_settings = load_json(SETTINGS_FILE, {})
    user_usage = load_json(USAGE_FILE, {})

def save_user_alerts():
    save_json(ALERTS_FILE, user_alerts)

def save_user_watchlists():
    save_json(WATCHLIST_FILE, user_watchlists)

def save_user_settings():
    save_json(SETTINGS_FILE, user_settings)

def save_user_usage():
    save_json(USAGE_FILE, user_usage)

# ------------------------------------------------------------------
# Rate Limiting
# ------------------------------------------------------------------

def check_rate_limit(chat_id: int) -> Tuple[bool, str]:
    if chat_id in ADMIN_IDS:
        return True, ""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    key = str(chat_id)
    user_data = user_usage.get(key, {"date": today, "count": 0})
    if user_data.get("date") != today:
        user_data = {"date": today, "count": 0}
    count = user_data.get("count", 0)
    is_premium = user_settings.get(key, {}).get("premium", False)
    if is_premium:
        return True, ""
    if count >= FREE_DAILY_LIMIT:
        return False, f"❌ Daily free limit reached ({FREE_DAILY_LIMIT} requests)."
    user_data["count"] = count + 1
    user_usage[key] = user_data
    save_user_usage()
    return True, ""

def get_remaining_requests(chat_id: int) -> int:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    key = str(chat_id)
    user_data = user_usage.get(key, {"date": today, "count": 0})
    if user_data.get("date") != today:
        return FREE_DAILY_LIMIT
    return max(0, FREE_DAILY_LIMIT - user_data.get("count", 0))

# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def now_ts() -> float:
    return time.time()

def clean_symbol(raw: str) -> str:
    return re.sub(r"\s+", "", raw.strip().upper())

def strip_separators(symbol: str) -> str:
    return symbol.replace("/", "").replace(":", "").replace(" ", "").replace("-", "").replace("_", "")

def safe_float(val: Any) -> Optional[float]:
    try:
        if val is None or (isinstance(val, str) and not val.strip()):
            return None
        return float(val)
    except Exception:
        return None

def is_forex_like(symbol: str) -> bool:
    s = clean_symbol(symbol)
    if s.endswith("=X") or re.fullmatch(r"[A-Z]{6}=X", s):
        return True
    if re.fullmatch(r"[A-Z]{6}", s):
        base, quote = s[:3], s[3:]
        return base.isalpha() and quote in COMMON_FOREX_QUOTES
    return False

def is_commodity_like(symbol: str) -> bool:
    s = clean_symbol(symbol)
    return s in COMMODITY_CODES or s.startswith(("XAU", "XAG", "XPT", "XPD", "USOIL", "UKOIL", "BRENT", "NGAS")) or s.endswith("=F")

def is_crypto_like(symbol: str) -> bool:
    s = clean_symbol(symbol).replace("-", "").replace("_", "")
    if s in COMMON_CRYPTO_BASES:
        return True
    if s.endswith("USD"):
        return s[:-3] in COMMON_CRYPTO_BASES
    return False

def market_class(symbol: str) -> str:
    if is_forex_like(symbol):
        return "forex"
    if is_commodity_like(symbol):
        return "commodity"
    if is_crypto_like(symbol):
        return "crypto"
    return "stock"

def yahoo_symbol_candidates(symbol: str) -> List[str]:
    s = clean_symbol(symbol)
    candidates = []
    def add(x):
        if x and x not in candidates:
            candidates.append(x)
    add(s)
    add(strip_separators(s))
    if s.endswith("=X") or s.endswith("=F"):
        add(s.replace("=X", "").replace("=F", ""))
    stripped = strip_separators(s)
    if re.fullmatch(r"[A-Z]{6}", stripped):
        base, quote = stripped[:3], stripped[3:]
        add(f"{base}{quote}=X")
        if quote == "USD" and base in COMMON_CRYPTO_BASES:
            add(f"{base}-USD")
    return candidates

def realmarket_symbol(symbol: str) -> str:
    return clean_symbol(symbol).replace("=X", "").replace("=F", "").replace("/", "").replace("-", "").replace("_", "")

# ------------------------------------------------------------------
# Historical Data
# ------------------------------------------------------------------

def df_from_yfinance(ticker_symbol: str) -> pd.DataFrame:
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=HISTORY_PERIOD, interval=HISTORY_INTERVAL, auto_adjust=False, actions=False)
    if hist is None or hist.empty:
        return pd.DataFrame()
    hist = hist.copy()
    rename_map = {col: col.capitalize() for col in hist.columns if col.lower() in ["open","high","low","close","volume"]}
    hist = hist.rename(columns=rename_map)
    wanted = [c for c in ["Open","High","Low","Close","Volume"] if c in hist.columns]
    return hist[wanted].dropna(subset=["Close"]).reset_index(drop=True)

def get_history(symbol: str) -> pd.DataFrame:
    symbol_clean = clean_symbol(symbol)
    cached = _history_cache.get(symbol_clean)
    if cached and now_ts() - cached["ts"] <= HISTORY_CACHE_TTL:
        return cached["df"].copy()
    df = pd.DataFrame()
    for candidate in yahoo_symbol_candidates(symbol_clean):
        try:
            df = df_from_yfinance(candidate)
            if not df.empty and len(df) >= 20:
                break
        except Exception:
            continue
    if df.empty:
        return df
    for col in ["Open","High","Low","Close","Volume"]:
        if col not in df.columns:
            df[col] = np.nan
    df = df[["Open","High","Low","Close","Volume"]].copy()
    for col in ["Open","High","Low","Close","Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Close"]).reset_index(drop=True)
    _history_cache[symbol_clean] = {"ts": now_ts(), "df": df.copy()}
    return df

# ------------------------------------------------------------------
# Current Price
# ------------------------------------------------------------------

def get_coingecko_price(symbol: str) -> Optional[float]:
    if not is_crypto_like(symbol):
        return None
    base = strip_separators(symbol).replace("USD", "")
    coin_id_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "ADA": "cardano",
        "DOGE": "dogecoin", "XRP": "ripple", "LTC": "litecoin"
    }
    coin_id = coin_id_map.get(base.upper())
    if not coin_id:
        return None
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        resp = requests.get(url, timeout=10)
        return safe_float(resp.json().get(coin_id, {}).get("usd"))
    except Exception:
        return None

def get_yahoo_last_price(symbol: str) -> Optional[float]:
    for candidate in yahoo_symbol_candidates(symbol):
        try:
            ticker = yf.Ticker(candidate)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return safe_float(hist["Close"].iloc[-1])
        except Exception:
            continue
    return None

def get_realtime_price(symbol: str) -> Optional[float]:
    aliases = [clean_symbol(symbol), realmarket_symbol(symbol), strip_separators(clean_symbol(symbol))]
    with realtime_lock:
        for alias in aliases:
            data = realtime_prices.get(alias)
            if data and (now_ts() - data["ts"]) <= REALTIME_FRESH_SECONDS:
                return safe_float(data["price"])
    return None

def start_realtime_feed(symbol: str) -> None:
    if not REALMARKET_API_KEY:
        return
    market_sym = realmarket_symbol(symbol)
    with _ws_lock:
        if market_sym in _started_ws_symbols:
            return
        _started_ws_symbols.add(market_sym)
    threading.Thread(target=_realtime_worker, args=(market_sym,), daemon=True).start()

def _realtime_worker(symbol: str) -> None:
    delay = 1.0
    while True:
        ws_url = f"wss://api.realmarketapi.com/price?apiKey={REALMARKET_API_KEY}&symbolCode={symbol}&timeFrame=M1"
        def on_message(ws, msg):
            try:
                data = json.loads(msg)
                candle = data[0] if isinstance(data, list) else data
                price = safe_float(candle.get("ClosePrice") or candle.get("close") or candle.get("c"))
                if price:
                    ts = now_ts()
                    with realtime_lock:
                        realtime_prices[symbol] = {"price": price, "ts": ts}
            except Exception:
                pass
        try:
            ws = WebSocketApp(ws_url, on_message=on_message)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception:
            pass
        time.sleep(delay)
        delay = min(delay * 2, MAX_WEBSOCKET_RETRY_DELAY)

def get_current_price(symbol: str) -> Tuple[Optional[float], str]:
    symbol_clean = clean_symbol(symbol)
    cached = _price_cache.get(symbol_clean)
    if cached and now_ts() - cached["ts"] <= PRICE_CACHE_TTL:
        return cached["price"], cached.get("source", "cache")
    start_realtime_feed(symbol_clean)
    price = get_realtime_price(symbol_clean)
    if price:
        _price_cache[symbol_clean] = {"ts": now_ts(), "price": price, "source": "real-time"}
        return price, "real-time"
    if is_crypto_like(symbol_clean):
        price = get_coingecko_price(symbol_clean)
        if price:
            _price_cache[symbol_clean] = {"ts": now_ts(), "price": price, "source": "coingecko"}
            return price, "coingecko"
    price = get_yahoo_last_price(symbol_clean)
    if price:
        _price_cache[symbol_clean] = {"ts": now_ts(), "price": price, "source": "yahoo"}
        return price, "yahoo"
    return None, "none"

# ------------------------------------------------------------------
# Technical Indicators
# ------------------------------------------------------------------

def compute_sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line, macd_line - signal_line

def compute_bollinger(series: pd.Series, window: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    return sma + 2*std, sma, sma - 2*std

def detect_divergence(prices: pd.Series, rsi: pd.Series, lookback: int = 5) -> Optional[str]:
    if len(prices) < lookback:
        return None
    p_seg = prices.iloc[-lookback:].values
    r_seg = rsi.iloc[-lookback:].values
    if p_seg[-1] < p_seg[0] and r_seg[-1] > r_seg[0]:
        return "bullish"
    if p_seg[-1] > p_seg[0] and r_seg[-1] < r_seg[0]:
        return "bearish"
    return None

def compute_teddy_score(df: pd.DataFrame, signal: str, details: Dict[str, Any]) -> int:
    score = 50
    last_rsi = details["rsi"]
    last_price = details["price"]
    sma20, sma50 = details["sma20"], details["sma50"]
    if last_rsi < 30:
        score += 15
    elif last_rsi > 70:
        score -= 15
    if last_price > sma20 > sma50:
        score += 10
    elif last_price < sma20 < sma50:
        score -= 10
    if details.get("divergence"):
        score += 15 if signal == "ACHETER" else -15
    if details["histogram"] > 0:
        score += 5
    else:
        score -= 5
    return max(0, min(100, score))

def generate_signal(df: pd.DataFrame) -> Tuple[str, str, str, Dict[str, Any], int]:
    close = df["Close"]
    rsi = compute_rsi(close)
    macd, signal, hist = compute_macd(close)
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    last_idx = -1
    last_price = close.iloc[last_idx]
    last_rsi = rsi.iloc[last_idx]
    last_macd = macd.iloc[last_idx]
    last_signal = signal.iloc[last_idx]
    last_hist = hist.iloc[last_idx]
    prev_macd = macd.iloc[-2] if len(macd) > 1 else last_macd
    prev_signal = signal.iloc[-2] if len(signal) > 1 else last_signal
    support = close.tail(50).min()
    resistance = close.tail(50).max()
    divergence = detect_divergence(close, rsi)

    signal_out = "ATTENDRE"
    advice = "📊 No clear signal – wait for better setup"
    extra_tip = ""

    if divergence == "bullish":
        signal_out, advice = "ACHETER", "🔥 Bullish divergence"
    elif divergence == "bearish":
        signal_out, advice = "VENDRE", "🔥 Bearish divergence"
    elif last_rsi < 30 and last_hist > 0:
        signal_out, advice = "ACHETER", "RSI oversold & MACD turning up"
    elif last_rsi > 70 and last_hist < 0:
        signal_out, advice = "VENDRE", "RSI overbought & MACD turning down"
    elif last_price <= support * 1.01 and last_rsi < 40:
        signal_out, advice = "ACHETER", "Price near support, RSI low"
    elif last_price >= resistance * 0.99 and last_rsi > 60:
        signal_out, advice = "VENDRE", "Price near resistance, RSI high"
    elif prev_macd < prev_signal and last_macd > last_signal:
        signal_out, advice = "ACHETER", "MACD bullish crossover"
    elif prev_macd > prev_signal and last_macd < last_signal:
        signal_out, advice = "VENDRE", "MACD bearish crossover"
    elif last_price > sma20.iloc[last_idx] > sma50.iloc[last_idx] and last_rsi < 50:
        signal_out, advice = "ACHETER", "Bullish trend pullback"
    elif last_price < sma20.iloc[last_idx] < sma50.iloc[last_idx] and last_rsi > 50:
        signal_out, advice = "VENDRE", "Bearish trend pullback"

    if signal_out != "ATTENDRE":
        if last_rsi > 70:
            extra_tip = "⚠️ Wait for a pullback before buying" if signal_out == "ACHETER" else "🔻 Selling pressure"
        elif last_rsi < 30:
            extra_tip = "📈 Bounce zone likely"
        else:
            extra_tip = "✅ Good entry point"

    details = {
        "price": last_price, "rsi": round(last_rsi, 2),
        "macd": round(last_macd, 4), "signal": round(last_signal, 4),
        "histogram": round(last_hist, 4), "sma20": round(sma20.iloc[last_idx], 4),
        "sma50": round(sma50.iloc[last_idx], 4), "support": round(support, 4),
        "resistance": round(resistance, 4), "divergence": divergence
    }
    teddy_score = compute_teddy_score(df, signal_out, details)
    return signal_out, advice, extra_tip, details, teddy_score

def generate_chart(df: pd.DataFrame, symbol: str) -> BytesIO:
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5))
    close = df["Close"]
    sma20 = compute_sma(close, 20)
    sma50 = compute_sma(close, 50)
    upper, mid, lower = compute_bollinger(close)
    x = range(len(close))
    ax.plot(x, close, label='Price', color='white', linewidth=1.5)
    ax.plot(x, sma20, label='SMA20', color='orange', linestyle='--', alpha=0.8)
    ax.plot(x, sma50, label='SMA50', color='cyan', linestyle='--', alpha=0.8)
    ax.plot(x, upper, label='Bollinger', color='gray', linestyle=':', alpha=0.5)
    ax.plot(x, lower, color='gray', linestyle=':', alpha=0.5)
    ax.fill_between(x, lower, upper, color='gray', alpha=0.1)
    ax.set_title(f"{symbol} – Daily Chart with Indicators", color='white')
    ax.set_xlabel("Days ago")
    ax.set_ylabel("Price")
    ax.legend(loc='upper left')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

def analyze_scalp(symbol: str, duration_sec: int) -> str:
    market_sym = realmarket_symbol(symbol)
    with tick_lock:
        ticks = tick_history.get(market_sym, [])
    relevant = [t for t in ticks if now_ts() - t["ts"] <= duration_sec]
    if len(relevant) < 3:
        return f"⚠️ Not enough tick data for {duration_sec}s."
    prices = [t["price"] for t in relevant]
    variation = ((prices[-1] - prices[0]) / prices[0]) * 100
    if variation > 0.05:
        signal, advice = "↗️ MICRO UPTREND", f"Rose {variation:.2f}%"
    elif variation < -0.05:
        signal, advice = "↘️ MICRO DOWNTREND", f"Fell {variation:.2f}%"
    else:
        signal, advice = "↔️ FLAT", "Stable"
    return f"⚡️ **Scalp ({duration_sec}s) {symbol}**\nPrice: {prices[-1]:.5f}\nVariation: {variation:+.2f}%\n🚦 {signal}\n💡 {advice}"

# ------------------------------------------------------------------
# Telegram Handlers
# ------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"🤖 **Bitsure Teddy**\n\nProfessional trading signals.\n⚠️ Free: {FREE_DAILY_LIMIT}/day.\n/help for commands."
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 **Commands**\n\n"
        "**Core**\n/analyse SYMBOL – Full analysis + chart\n/price SYMBOL – Real-time price\n"
        "/trend SYMBOL – Trend direction\n/volatility SYMBOL – ATR\n"
        "/correlation S1 S2 – Correlation\n/levels SYMBOL – S/R levels\n\n"
        "**Scalping**\n/scalp SYMBOL DURATION (3,5,10,20s)\n/tick SYMBOL\n/spread SYMBOL\n\n"
        "**Alerts**\n/alert SYMBOL above/below PRICE\n/alerts\n/delalert ID\n/clearalerts\n\n"
        "**Watchlist**\n/watchlist\n/addwatch SYMBOL\n/removewatch SYMBOL\n/scan\n\n"
        "**Settings**\n/settings\n/settimeframe\n/setrisk\n/setlanguage\n/usage\n\n"
        "**Info**\n/status\n/about\n/symbolinfo\n/myid"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in ADMIN_IDS:
        await update.message.reply_text("👑 Admin – unlimited.")
        return
    remaining = get_remaining_requests(chat_id)
    await update.message.reply_text(f"📊 Free: {remaining}/{FREE_DAILY_LIMIT}")

def rate_limited_command(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        allowed, msg = check_rate_limit(chat_id)
        if not allowed:
            await update.message.reply_text(msg)
            return
        return await func(update, context)
    return wrapper

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /price SYMBOL")
        return
    price, source = get_current_price(context.args[0])
    if price is None:
        await update.message.reply_text("❌ Not found.")
    else:
        await update.message.reply_text(f"💰 {context.args[0].upper()}: {price:.4f} ({source})")

@rate_limited_command
async def analyse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ /analyse SYMBOL")
        return
    symbol = context.args[0].strip()
    await update.message.chat.send_action(action="typing")
    df = get_history(symbol)
    if df.empty or len(df) < 30:
        await update.message.reply_text("❌ Not found or insufficient data.")
        return
    signal, advice, extra_tip, details, teddy_score = generate_signal(df)
    live_price, source = get_current_price(symbol)
    if live_price is None:
        live_price = details["price"]
    message = (
        f"📊 **{symbol.upper()} Analysis**\n💰 {live_price:.4f} ({source})\n"
        f"📈 RSI: {details['rsi']}\n📉 MACD: {details['macd']} | Signal: {details['signal']}\n"
        f"📊 SMA20: {details['sma20']} | SMA50: {details['sma50']}\n"
        f"🛡️ S/R: {details['support']} / {details['resistance']}\n"
        f"\n🚦 **{signal}**\n💡 {advice}\n📌 {extra_tip}\n\n🏆 Teddy Score: {teddy_score}/100"
    )
    chart = generate_chart(df, symbol)
    await update.message.reply_photo(photo=chart, caption=message, parse_mode="Markdown")

@rate_limited_command
async def trend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    df = get_history(context.args[0])
    if df.empty:
        await update.message.reply_text("❌ Not found.")
        return
    close = df["Close"]
    sma20, sma50 = compute_sma(close, 20).iloc[-1], compute_sma(close, 50).iloc[-1]
    last = close.iloc[-1]
    trend = "📈 Uptrend" if last > sma20 > sma50 else "📉 Downtrend" if last < sma20 < sma50 else "↔️ Neutral"
    await update.message.reply_text(f"📐 {context.args[0].upper()}: {trend}")

async def scalp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ /scalp SYMBOL DURATION")
        return
    symbol = context.args[0]
    try:
        duration = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Duration must be 3,5,10,20")
        return
    start_realtime_feed(symbol)
    await asyncio.sleep(1)
    await update.message.reply_text(analyze_scalp(symbol, duration), parse_mode="Markdown")

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = f"🆔 User ID: `{user.id}`\nChat ID: `{update.effective_chat.id}`"
    if user.id in ADMIN_IDS:
        msg += "\n👑 Admin"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ /alert SYMBOL above/below PRICE")
        return
    symbol, cond, target = context.args[0].upper(), context.args[1].lower(), float(context.args[2])
    chat_id = str(update.effective_chat.id)
    alert = {"id": int(time.time()*1000)%1000000, "symbol": symbol, "condition": cond, "target": target}
    user_alerts.setdefault(chat_id, []).append(alert)
    save_user_alerts()
    await update.message.reply_text(f"✅ Alert set: {symbol} {cond} {target}")

async def list_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alerts = user_alerts.get(str(update.effective_chat.id), [])
    if not alerts:
        await update.message.reply_text("📭 No alerts.")
        return
    msg = "🔔 **Alerts**\n" + "\n".join(f"ID {a['id']}: {a['symbol']} {a['condition']} {a['target']}" for a in alerts)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id, alerts in list(user_alerts.items()):
        for alert in alerts[:]:
            price, _ = get_current_price(alert["symbol"])
            if price and ((alert["condition"]=="above" and price>=alert["target"]) or (alert["condition"]=="below" and price<=alert["target"])):
                try:
                    await context.bot.send_message(int(chat_id), f"🚨 {alert['symbol']} {alert['condition']} {alert['target']} @ {price:.4f}")
                except Exception:
                    pass
                user_alerts[chat_id].remove(alert)
                save_user_alerts()

async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wl = user_watchlists.get(str(update.effective_chat.id), [])
    if not wl:
        await update.message.reply_text("📭 Empty. /addwatch SYMBOL")
        return
    msg = "📋 **Watchlist**\n" + "\n".join(f"{s}: {get_current_price(s)[0]:.4f}" if get_current_price(s)[0] else f"{s}: N/A" for s in wl)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def addwatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    chat_id = str(update.effective_chat.id)
    sym = context.args[0].upper()
    user_watchlists.setdefault(chat_id, []).append(sym)
    save_user_watchlists()
    await update.message.reply_text(f"✅ {sym} added.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🤖 Online | WS: {len(_started_ws_symbols)} symbols")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("**Bitsure Teddy** v2.4\nDAILY analysis. Deployed on Railway.", parse_mode="Markdown")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    global alert_job_queue
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN missing.")
        return
    load_all_user_data()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    alert_job_queue = app.job_queue

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("usage", usage_command))
    app.add_handler(CommandHandler("analyse", analyse_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(CommandHandler("scalp", scalp_command))
    app.add_handler(CommandHandler("trend", trend_command))
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("alerts", list_alerts_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("addwatch", addwatch_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("about", about_command))

    app.job_queue.run_repeating(check_alerts_job, interval=30, first=10)
    logger.info("Bitsure Teddy v2.4 starting with DAILY analysis...")
    app.run_polling()

if __name__ == "__main__":
    main()