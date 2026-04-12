#!/usr/bin/env python3
"""
Bitsure Teddy - Professional Trading Signals Bot
Enhanced with:
- Rate limiting (10 free requests/day/user)
- Teddy Score (0-100 confidence indicator)
- CoinGecko fallback for crypto prices
- Extended history cache (1 hour)
- Automatic degraded mode when FCS API quota exceeded
- Consistent JSON persistence (string chat_id keys)
- HOURLY INTRADAY ANALYSIS (1h interval, 5 days period)
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

# Constants
HISTORY_PERIOD = "5d"       # 5 days of hourly data (~120 bars)
HISTORY_INTERVAL = "1h"     # Hourly interval for intraday analysis
REALTIME_FRESH_SECONDS = 120
PRICE_CACHE_TTL = 15
HISTORY_CACHE_TTL = 3600    # 1 hour (since hourly data updates every hour)
MAX_WEBSOCKET_RETRY_DELAY = 30

# Rate limiting
FREE_DAILY_LIMIT = 10  # requests per day for free users

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

# ------------------------------------------------------------------
# Global Caches & Realtime Prices
# ------------------------------------------------------------------

realtime_prices: Dict[str, Dict[str, Any]] = {}
realtime_lock = threading.Lock()

_price_cache: Dict[str, Dict[str, Any]] = {}
_history_cache: Dict[str, Dict[str, Any]] = {}

_started_ws_symbols: Set[str] = set()
_ws_lock = threading.Lock()

# Tick history for scalping (last 120 seconds)
tick_history: Dict[str, List[Dict[str, Any]]] = {}
tick_lock = threading.Lock()

# User data (ALL keys are str(chat_id) for consistency)
user_alerts: Dict[str, List[Dict[str, Any]]] = {}
user_watchlists: Dict[str, List[str]] = {}
user_settings: Dict[str, Dict[str, Any]] = {}
user_usage: Dict[str, Dict[str, Any]] = {}

# FCS API degraded mode flag (if quota exceeded)
fcs_degraded_mode = False
fcs_degraded_lock = threading.Lock()

alert_job_queue: Optional[JobQueue] = None

# ------------------------------------------------------------------
# Data Persistence Helpers
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
    """Returns (allowed, message)."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    key = str(chat_id)
    user_data = user_usage.get(key, {"date": today, "count": 0})
    if user_data.get("date") != today:
        user_data = {"date": today, "count": 0}
    count = user_data.get("count", 0)

    # Premium users have unlimited
    is_premium = user_settings.get(key, {}).get("premium", False)
    if is_premium:
        return True, ""

    if count >= FREE_DAILY_LIMIT:
        return False, f"❌ Daily free limit reached ({FREE_DAILY_LIMIT} requests). Upgrade to premium for unlimited access."

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
        if val is None:
            return None
        if isinstance(val, str) and not val.strip():
            return None
        return float(val)
    except Exception:
        return None

def is_forex_like(symbol: str) -> bool:
    s = clean_symbol(symbol)
    if s.endswith("=X"):
        return True
    if re.fullmatch(r"[A-Z]{6}=X", s):
        return True
    if re.fullmatch(r"[A-Z]{6}", s):
        base, quote = s[:3], s[3:]
        return base.isalpha() and quote in COMMON_FOREX_QUOTES
    return False

def is_commodity_like(symbol: str) -> bool:
    s = clean_symbol(symbol)
    if s in COMMODITY_CODES:
        return True
    if s.startswith(("XAU", "XAG", "XPT", "XPD", "USOIL", "UKOIL", "BRENT", "NGAS", "OSX")):
        return True
    if s.endswith("=F"):
        return True
    return False

def is_crypto_like(symbol: str) -> bool:
    s = clean_symbol(symbol).replace("-", "").replace("_", "")
    if s in COMMON_CRYPTO_BASES:
        return True
    if s.endswith("USD"):
        base = s[:-3]
        if base in COMMON_CRYPTO_BASES:
            return True
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
        add(s)
        add(s.replace("=X", "").replace("=F", ""))
    stripped = strip_separators(s)
    if re.fullmatch(r"[A-Z]{6}", stripped):
        base, quote = stripped[:3], stripped[3:]
        add(f"{base}{quote}=X")
        add(f"{base}-{quote}")
        if quote == "USD" and base in COMMON_CRYPTO_BASES:
            add(f"{base}-USD")
        if base in {"XAU", "XAG", "XPT", "XPD"} and quote == "USD":
            add(f"{base}USD=X")
    if re.fullmatch(r"[A-Z]{3,5}", stripped):
        add(f"{stripped}=X")
    if is_crypto_like(stripped):
        core = stripped.replace("-", "").replace("_", "")
        if core.endswith("USD") and len(core) > 3:
            add(f"{core[:-3]}-USD")
            add(core)
    if is_commodity_like(stripped):
        add(f"{stripped}=X")
        add(stripped)
    return candidates

def realmarket_symbol(symbol: str) -> str:
    s = clean_symbol(symbol)
    s = s.replace("=X", "").replace("=F", "")
    s = s.replace("/", "").replace("-", "").replace("_", "")
    return s

def get_user_setting(chat_id: int, key: str, default: Any = None) -> Any:
    return user_settings.get(str(chat_id), {}).get(key, default)

def set_user_setting(chat_id: int, key: str, value: Any) -> None:
    key_str = str(chat_id)
    if key_str not in user_settings:
        user_settings[key_str] = {}
    user_settings[key_str][key] = value
    save_user_settings()

# ------------------------------------------------------------------
# Historical Data (Yahoo + FCS fallback) with extended cache
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
    hist = hist[wanted].dropna(subset=["Close"]).reset_index(drop=True)
    return hist

def extract_ohlcv_from_payload(payload: Any) -> List[Dict[str, Any]]:
    records = []
    def recurse(obj):
        if isinstance(obj, list):
            if obj and all(isinstance(x, dict) for x in obj):
                if any(k in obj[0] for k in ("o","h","l","c","open","high","low","close")):
                    records.extend([x for x in obj if isinstance(x, dict)])
                    return
            for item in obj:
                recurse(item)
        elif isinstance(obj, dict):
            if any(k in obj for k in ("o","h","l","c","open","high","low","close")):
                records.append(obj)
                return
            for key in ("response","historical","data","candles","result","results"):
                if key in obj:
                    recurse(obj[key])
    recurse(payload)
    return records

def df_from_fcs_history(symbol: str) -> pd.DataFrame:
    global fcs_degraded_mode
    if not FCS_API_KEY:
        return pd.DataFrame()
    with fcs_degraded_lock:
        if fcs_degraded_mode:
            return pd.DataFrame()
    params = {"access_key": FCS_API_KEY, "symbol": realmarket_symbol(symbol), "period": "1h"}
    cls = market_class(symbol)
    if cls == "commodity":
        params["type"] = "commodity"
    elif cls == "crypto":
        params["type"] = "crypto"
    elif cls == "forex":
        params["synthetic"] = "1"
    try:
        resp = requests.get("https://api-v4.fcsapi.com/forex/history", params=params, timeout=15)
        if resp.status_code == 429:
            with fcs_degraded_lock:
                fcs_degraded_mode = True
            logger.warning("FCS API quota exceeded. Switching to degraded mode (Yahoo only).")
            return pd.DataFrame()
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        logger.warning(f"FCS history failed for {symbol}: {e}")
        return pd.DataFrame()

    records = extract_ohlcv_from_payload(payload)
    if not records:
        return pd.DataFrame()
    rows = []
    for item in records:
        c = safe_float(item.get("c") or item.get("close"))
        if c is None:
            continue
        rows.append({
            "Open": safe_float(item.get("o") or item.get("open")),
            "High": safe_float(item.get("h") or item.get("high")) or c,
            "Low": safe_float(item.get("l") or item.get("low")) or c,
            "Close": c,
            "Volume": safe_float(item.get("v") or item.get("volume")),
        })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df[["Open","High","Low","Close","Volume"]].dropna(subset=["Close"]).reset_index(drop=True)
    return df

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
        except Exception as e:
            logger.debug(f"Yahoo attempt {candidate}: {e}")
            continue

    if df.empty and market_class(symbol_clean) in {"forex", "commodity", "crypto"}:
        try:
            df = df_from_fcs_history(symbol_clean)
        except Exception as e:
            logger.warning(f"FCS fallback history failed: {e}")

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
# Current Price (WebSocket > FCS > CoinGecko > Yahoo)
# ------------------------------------------------------------------

def get_coingecko_price(symbol: str) -> Optional[float]:
    """Fetch crypto price from CoinGecko (free API)."""
    if not is_crypto_like(symbol):
        return None
    base = strip_separators(symbol)
    if base.endswith("USD"):
        base = base[:-3]
    coin_id_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "XRP": "ripple", "LTC": "litecoin",
        "BCH": "bitcoin-cash", "ADA": "cardano", "SOL": "solana", "DOT": "polkadot",
        "DOGE": "dogecoin", "AVAX": "avalanche-2", "LINK": "chainlink",
        "MATIC": "matic-network", "XLM": "stellar", "ATOM": "cosmos", "UNI": "uniswap",
        "ETC": "ethereum-classic", "TRX": "tron", "NEAR": "near", "FIL": "filecoin",
        "ARB": "arbitrum", "OP": "optimism", "APT": "aptos", "HBAR": "hedera-hashgraph",
        "ALGO": "algorand", "VET": "vechain", "ICP": "internet-computer", "SUI": "sui",
        "INJ": "injective-protocol", "SEI": "sei-network", "PEPE": "pepe",
        "TON": "the-open-network", "SHIB": "shiba-inu", "BNB": "binancecoin",
    }
    coin_id = coin_id_map.get(base.upper())
    if not coin_id:
        return None
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return safe_float(data.get(coin_id, {}).get("usd"))
    except Exception as e:
        logger.debug(f"CoinGecko failed for {symbol}: {e}")
        return None

def get_yahoo_last_price(symbol: str) -> Optional[float]:
    for candidate in yahoo_symbol_candidates(symbol):
        try:
            ticker = yf.Ticker(candidate)
            try:
                fi = ticker.fast_info
                for attr in ("lastPrice","last_price","regularMarketPrice","previousClose"):
                    p = safe_float(getattr(fi, attr, None))
                    if p and p > 0:
                        return p
            except Exception:
                pass
            hist = ticker.history(period="1d")
            if not hist.empty:
                c = safe_float(hist["Close"].iloc[-1])
                if c and c > 0:
                    return c
        except Exception as e:
            logger.debug(f"Yahoo price {candidate}: {e}")
    return None

def get_fcs_latest_price(symbol: str) -> Optional[float]:
    global fcs_degraded_mode
    if not FCS_API_KEY:
        return None
    with fcs_degraded_lock:
        if fcs_degraded_mode:
            return None
    cls = market_class(symbol)
    if cls not in {"forex", "commodity", "crypto"}:
        return None
    params = {"access_key": FCS_API_KEY, "symbol": realmarket_symbol(symbol)}
    if cls == "commodity":
        params["type"] = "commodity"
    elif cls == "crypto":
        params["type"] = "crypto"
    elif cls == "forex":
        params["synthetic"] = "1"
    try:
        resp = requests.get("https://api-v4.fcsapi.com/forex/latest", params=params, timeout=15)
        if resp.status_code == 429:
            with fcs_degraded_lock:
                fcs_degraded_mode = True
            logger.warning("FCS API quota exceeded. Switching to degraded mode.")
            return None
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        logger.warning(f"FCS latest {symbol}: {e}")
        return None

    def search_price(obj):
        if isinstance(obj, dict):
            for key in ("c","close","price","last","lastPrice","ClosePrice","bid","ask"):
                p = safe_float(obj.get(key))
                if p and p > 0:
                    return p
            for key in ("response","data","result"):
                if key in obj:
                    p = search_price(obj[key])
                    if p:
                        return p
        elif isinstance(obj, list):
            for item in obj:
                p = search_price(item)
                if p:
                    return p
        return None

    return search_price(payload)

def update_realtime_price(symbol: str, price: float) -> None:
    if not price or price <= 0:
        return
    ts = now_ts()
    aliases = {clean_symbol(symbol), realmarket_symbol(symbol), strip_separators(clean_symbol(symbol))}
    with realtime_lock:
        for alias in aliases:
            realtime_prices[alias] = {"price": price, "ts": ts}
    with tick_lock:
        base_sym = realmarket_symbol(symbol)
        if base_sym not in tick_history:
            tick_history[base_sym] = []
        tick_history[base_sym].append({"ts": ts, "price": price})
        tick_history[base_sym] = [t for t in tick_history[base_sym] if ts - t["ts"] <= 120]

def get_realtime_price(symbol: str) -> Optional[float]:
    aliases = [clean_symbol(symbol), realmarket_symbol(symbol), strip_separators(clean_symbol(symbol))]
    with realtime_lock:
        for alias in aliases:
            data = realtime_prices.get(alias)
            if data and (now_ts() - data["ts"]) <= REALTIME_FRESH_SECONDS:
                p = safe_float(data["price"])
                if p and p > 0:
                    return p
    return None

def start_realtime_feed(symbol: str) -> None:
    if not REALMARKET_API_KEY:
        return
    market_sym = realmarket_symbol(symbol)
    if not market_sym:
        return
    with _ws_lock:
        if market_sym in _started_ws_symbols:
            return
        _started_ws_symbols.add(market_sym)
    thread = threading.Thread(target=_realtime_worker, args=(market_sym,), daemon=True)
    thread.start()

def _realtime_worker(symbol: str) -> None:
    if not REALMARKET_API_KEY:
        return
    delay = 1.0
    while True:
        ws_url = f"wss://api.realmarketapi.com/price?apiKey={REALMARKET_API_KEY}&symbolCode={symbol}&timeFrame=M1"
        def on_message(ws, msg):
            try:
                data = json.loads(msg)
                if isinstance(data, list):
                    candle = data[0] if data else {}
                elif isinstance(data, dict):
                    candle = data
                else:
                    return
                price = safe_float(candle.get("ClosePrice") or candle.get("close") or candle.get("c") or candle.get("price"))
                if price:
                    update_realtime_price(symbol, price)
            except Exception:
                pass
        def on_error(ws, err): logger.warning(f"WebSocket error {symbol}: {err}")
        def on_close(ws, code, msg): logger.warning(f"WebSocket closed {symbol}, reconnecting in {delay}s")
        def on_open(ws): 
            nonlocal delay; delay = 1.0
            logger.info(f"WebSocket connected for {symbol}")
        try:
            ws = WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            logger.error(f"WebSocket worker crash {symbol}: {e}")
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

    price = get_fcs_latest_price(symbol_clean)
    if price:
        _price_cache[symbol_clean] = {"ts": now_ts(), "price": price, "source": "fcs"}
        return price, "fcs"

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
# Technical Indicators (pure Python)
# ------------------------------------------------------------------

def compute_sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def compute_bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std(ddof=0)
    upper = sma + num_std * std
    lower = sma - num_std * std
    return upper, sma, lower

def detect_divergence(prices: pd.Series, rsi: pd.Series, lookback: int = 5) -> Optional[str]:
    if len(prices) < lookback or len(rsi) < lookback:
        return None
    p_seg = prices.iloc[-lookback:].values
    r_seg = rsi.iloc[-lookback:].values
    if p_seg[-1] < p_seg[0] and r_seg[-1] > r_seg[0]:
        return "bullish"
    if p_seg[-1] > p_seg[0] and r_seg[-1] < r_seg[0]:
        return "bearish"
    return None

# ------------------------------------------------------------------
# Teddy Score (0-100 confidence indicator)
# ------------------------------------------------------------------

def compute_teddy_score(df: pd.DataFrame, signal: str, details: Dict[str, Any]) -> int:
    score = 50
    close = df["Close"]
    last_rsi = details["rsi"]
    last_price = details["price"]
    sma20 = details["sma20"]
    sma50 = details["sma50"]
    support = details["support"]
    resistance = details["resistance"]

    if last_rsi < 30:
        score += 15
    elif last_rsi > 70:
        score -= 15
    elif 40 <= last_rsi <= 60:
        score += 5

    if last_price > sma20 > sma50:
        score += 10
    elif last_price < sma20 < sma50:
        score -= 10

    dist_to_support = (last_price - support) / support * 100 if support else 0
    dist_to_resistance = (resistance - last_price) / last_price * 100 if resistance else 0
    if dist_to_support < 1:
        score += 10
    elif dist_to_resistance < 1:
        score -= 5

    if "Volume" in df.columns and len(df) > 20:
        avg_vol = df["Volume"].tail(20).mean()
        last_vol = df["Volume"].iloc[-1]
        if last_vol > avg_vol * 1.5:
            score += 5 if signal == "ACHETER" else -5 if signal == "VENDRE" else 0

    if details.get("divergence"):
        score += 15 if signal == "ACHETER" else -15 if signal == "VENDRE" else 0

    if details["histogram"] > 0:
        score += 5
    else:
        score -= 5

    return max(0, min(100, score))

# ------------------------------------------------------------------
# Signal Engine (strict rules)
# ------------------------------------------------------------------

def generate_signal(df: pd.DataFrame) -> Tuple[str, str, str, Dict[str, Any], int]:
    close = df["Close"]
    rsi = compute_rsi(close, 14)
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

    window_50 = close.tail(50)
    support = window_50.min()
    resistance = window_50.max()

    divergence = detect_divergence(close, rsi, lookback=5)

    signal_out = "ATTENDRE"
    advice = ""
    extra_tip = ""

    if divergence == "bullish":
        signal_out = "ACHETER"
        advice = "🔥 Bullish divergence"
    elif divergence == "bearish":
        signal_out = "VENDRE"
        advice = "🔥 Bearish divergence"
    elif last_rsi < 30 and last_hist > 0:
        signal_out = "ACHETER"
        advice = "RSI oversold & MACD turning up"
    elif last_rsi > 70 and last_hist < 0:
        signal_out = "VENDRE"
        advice = "RSI overbought & MACD turning down"
    elif last_price <= support * 1.01 and last_rsi < 40:
        signal_out = "ACHETER"
        advice = "Price near support, RSI low"
    elif last_price >= resistance * 0.99 and last_rsi > 60:
        signal_out = "VENDRE"
        advice = "Price near resistance, RSI high"
    elif prev_macd < prev_signal and last_macd > last_signal:
        signal_out = "ACHETER"
        advice = "MACD bullish crossover"
    elif prev_macd > prev_signal and last_macd < last_signal:
        signal_out = "VENDRE"
        advice = "MACD bearish crossover"
    elif last_price > sma20.iloc[last_idx] > sma50.iloc[last_idx] and last_rsi < 50:
        signal_out = "ACHETER"
        advice = "Bullish trend pullback"
    elif last_price < sma20.iloc[last_idx] < sma50.iloc[last_idx] and last_rsi > 50:
        signal_out = "VENDRE"
        advice = "Bearish trend pullback"
    else:
        signal_out = "ATTENDRE"
        advice = "📊 No clear signal – wait for better setup"

    if signal_out != "ATTENDRE":
        if last_rsi > 70:
            extra_tip = "⚠️ Wait for a pullback before buying" if signal_out == "ACHETER" else "🔻 Selling pressure, downside risk"
        elif last_rsi < 30:
            extra_tip = "📈 Bounce zone likely"
        elif last_price <= support * 1.02:
            extra_tip = "📈 Bounce zone likely"
        elif last_price >= resistance * 0.98:
            extra_tip = "⚠️ Wait for a pullback before buying"
        else:
            extra_tip = "✅ Good entry point"

    details = {
        "price": last_price,
        "rsi": round(last_rsi, 2),
        "macd": round(last_macd, 4),
        "signal": round(last_signal, 4),
        "histogram": round(last_hist, 4),
        "sma20": round(sma20.iloc[last_idx], 4),
        "sma50": round(sma50.iloc[last_idx], 4),
        "support": round(support, 4),
        "resistance": round(resistance, 4),
        "divergence": divergence,
    }

    teddy_score = compute_teddy_score(df, signal_out, details)
    return signal_out, advice, extra_tip, details, teddy_score

# ------------------------------------------------------------------
# Chart Generation (with hourly timestamps)
# ------------------------------------------------------------------

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
    ax.plot(x, upper, label='Bollinger Upper', color='gray', linestyle=':', alpha=0.7)
    ax.plot(x, mid, label='Bollinger Mid', color='gray', linestyle=':', alpha=0.7)
    ax.plot(x, lower, label='Bollinger Lower', color='gray', linestyle=':', alpha=0.7)
    ax.fill_between(x, lower, upper, color='gray', alpha=0.1)
    ax.set_title(f"{symbol} – Hourly Chart with Indicators", color='white')
    ax.set_xlabel("Hours ago")
    ax.set_ylabel("Price")
    ax.legend(loc='upper left')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

# ------------------------------------------------------------------
# Scalping Analysis (micro timeframe)
# ------------------------------------------------------------------

def analyze_scalp(symbol: str, duration_sec: int) -> str:
    market_sym = realmarket_symbol(symbol)
    ts_now = now_ts()
    with tick_lock:
        ticks = tick_history.get(market_sym, [])
    relevant = [t for t in ticks if ts_now - t["ts"] <= duration_sec]
    if len(relevant) < 3:
        return f"⚠️ Not enough tick data for the last {duration_sec} seconds. Ensure WebSocket is active."

    prices = [t["price"] for t in relevant]
    first = prices[0]
    last = prices[-1]
    high = max(prices)
    low = min(prices)

    variation = ((last - first) / first) * 100
    volatility = ((high - low) / first) * 100

    x = np.arange(len(prices))
    slope, _ = np.polyfit(x, prices, 1)

    if slope > 0 and variation > 0.05:
        signal = "↗️ MICRO UPTREND"
        advice = f"Price rose {variation:.2f}% in {duration_sec}s. Momentum is bullish."
    elif slope < 0 and variation < -0.05:
        signal = "↘️ MICRO DOWNTREND"
        advice = f"Price fell {variation:.2f}% in {duration_sec}s. Momentum is bearish."
    else:
        signal = "↔️ FLAT"
        advice = f"Price stable (variation {variation:+.2f}%). No clear micro-trend."

    return (f"⚡️ **Scalp Analysis ({duration_sec}s) for {symbol}**\n"
            f"Price: {last:.5f}\n"
            f"Variation: {variation:+.2f}%\n"
            f"Volatility: {volatility:.2f}%\n\n"
            f"🚦 Signal: {signal}\n"
            f"💡 {advice}")

# ------------------------------------------------------------------
# Telegram Bot Handlers - Core
# ------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 **Bitsure Teddy – Trading Signals Bot**\n\n"
        "Professional market analysis for crypto, forex, stocks & commodities.\n"
        "Use /help to see all available commands.\n\n"
        f"⚠️ Free tier: {FREE_DAILY_LIMIT} requests/day. Upgrade for unlimited.\n"
        "⚠️ Trading involves risk. Use signals as part of your own strategy."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 **Bitsure Teddy – Command List**\n\n"
        "**Core Analysis**\n"
        "/analyse SYMBOL – Full analysis + Teddy Score + chart (hourly)\n"
        "/price SYMBOL – Real‑time price\n"
        "/trend SYMBOL – Trend direction (multi‑timeframe)\n"
        "/volatility SYMBOL – ATR volatility (14 periods)\n"
        "/correlation S1 S2 – 30‑period correlation\n"
        "/levels SYMBOL – Support/resistance & pivot points\n\n"
        "**Scalping (micro)**\n"
        "/scalp SYMBOL DURATION – Micro trend (3,5,10,20s)\n"
        "/tick SYMBOL – Latest tick price\n"
        "/spread SYMBOL – Bid/ask spread (if available)\n\n"
        "**Alerts**\n"
        "/alert SYMBOL CONDITION PRICE – Set price alert\n"
        "/alerts – List your alerts\n"
        "/delalert ID – Delete alert by ID\n"
        "/clearalerts – Delete all alerts\n\n"
        "**Watchlist**\n"
        "/watchlist – View your watchlist\n"
        "/addwatch SYMBOL – Add symbol\n"
        "/removewatch SYMBOL – Remove symbol\n"
        "/scan – Quick scan of watchlist\n\n"
        "**Settings**\n"
        "/settings – View your settings\n"
        "/settimeframe TF – Default timeframe (1h,4h,1d)\n"
        "/setrisk PROFILE – low, medium, high\n"
        "/setlanguage LANG – (en/fr)\n"
        "/usage – Check remaining free requests\n\n"
        "**Info**\n"
        "/status – Bot & API status\n"
        "/about – About this bot\n"
        "/symbolinfo SYMBOL – Metadata\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remaining = get_remaining_requests(chat_id)
    is_premium = user_settings.get(str(chat_id), {}).get("premium", False)
    if is_premium:
        await update.message.reply_text("💎 Premium user – unlimited requests.")
    else:
        await update.message.reply_text(f"📊 Free tier: {remaining}/{FREE_DAILY_LIMIT} requests remaining today.")

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
        await update.message.reply_text("❌ Usage: /price SYMBOL")
        return
    symbol = context.args[0].strip()
    price, source = get_current_price(symbol)
    if price is None:
        await update.message.reply_text(f"❌ Symbol {symbol} not found or price unavailable.")
        return
    msg = f"💰 {symbol.upper()} : {price:.4f}\n📡 Source: {source}"
    if fcs_degraded_mode and source != "real-time":
        msg += "\n⚠️ FCS API quota exceeded, using fallback sources."
    await update.message.reply_text(msg)

@rate_limited_command
async def analyse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /analyse SYMBOL")
        return
    symbol = context.args[0].strip()
    await update.message.chat.send_action(action="typing")

    df = get_history(symbol)
    if df.empty or len(df) < 30:
        await update.message.reply_text(f"❌ Symbol {symbol} not found or insufficient data.")
        return

    signal, advice, extra_tip, details, teddy_score = generate_signal(df)
    live_price, source = get_current_price(symbol)
    if live_price is None:
        live_price = details["price"]

    message = (
        f"📊 **{symbol.upper()} Analysis (Hourly)**\n"
        f"💰 Price: {live_price:.4f} ({source})\n"
        f"📈 RSI(14): {details['rsi']}\n"
        f"📉 MACD: {details['macd']} | Signal: {details['signal']} | Hist: {details['histogram']}\n"
        f"📊 SMA20: {details['sma20']} | SMA50: {details['sma50']}\n"
        f"🛡️ Support: {details['support']} | Resistance: {details['resistance']}\n"
    )
    if details.get("divergence"):
        message += f"🔄 Divergence: {details['divergence'].capitalize()}\n"
    message += f"\n🚦 **Signal: {signal}**\n💡 {advice}"
    if extra_tip:
        message += f"\n📌 {extra_tip}"
    message += f"\n\n🏆 **Teddy Score: {teddy_score}/100**"
    if fcs_degraded_mode:
        message += "\n⚠️ FCS API quota exceeded, using fallback data."

    chart_buf = generate_chart(df, symbol)
    await update.message.reply_photo(photo=chart_buf, caption=message, parse_mode="Markdown")

# ------------------------------------------------------------------
# Advanced Analysis Commands (rate limited)
# ------------------------------------------------------------------

@rate_limited_command
async def trend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /trend SYMBOL")
        return
    symbol = context.args[0].strip()
    df = get_history(symbol)
    if df.empty:
        await update.message.reply_text(f"❌ Symbol {symbol} not found.")
        return
    close = df["Close"]
    sma20 = compute_sma(close, 20).iloc[-1]
    sma50 = compute_sma(close, 50).iloc[-1]
    last = close.iloc[-1]
    if last > sma20 > sma50:
        trend = "📈 Strong Uptrend"
    elif last > sma20:
        trend = "↗️ Uptrend (above SMA20)"
    elif last < sma20 < sma50:
        trend = "📉 Strong Downtrend"
    elif last < sma20:
        trend = "↘️ Downtrend (below SMA20)"
    else:
        trend = "↔️ Neutral / Ranging"
    await update.message.reply_text(f"📐 **{symbol} Trend**\n\nPrice: {last:.4f}\nSMA20: {sma20:.4f}\nSMA50: {sma50:.4f}\n\nTrend: {trend}", parse_mode="Markdown")

@rate_limited_command
async def volatility_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /volatility SYMBOL")
        return
    symbol = context.args[0].strip()
    df = get_history(symbol)
    if df.empty:
        await update.message.reply_text(f"❌ Symbol {symbol} not found.")
        return
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    last = close.iloc[-1]
    atr_pct = (atr / last) * 100
    await update.message.reply_text(f"📊 **{symbol} Volatility (ATR 14)**\n\nATR: {atr:.4f}\nPrice: {last:.4f}\nVolatility: {atr_pct:.2f}%", parse_mode="Markdown")

@rate_limited_command
async def correlation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /correlation SYMBOL1 SYMBOL2")
        return
    sym1, sym2 = context.args[0], context.args[1]
    df1 = get_history(sym1)
    df2 = get_history(sym2)
    if df1.empty or df2.empty:
        await update.message.reply_text("❌ One or both symbols not found.")
        return
    common_len = min(len(df1), len(df2), 50)  # more bars for hourly
    ret1 = df1["Close"].pct_change().tail(common_len)
    ret2 = df2["Close"].pct_change().tail(common_len)
    corr = ret1.corr(ret2)
    await update.message.reply_text(f"📈 **Correlation ({common_len} periods)**\n{sym1.upper()} vs {sym2.upper()}: {corr:.3f}")

@rate_limited_command
async def levels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /levels SYMBOL")
        return
    symbol = context.args[0].strip()
    df = get_history(symbol)
    if df.empty:
        await update.message.reply_text(f"❌ Symbol {symbol} not found.")
        return
    high_50 = df["High"].tail(50).max()
    low_50 = df["Low"].tail(50).min()
    last = df["Close"].iloc[-1]
    pivot = (high_50 + low_50 + last) / 3
    r1 = 2 * pivot - low_50
    s1 = 2 * pivot - high_50
    r2 = pivot + (high_50 - low_50)
    s2 = pivot - (high_50 - low_50)
    msg = (f"📏 **{symbol} Levels**\n\n"
           f"Resistance 2: {r2:.4f}\n"
           f"Resistance 1: {r1:.4f}\n"
           f"Pivot: {pivot:.4f}\n"
           f"Support 1: {s1:.4f}\n"
           f"Support 2: {s2:.4f}\n"
           f"Current Price: {last:.4f}")
    await update.message.reply_text(msg, parse_mode="Markdown")

# ------------------------------------------------------------------
# Scalping Commands (no rate limit)
# ------------------------------------------------------------------

async def scalp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /scalp SYMBOL DURATION (3,5,10,20)")
        return
    symbol = context.args[0].strip().upper()
    try:
        duration = int(context.args[1])
        if duration not in [3,5,10,20]:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Duration must be 3, 5, 10, or 20 seconds.")
        return

    start_realtime_feed(symbol)
    await asyncio.sleep(1)
    analysis = analyze_scalp(symbol, duration)
    await update.message.reply_text(analysis, parse_mode="Markdown")

async def tick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /tick SYMBOL")
        return
    symbol = context.args[0].strip().upper()
    market_sym = realmarket_symbol(symbol)
    with tick_lock:
        ticks = tick_history.get(market_sym, [])
    if not ticks:
        await update.message.reply_text(f"⚠️ No tick data for {symbol}. Ensure WebSocket is active.")
        return
    latest = max(ticks, key=lambda x: x["ts"])
    age = now_ts() - latest["ts"]
    await update.message.reply_text(f"🕒 {symbol} last tick: {latest['price']:.5f} ({age:.1f}s ago)")

async def spread_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FCS_API_KEY:
        await update.message.reply_text("❌ FCS API not configured.")
        return
    if fcs_degraded_mode:
        await update.message.reply_text("⚠️ FCS API quota exceeded, spread unavailable.")
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: /spread SYMBOL")
        return
    symbol = context.args[0].strip().upper()
    params = {"access_key": FCS_API_KEY, "symbol": realmarket_symbol(symbol)}
    cls = market_class(symbol)
    if cls == "commodity":
        params["type"] = "commodity"
    elif cls == "crypto":
        params["type"] = "crypto"
    elif cls == "forex":
        params["synthetic"] = "1"
    try:
        resp = requests.get("https://api-v4.fcsapi.com/forex/latest", params=params, timeout=10)
        if resp.status_code == 429:
            with fcs_degraded_lock:
                fcs_degraded_mode = True
            await update.message.reply_text("⚠️ FCS API quota exceeded, spread unavailable.")
            return
        data = resp.json()
        def find_bid_ask(obj):
            if isinstance(obj, dict):
                bid = safe_float(obj.get("bid"))
                ask = safe_float(obj.get("ask"))
                if bid and ask:
                    return bid, ask
                for k in ("response","data"):
                    if k in obj:
                        return find_bid_ask(obj[k])
            return None, None
        bid, ask = find_bid_ask(data)
        if bid and ask:
            spread = ask - bid
            await update.message.reply_text(f"📊 {symbol} Spread: {spread:.5f} (Bid: {bid:.5f} / Ask: {ask:.5f})")
        else:
            await update.message.reply_text("❌ Bid/ask not available.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# ------------------------------------------------------------------
# Alerts System (keys are str(chat_id))
# ------------------------------------------------------------------

async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("❌ Usage: /alert SYMBOL above/below PRICE")
        return
    symbol = context.args[0].strip().upper()
    condition = context.args[1].lower()
    if condition not in ("above", "below"):
        await update.message.reply_text("❌ Condition must be 'above' or 'below'.")
        return
    try:
        target = float(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Price must be a number.")
        return

    chat_id = str(update.effective_chat.id)
    alert_id = int(time.time() * 1000) % 1000000
    alert = {
        "id": alert_id,
        "symbol": symbol,
        "condition": condition,
        "target": target,
        "created": now_ts()
    }
    if chat_id not in user_alerts:
        user_alerts[chat_id] = []
    user_alerts[chat_id].append(alert)
    save_user_alerts()
    await update.message.reply_text(f"✅ Alert set: {symbol} {condition} {target} (ID: {alert_id})")

async def list_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    alerts = user_alerts.get(chat_id, [])
    if not alerts:
        await update.message.reply_text("📭 You have no active alerts.")
        return
    msg = "🔔 **Your Alerts**\n\n"
    for a in alerts:
        msg += f"ID {a['id']}: {a['symbol']} {a['condition']} {a['target']}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def delalert_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /delalert ID")
        return
    try:
        alert_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID must be a number.")
        return
    chat_id = str(update.effective_chat.id)
    alerts = user_alerts.get(chat_id, [])
    new_alerts = [a for a in alerts if a["id"] != alert_id]
    if len(new_alerts) == len(alerts):
        await update.message.reply_text("❌ Alert ID not found.")
        return
    user_alerts[chat_id] = new_alerts
    save_user_alerts()
    await update.message.reply_text(f"✅ Alert {alert_id} deleted.")

async def clearalerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user_alerts[chat_id] = []
    save_user_alerts()
    await update.message.reply_text("✅ All alerts cleared.")

async def check_alerts_job(context: ContextTypes.DEFAULT_TYPE):
    for chat_id_str, alerts in user_alerts.items():
        for alert in alerts[:]:
            price, _ = get_current_price(alert["symbol"])
            if price is None:
                continue
            triggered = False
            if alert["condition"] == "above" and price >= alert["target"]:
                triggered = True
            elif alert["condition"] == "below" and price <= alert["target"]:
                triggered = True
            if triggered:
                try:
                    await context.bot.send_message(
                        chat_id=int(chat_id_str),
                        text=f"🚨 **ALERT TRIGGERED**\n{alert['symbol']} is {alert['condition']} {alert['target']}\nCurrent price: {price:.4f}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send alert: {e}")
                user_alerts[chat_id_str] = [a for a in user_alerts[chat_id_str] if a["id"] != alert["id"]]
                save_user_alerts()

# ------------------------------------------------------------------
# Watchlist Commands (keys are str(chat_id))
# ------------------------------------------------------------------

async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    wl = user_watchlists.get(chat_id, [])
    if not wl:
        await update.message.reply_text("📭 Your watchlist is empty. Use /addwatch SYMBOL.")
        return
    msg = "📋 **Your Watchlist**\n\n"
    for sym in wl:
        price, source = get_current_price(sym)
        if price:
            msg += f"{sym}: {price:.4f} ({source})\n"
        else:
            msg += f"{sym}: price unavailable\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def addwatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /addwatch SYMBOL")
        return
    symbol = context.args[0].strip().upper()
    chat_id = str(update.effective_chat.id)
    if chat_id not in user_watchlists:
        user_watchlists[chat_id] = []
    if symbol in user_watchlists[chat_id]:
        await update.message.reply_text(f"⚠️ {symbol} already in watchlist.")
        return
    user_watchlists[chat_id].append(symbol)
    save_user_watchlists()
    await update.message.reply_text(f"✅ {symbol} added to watchlist.")

async def removewatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /removewatch SYMBOL")
        return
    symbol = context.args[0].strip().upper()
    chat_id = str(update.effective_chat.id)
    wl = user_watchlists.get(chat_id, [])
    if symbol not in wl:
        await update.message.reply_text(f"❌ {symbol} not in watchlist.")
        return
    user_watchlists[chat_id] = [s for s in wl if s != symbol]
    save_user_watchlists()
    await update.message.reply_text(f"✅ {symbol} removed from watchlist.")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    wl = user_watchlists.get(chat_id, [])
    if not wl:
        await update.message.reply_text("📭 Watchlist empty.")
        return
    await update.message.chat.send_action(action="typing")
    results = []
    for sym in wl:
        df = get_history(sym)
        if df.empty or len(df) < 30:
            results.append(f"{sym}: insufficient data")
            continue
        signal, advice, _, _, _ = generate_signal(df)
        price, _ = get_current_price(sym)
        results.append(f"{sym}: {price:.4f} → {signal} ({advice[:30]}...)")
    msg = "🔍 **Watchlist Scan**\n\n" + "\n".join(results)
    await update.message.reply_text(msg, parse_mode="Markdown")

# ------------------------------------------------------------------
# Settings Commands
# ------------------------------------------------------------------

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    settings = user_settings.get(chat_id, {})
    msg = "⚙️ **Your Settings**\n\n"
    msg += f"Timeframe: {settings.get('timeframe', '1h')}\n"
    msg += f"Risk profile: {settings.get('risk', 'medium')}\n"
    msg += f"Language: {settings.get('language', 'en')}\n"
    msg += f"Premium: {'✅ Yes' if settings.get('premium', False) else '❌ No'}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def settimeframe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /settimeframe TIMEFRAME (1h,4h,1d)")
        return
    tf = context.args[0].lower()
    if tf not in ["1h","4h","1d"]:
        await update.message.reply_text("❌ Supported: 1h, 4h, 1d")
        return
    set_user_setting(update.effective_chat.id, "timeframe", tf)
    await update.message.reply_text(f"✅ Default timeframe set to {tf}.")

async def setrisk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /setrisk low/medium/high")
        return
    risk = context.args[0].lower()
    if risk not in ["low","medium","high"]:
        await update.message.reply_text("❌ Choose low, medium, or high.")
        return
    set_user_setting(update.effective_chat.id, "risk", risk)
    await update.message.reply_text(f"✅ Risk profile set to {risk}.")

async def setlanguage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /setlanguage en/fr")
        return
    lang = context.args[0].lower()
    if lang not in ["en","fr"]:
        await update.message.reply_text("❌ Supported: en, fr")
        return
    set_user_setting(update.effective_chat.id, "language", lang)
    await update.message.reply_text(f"✅ Language set to {lang}.")

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche l'ID Telegram de l'utilisateur."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    message = (
        f"🆔 **Your Telegram Info**\n\n"
        f"User ID: `{user.id}`\n"
        f"Chat ID: `{chat_id}`\n"
        f"Username: @{user.username if user.username else 'None'}\n"
        f"First Name: {user.first_name or 'None'}\n"
    )
    
    # Indiquer si l'utilisateur est admin
    if user.id in ADMIN_IDS:
        message += "\n👑 **You are a bot administrator**"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# ------------------------------------------------------------------
# Info & Admin Commands
# ------------------------------------------------------------------

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ws_status = "Connected" if _started_ws_symbols else "Idle"
    fcs_status = "⚠️ Degraded (quota exceeded)" if fcs_degraded_mode else ("✅" if FCS_API_KEY else "❌")
    msg = (f"🤖 **Bitsure Teddy Status**\n\n"
           f"Telegram: ✅\n"
           f"WebSocket: {ws_status} ({len(_started_ws_symbols)} symbols)\n"
           f"FCS API: {fcs_status}\n"
           f"RealMarketAPI: {'✅' if REALMARKET_API_KEY else '❌'}\n"
           f"Uptime: running")
    await update.message.reply_text(msg, parse_mode="Markdown")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "**Bitsure Teddy** v2.3\n"
        "Professional trading signals bot\n\n"
        "Now using HOURLY intraday analysis (1h bars, 5 days period).\n"
        "Enhanced with Teddy Score, rate limiting, extended cache, and automatic degraded mode.\n"
        "Powered by Yahoo Finance, FCS API, RealMarketAPI, CoinGecko.\n"
        "Deployed on Railway."
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def symbolinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /symbolinfo SYMBOL")
        return
    symbol = context.args[0].strip().upper()
    cls = market_class(symbol)
    info = f"**{symbol}**\nMarket class: {cls}\n"
    if cls == "forex":
        info += "Type: Forex pair\n"
    elif cls == "crypto":
        info += "Type: Cryptocurrency\n"
    elif cls == "commodity":
        info += "Type: Commodity\n"
    else:
        info += "Type: Stock/ETF\n"
    price, source = get_current_price(symbol)
    if price:
        info += f"Current price: {price:.4f} ({source})"
    else:
        info += "Price unavailable"
    await update.message.reply_text(info, parse_mode="Markdown")

ADMIN_IDS = {8376348929}  # Replace with actual admin Telegram IDs

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❌ Usage: /broadcast message")
        return
    count = 0
    all_chats = set(user_alerts.keys()) | set(user_watchlists.keys()) | set(user_settings.keys())
    for chat_id_str in all_chats:
        try:
            await context.bot.send_message(chat_id=int(chat_id_str), text=f"📢 **Broadcast from Bitsure Teddy**\n\n{text}")
            count += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    load_all_user_data()
    await update.message.reply_text("✅ Configuration reloaded.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized.")
        return
    users = len(set(user_alerts.keys()) | set(user_watchlists.keys()))
    alerts_total = sum(len(a) for a in user_alerts.values())
    msg = f"📊 **Bot Stats**\nUsers: {users}\nActive alerts: {alerts_total}\nWebSocket symbols: {len(_started_ws_symbols)}\nFCS degraded: {fcs_degraded_mode}"
    await update.message.reply_text(msg, parse_mode="Markdown")

# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------

def main():
    global alert_job_queue

    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN missing.")
        return

    load_all_user_data()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    alert_job_queue = app.job_queue

    # Core
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("usage", usage_command))
    app.add_handler(CommandHandler("analyse", analyse_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("myid", myid_command))

    # Scalping
    app.add_handler(CommandHandler("scalp", scalp_command))
    app.add_handler(CommandHandler("tick", tick_command))
    app.add_handler(CommandHandler("spread", spread_command))

    # Advanced
    app.add_handler(CommandHandler("trend", trend_command))
    app.add_handler(CommandHandler("volatility", volatility_command))
    app.add_handler(CommandHandler("correlation", correlation_command))
    app.add_handler(CommandHandler("levels", levels_command))

    # Alerts
    app.add_handler(CommandHandler("alert", alert_command))
    app.add_handler(CommandHandler("alerts", list_alerts_command))
    app.add_handler(CommandHandler("delalert", delalert_command))
    app.add_handler(CommandHandler("clearalerts", clearalerts_command))

    # Watchlist
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("addwatch", addwatch_command))
    app.add_handler(CommandHandler("removewatch", removewatch_command))
    app.add_handler(CommandHandler("scan", scan_command))

    # Settings
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("settimeframe", settimeframe_command))
    app.add_handler(CommandHandler("setrisk", setrisk_command))
    app.add_handler(CommandHandler("setlanguage", setlanguage_command))

    # Info & Admin
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("symbolinfo", symbolinfo_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("reload", reload_command))
    app.add_handler(CommandHandler("stats", stats_command))

    app.job_queue.run_repeating(check_alerts_job, interval=30, first=10)

    logger.info("Bitsure Teddy v2.3 starting with HOURLY intraday analysis...")
    app.run_polling()

if __name__ == "__main__":
    main()