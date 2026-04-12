import asyncio
import json
import logging
import math
import os
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import yfinance as yf
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application, ApplicationBuilder, CallbackContext, CommandHandler,
    ContextTypes, MessageHandler, filters,
)
def main():
    """Point d'entrée principal du bot"""
    print("Bitsure Teddy bot starting...")
    logger.info("Bot starting...")
    
    # Créer l'application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Ajouter les handlers (à compléter)
    # application.add_handler(CommandHandler("start", start_command))
    
    # Démarrer le bot
    application.run_polling()

if __name__ == "__main__":
    main()
try:
    import websocket
except Exception:
    websocket = None

# =========================
# Configuration
# =========================

BOT_NAME = os.getenv('BOT_NAME', 'Bitsure Teddy')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '').strip()
FCS_API_KEY = os.getenv('FCS_API_KEY', '').strip()
REALMARKET_API_KEY = os.getenv('REALMARKET_API_KEY', '').strip()
REALMARKET_WS_URL = os.getenv('REALMARKET_WS_URL', '').strip()
FCS_BASE_URL = os.getenv('FCS_BASE_URL', 'https://fcsapi.com/api-v3').strip()
COINGECKO_BASE_URL = os.getenv('COINGECKO_BASE_URL', 'https://api.coingecko.com/api/v3').strip()
YAHOO_MAX_PERIOD = os.getenv('YAHOO_MAX_PERIOD', '2mo')
ADMIN_ID = int(os.getenv('ADMIN_TELEGRAM_ID', '8376348929'))
DATA_DIR = Path(os.getenv('DATA_DIR', '/data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)

USERS_FILE = DATA_DIR / 'users.json'
WATCHLIST_FILE = DATA_DIR / 'watchlists.json'
ALERTS_FILE = DATA_DIR / 'alerts.json'
SETTINGS_FILE = DATA_DIR / 'settings.json'
USAGE_FILE = DATA_DIR / 'usage.json'
CACHE_FILE = DATA_DIR / 'cache.json'
STATS_FILE = DATA_DIR / 'stats.json'

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger('bitsure-teddy')

# =========================
# Helpers
# =========================

def now_ts() -> float:
    return time.time()

def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

def safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None

def load_json(path: Path, default):
    try:
        if not path.exists():
            return default
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path: Path, data) -> None:
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

def ensure_dict_file(path: Path) -> Dict[str, Any]:
    data = load_json(path, {})
    if not isinstance(data, dict):
        data = {}
    return data

def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(' ', '')

def day_key() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')

def start_of_day_ts() -> float:
    dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return dt.timestamp()

# =========================
# Persistent state
# =========================

state_lock = threading.Lock()
cache_lock = threading.Lock()
ws_lock = threading.Lock()

USERS = ensure_dict_file(USERS_FILE)
WATCHLISTS = ensure_dict_file(WATCHLIST_FILE)
ALERTS = load_json(ALERTS_FILE, [])
if not isinstance(ALERTS, list):
    ALERTS = []
SETTINGS = ensure_dict_file(SETTINGS_FILE)
USAGE = ensure_dict_file(USAGE_FILE)
CACHE = load_json(CACHE_FILE, {})
if not isinstance(CACHE, dict):
    CACHE = {}
STATS = ensure_dict_file(STATS_FILE)
if 'requests_total' not in STATS:
    STATS['requests_total'] = 0
if 'signals' not in STATS:
    STATS['signals'] = {'BUY': 0, 'SELL': 0, 'WAIT': 0}

DEFAULT_USER_SETTINGS = {
    'timeframe': '1d',
    'risk': 'medium',
    'language': 'en',
    'premium': False,
}

FREE_DAILY_LIMIT = 10

# =========================
# Market data providers
# =========================

@dataclass
class MarketSnapshot:
    symbol: str
    price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    source: str = 'unknown'
    timestamp: float = 0.0
    extra: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}

class RealMarketCache:
    def __init__(self):
        self.prices: Dict[str, MarketSnapshot] = {}
        self.last_message: Dict[str, Any] = {}
        self.connected = False
        self.last_update = 0.0
        self.ws = None

    def update(self, symbol: str, price: Optional[float], bid: Optional[float],
               ask: Optional[float], source='realmarket', extra=None):
        with ws_lock:
            self.prices[symbol] = MarketSnapshot(
                symbol=symbol,
                price=price,
                bid=bid,
                ask=ask,
                source=source,
                timestamp=now_ts(),
                extra=extra or {},
            )
            self.last_update = now_ts()

    def get(self, symbol: str) -> Optional[MarketSnapshot]:
        with ws_lock:
            return self.prices.get(symbol)

REALMARKET = RealMarketCache()

class DataProvider:
    @staticmethod
    def get_price(symbol: str) -> MarketSnapshot:
        symbol = normalize_symbol(symbol)
        snap = REALMARKET.get(symbol)
        if snap and snap.price is not None and (now_ts() - snap.timestamp) <= 15:
            return snap

        snap = FCSProvider.get_price(symbol)
        if snap and snap.price is not None:
            return snap

        snap = CoinGeckoProvider.get_price(symbol)
        if snap and snap.price is not None:
            return snap

        snap = YahooProvider.get_price(symbol)
        if snap and snap.price is not None:
            return snap

        return MarketSnapshot(symbol=symbol, source='none', timestamp=now_ts())

    @staticmethod
    def get_history(symbol: str, period='2mo', interval='1d') -> pd.DataFrame:
        symbol = normalize_symbol(symbol)
        cache_key = f'history:{symbol}:{period}:{interval}'
        cached = get_cache(cache_key)
        if cached is not None:
            return cached

        providers = [FCSProvider.get_history, CoinGeckoProvider.get_history, YahooProvider.get_history]
        df = pd.DataFrame()
        for fn in providers:
            try:
                df = fn(symbol, period=period, interval=interval)
                if df is not None and not df.empty:
                    break
            except Exception as e:
                logger.info('History provider failed for %s: %s', symbol, e)

        if df is None:
            df = pd.DataFrame()
        if not df.empty:
            set_cache(cache_key, df, ttl=300)
        return df

class FCSProvider:
    @staticmethod
    def headers() -> Dict[str, str]:
        return {'Authorization': f'Bearer {FCS_API_KEY}'} if FCS_API_KEY else {}

    @staticmethod
    def get_price(symbol: str) -> Optional[MarketSnapshot]:
        if not FCS_API_KEY:
            return None
        url = f'{FCS_BASE_URL}/latest'
        params = {'symbol': symbol}
        try:
            r = requests.get(url, params=params, headers=FCSProvider.headers(), timeout=10)
            r.raise_for_status()
            data = r.json()
            price = FCSProvider._extract_price(data)
            bid = safe_float(data.get('bid')) if isinstance(data, dict) else None
            ask = safe_float(data.get('ask')) if isinstance(data, dict) else None
            if price is None:
                return None
            return MarketSnapshot(symbol=symbol, price=price, bid=bid, ask=ask,
                                  source='fcs', timestamp=now_ts(), extra={'raw': data})
        except Exception as e:
            logger.info('FCS price failed for %s: %s', symbol, e)
            return None

    @staticmethod
    def get_history(symbol: str, period='2mo', interval='1d') -> pd.DataFrame:
        if not FCS_API_KEY:
            return pd.DataFrame()
        url = f'{FCS_BASE_URL}/historical'
        params = {'symbol': symbol, 'period': period, 'interval': interval}
        try:
            r = requests.get(url, params=params, headers=FCSProvider.headers(), timeout=15)
            r.raise_for_status()
            data = r.json()
            rows = data.get('response') if isinstance(data, dict) else None
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows)
            return standardize_history_df(df)
        except Exception as e:
            logger.info('FCS history failed for %s: %s', symbol, e)
            return pd.DataFrame()

    @staticmethod
    def _extract_price(data: Any) -> Optional[float]:
        if isinstance(data, dict):
            for key in ['price', 'close', 'last', 'bid', 'ask']:
                v = safe_float(data.get(key))
                if v is not None:
                    return v
            if 'response' in data and isinstance(data['response'], dict):
                return FCSProvider._extract_price(data['response'])
            if 'response' in data and isinstance(data['response'], list) and data['response']:
                return FCSProvider._extract_price(data['response'][0])
        return None

class CoinGeckoProvider:
    SYMBOL_MAP = {
        'BTCUSD': 'bitcoin', 'ETHUSD': 'ethereum', 'SOLUSD': 'solana',
        'XRPUSD': 'ripple', 'BNBUSD': 'binancecoin', 'ADAUSD': 'cardano',
        'DOGEUSD': 'dogecoin',
    }

    @staticmethod
    def _coin_id(symbol: str) -> Optional[str]:
        s = normalize_symbol(symbol)
        if s in CoinGeckoProvider.SYMBOL_MAP:
            return CoinGeckoProvider.SYMBOL_MAP[s]
        if s.endswith('USD'):
            base = s[:-3].lower()
            return base
        return None

    @staticmethod
    def get_price(symbol: str) -> Optional[MarketSnapshot]:
        coin_id = CoinGeckoProvider._coin_id(symbol)
        if not coin_id:
            return None
        url = f'{COINGECKO_BASE_URL}/simple/price'
        params = {'ids': coin_id, 'vs_currencies': 'usd'}
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            price = safe_float(data.get(coin_id, {}).get('usd'))
            if price is None:
                return None
            return MarketSnapshot(symbol=symbol, price=price, source='coingecko',
                                  timestamp=now_ts(), extra={'coin_id': coin_id})
        except Exception as e:
            logger.info('CoinGecko price failed for %s: %s', symbol, e)
            return None

    @staticmethod
    def get_history(symbol: str, period='2mo', interval='1d') -> pd.DataFrame:
        coin_id = CoinGeckoProvider._coin_id(symbol)
        if not coin_id:
            return pd.DataFrame()
        days = 60 if period == '2mo' else 30
        try:
            url = f'{COINGECKO_BASE_URL}/coins/{coin_id}/market_chart'
            params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            prices = data.get('prices', [])
            if not prices:
                return pd.DataFrame()
            df = pd.DataFrame(prices, columns=['timestamp_ms', 'Close'])
            df['Date'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
            df = df.drop(columns=['timestamp_ms'])
            df['Open'] = df['Close']
            df['High'] = df['Close']
            df['Low'] = df['Close']
            df['Volume'] = np.nan
            return standardize_history_df(df)
        except Exception as e:
            logger.info('CoinGecko history failed for %s: %s', symbol, e)
            return pd.DataFrame()

class YahooProvider:
    @staticmethod
    def _ticker_candidates(symbol: str) -> List[str]:
        s = normalize_symbol(symbol)
        candidates = [s]
        if not any(ch in s for ch in ['=', '.', '^']):
            if s.endswith('USD'):
                base = s[:-3]
                candidates.extend([f'{base}-USD', f'{base}=X'])
            elif len(s) <= 6:
                candidates.extend([f'{s}=X', f'{s}-USD'])
        if s in ['XAUUSD', 'GOLD']:
            candidates.append('GC=F')
        if s in ['XAGUSD', 'SILVER']:
            candidates.append('SI=F')
        if s in ['OIL', 'USOIL', 'WTI']:
            candidates.append('CL=F')
        return list(dict.fromkeys(candidates))

    @staticmethod
    def get_price(symbol: str) -> Optional[MarketSnapshot]:
        for candidate in YahooProvider._ticker_candidates(symbol):
            try:
                t = yf.Ticker(candidate)
                info = {}
                try:
                    info = t.fast_info if hasattr(t, 'fast_info') else {}
                except Exception:
                    info = {}
                price = None
                if isinstance(info, dict):
                    for k in ['last_price', 'lastPrice', 'regularMarketPrice']:
                        price = safe_float(info.get(k))
                        if price is not None:
                            break
                if price is None:
                    hist = t.history(period='1d', interval='1m')
                    if hist is not None and not hist.empty:
                        price = safe_float(hist['Close'].iloc[-1])
                if price is not None:
                    return MarketSnapshot(symbol=candidate, price=price, source='yahoo', timestamp=now_ts())
            except Exception as e:
                logger.info('Yahoo price failed for %s/%s: %s', symbol, candidate, e)
                continue
        return None

    @staticmethod
    def get_history(symbol: str, period='2mo', interval='1d') -> pd.DataFrame:
        for candidate in YahooProvider._ticker_candidates(symbol):
            try:
                df = yf.download(candidate, period=period, interval=interval,
                                 auto_adjust=False, progress=False, threads=False)
                if df is not None and not df.empty:
                    df = df.reset_index()
                    return standardize_history_df(df)
            except Exception as e:
                logger.info('Yahoo history failed for %s/%s: %s', symbol, candidate, e)
                continue
        return pd.DataFrame()

# =========================
# WebSocket ingestion
# =========================

class RealMarketWebSocketThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()

    def run(self):
        if websocket is None or not REALMARKET_WS_URL:
            logger.info('RealMarket WS not configured.')
            return
        while not self.stop_event.is_set():
            try:
                ws = websocket.WebSocketApp(
                    REALMARKET_WS_URL,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                )
                REALMARKET.ws = ws
                REALMARKET.connected = True
                ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                logger.exception('WS loop error: %s', e)
            REALMARKET.connected = False
            time.sleep(5)

    def on_open(self, ws):
        logger.info('RealMarket WS connected')
        if REALMARKET_API_KEY:
            try:
                ws.send(json.dumps({'type': 'auth', 'api_key': REALMARKET_API_KEY}))
            except Exception:
                pass
        try:
            ws.send(json.dumps({'type': 'subscribe', 'channels': ['prices', 'ticks']}))
        except Exception:
            pass

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
        except Exception:
            return
        symbol = normalize_symbol(str(data.get('symbol') or data.get('pair') or data.get('ticker') or ''))
        price = safe_float(data.get('price') or data.get('last') or data.get('close'))
        bid = safe_float(data.get('bid'))
        ask = safe_float(data.get('ask'))
        if symbol and price is not None:
            REALMARKET.update(symbol, price=price, bid=bid, ask=ask, extra=data)

    def on_error(self, ws, error):
        logger.info('RealMarket WS error: %s', error)

    def on_close(self, ws, close_status_code, close_msg):
        logger.info('RealMarket WS closed: %s %s', close_status_code, close_msg)

# =========================
# Cache
# =========================

def get_cache(key: str):
    with cache_lock:
        entry = CACHE.get(key)
        if not entry:
            return None
        if now_ts() > entry.get('expires_at', 0):
            CACHE.pop(key, None)
            save_json(CACHE_FILE, CACHE)
            return None
        t = entry.get('type')
        if t == 'dataframe':
            try:
                return pd.read_json(entry['value'], orient='split')
            except Exception:
                return None
        return entry.get('value')

def set_cache(key: str, value, ttl: int = 60):
    with cache_lock:
        entry = {'expires_at': now_ts() + ttl}
        if isinstance(value, pd.DataFrame):
            entry['type'] = 'dataframe'
            entry['value'] = value.to_json(orient='split', date_format='iso')
        else:
            entry['type'] = 'value'
            entry['value'] = value
        CACHE[key] = entry
        save_json(CACHE_FILE, CACHE)

# =========================
# History normalization
# =========================

def standardize_history_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    cols = {c.lower(): c for c in df.columns}

    def getcol(name):
        return cols.get(name.lower())

    rename = {}
    for want in ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']:
        if getcol(want):
            rename[getcol(want)] = want
    if rename:
        df = df.rename(columns=rename)

    if 'Date' not in df.columns:
        for alt in ['Datetime', 'date', 'timestamp', 'Time']:
            if alt in df.columns:
                df['Date'] = pd.to_datetime(df[alt])
                break
    if 'Date' not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index().rename(columns={'index': 'Date'})
        else:
            df['Date'] = pd.RangeIndex(len(df))

    if not np.issubdtype(df['Date'].dtype, np.datetime64):
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception:
            pass

    for c in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].sort_values('Date').reset_index(drop=True)
    df = df.dropna(subset=['Close'])
    return df

# =========================
# Indicators (manual)
# =========================

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(method='bfill').fillna(50)

def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def bollinger(series: pd.Series, period: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    mid = sma(series, period)
    std = series.rolling(period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def divergence(df: pd.DataFrame, lookback: int = 5) -> str:
    if len(df) < lookback + 3:
        return 'none'
    close = df['Close'].reset_index(drop=True)
    r = rsi(close, 14).reset_index(drop=True)
    p0, p1 = close.iloc[-lookback], close.iloc[-1]
    r0, r1 = r.iloc[-lookback], r.iloc[-1]
    if p1 < p0 and r1 > r0:
        return 'bullish'
    if p1 > p0 and r1 < r0:
        return 'bearish'
    return 'none'

def support_resistance(df: pd.DataFrame, lookback: int = 50) -> Tuple[Optional[float], Optional[float]]:
    tail = df.tail(lookback)
    if tail.empty:
        return None, None
    return safe_float(tail['Low'].min()), safe_float(tail['High'].max())

# =========================
# Signal engine
# =========================

@dataclass
class SignalResult:
    action: str
    label: str
    reason: str
    risk_tip: str
    teddy_score: int
    price: Optional[float]
    support: Optional[float]
    resistance: Optional[float]
    metrics: Dict[str, Any]

RISK_TIPS = {
    'BUY': '⚠️ Wait for a pullback before buying',
    'SELL': '🔻 Selling pressure, downside risk',
    'WAIT': '📈 Bounce zone likely',
}

def teddy_score(df: pd.DataFrame, action: str, metrics: Dict[str, Any]) -> int:
    score = 50
    r = metrics.get('rsi')
    hist = metrics.get('macd_hist')
    trend = metrics.get('trend')
    div = metrics.get('divergence')
    price = metrics.get('price')
    support = metrics.get('support')
    resistance = metrics.get('resistance')

    if r is not None:
        if r < 30:
            score += 15
        elif r > 70:
            score -= 15
        elif 40 < r < 60:
            score += 5

    if hist is not None:
        if hist > 0:
            score += 10
        else:
            score -= 10

    if div == 'bullish':
        score += 20
    elif div == 'bearish':
        score -= 20

    if trend == 'up':
        score += 10
    elif trend == 'down':
        score -= 10

    if support and price:
        if price <= support * 1.02:
            score += 15
    if resistance and price:
        if price >= resistance * 0.98:
            score -= 15

    if action == 'BUY':
        score = max(score, 60)
    elif action == 'SELL':
        score = min(score, 40)

    return max(0, min(100, int(score)))