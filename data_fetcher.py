import asyncio
import json
import time
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import requests
import websocket
import threading
import pandas as pd

from config import (
    FCS_API_KEY, REALMARKET_API_KEY, TWELVEDATA_API_KEY, WS_URL,
    PRICE_CACHE_TTL, HISTORY_CACHE_TTL, DEFAULT_TIMEFRAME, HISTORY_PERIOD
)
from utils import cache_key, normalize_symbol

logger = logging.getLogger(__name__)

class DataFetcher:
    _instance = None

    def __init__(self):
        self.price_cache = {}
        self.history_cache = {}
        self.ws = None
        self.ws_thread = None
        self.ws_running = False
        self.subscribed_symbols = set()
        self.ws_twelvedata = None
        self.ws_twelvedata_thread = None
        self.ws_twelvedata_running = False
        self.twelvedata_callbacks = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_websocket(self):
        pass

    # --- WebSocket Twelve Data (Premium) ---
    def start_twelvedata_websocket(self):
        if self.ws_twelvedata_running:
            return
        self.ws_twelvedata_running = True
        self.ws_twelvedata_thread = threading.Thread(target=self._run_twelvedata_websocket, daemon=True)
        self.ws_twelvedata_thread.start()

    def _run_twelvedata_websocket(self):
        while self.ws_twelvedata_running:
            try:
                ws = websocket.WebSocketApp(
                    "wss://ws.twelvedata.com/v1/quotes/price",
                    on_open=self._on_open_twelvedata,
                    on_message=self._on_message_twelvedata,
                    on_error=self._on_error_twelvedata,
                    on_close=self._on_close_twelvedata
                )
                self.ws_twelvedata = ws
                ws.run_forever()
            except Exception as e:
                logger.error(f"Twelve Data WebSocket error: {e}")
            time.sleep(5)

    def _on_open_twelvedata(self, ws):
        logger.info("Twelve Data WebSocket connected")
        if self.subscribed_symbols:
            subscribe_msg = {
                "action": "subscribe",
                "params": {
                    "apikey": TWELVEDATA_API_KEY,
                    "symbols": ",".join(self.subscribed_symbols)
                }
            }
            ws.send(json.dumps(subscribe_msg))

    def _on_message_twelvedata(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("event") == "price":
                symbol = data.get("symbol")
                price = float(data.get("price", 0))
                bid = float(data.get("bid", price))
                ask = float(data.get("ask", price))
                self.price_cache[symbol] = {
                    "price": price,
                    "bid": bid,
                    "ask": ask,
                    "timestamp": time.time()
                }
                if symbol in self.twelvedata_callbacks:
                    for cb in self.twelvedata_callbacks[symbol]:
                        cb(symbol, price, bid, ask)
        except Exception as e:
            logger.error(f"Twelve Data WebSocket message error: {e}")

    def _on_error_twelvedata(self, ws, error):
        logger.error(f"Twelve Data WebSocket error: {error}")

    def _on_close_twelvedata(self, ws, close_status_code, close_msg):
        logger.info("Twelve Data WebSocket closed")

    def subscribe_twelvedata(self, symbol: str, callback=None):
        symbol = normalize_symbol(symbol)
        self.subscribed_symbols.add(symbol)
        if callback:
            if symbol not in self.twelvedata_callbacks:
                self.twelvedata_callbacks[symbol] = []
            self.twelvedata_callbacks[symbol].append(callback)
        if self.ws_twelvedata and self.ws_twelvedata.sock and self.ws_twelvedata.sock.connected:
            subscribe_msg = {
                "action": "subscribe",
                "params": {
                    "apikey": TWELVEDATA_API_KEY,
                    "symbols": symbol
                }
            }
            self.ws_twelvedata.send(json.dumps(subscribe_msg))

    # --- Récupération des prix temps réel (REST) ---
    async def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)
        # Vérifier d'abord le cache
        if symbol in self.price_cache:
            cache = self.price_cache[symbol]
            if time.time() - cache["timestamp"] < PRICE_CACHE_TTL:
                return cache
        # Essayer Twelve Data
        price = await self._fetch_twelvedata_price(symbol)
        if price:
            self.price_cache[symbol] = price
            return price
        # Fallback Yahoo Finance
        price = await self._fetch_yahoo_price(symbol)
        if price:
            self.price_cache[symbol] = price
            return price
        return None

    async def _fetch_twelvedata_price(self, symbol: str) -> Optional[Dict]:
        if not TWELVEDATA_API_KEY:
            return None
        try:
            td_symbol = self._to_twelvedata_symbol(symbol)
            url = f"https://api.twelvedata.com/quote?symbol={td_symbol}&apikey={TWELVEDATA_API_KEY}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                price_str = data.get("close") or data.get("price")
                bid_str = data.get("bid")
                ask_str = data.get("ask")
                if price_str is not None:
                    price = float(price_str)
                    bid = float(bid_str) if bid_str is not None else price
                    ask = float(ask_str) if ask_str is not None else price
                    return {
                        "price": price,
                        "bid": bid,
                        "ask": ask,
                        "timestamp": time.time()
                    }
        except Exception as e:
            logger.warning(f"Twelve Data quote error for {symbol}: {e}")
        return None

    async def _fetch_yahoo_price(self, symbol: str) -> Optional[Dict]:
        try:
            import yfinance as yf
            ticker_symbol = self._to_yahoo_symbol(symbol)
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                return {
                    "price": float(price),
                    "bid": float(price),
                    "ask": float(price),
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.warning(f"Yahoo price error for {symbol}: {e}")
        return None

    def _to_twelvedata_symbol(self, symbol: str) -> str:
        """Convertit un symbole en format Twelve Data (actions, forex, crypto)."""
        s = symbol.upper()
        # Cryptos (BTCUSD, ETHUSD, etc.)
        if s.endswith("USD") and s[:-3] in ["BTC", "ETH", "XRP", "SOL", "ADA", "BNB", "LTC", "BCH", "DOT", "LINK"]:
            return s[:-3] + "/USD"
        # Forex (EURUSD -> EUR/USD)
        if len(s) == 6 and s.endswith("USD"):
            return f"{s[:3]}/{s[3:]}"
        # Matières premières
        if s == "XAUUSD":
            return "XAU/USD"
        if s == "XAGUSD":
            return "XAG/USD"
        if s in ["USOIL", "WTI"]:
            return "WTI/USD"
        if s == "UKOIL":
            return "BRENT/USD"
        # Actions : AAPL, TSLA, etc. restent tels quels
        return s

    def _to_yahoo_symbol(self, symbol: str) -> str:
        """Convertit un symbole en format Yahoo Finance."""
        s = symbol.upper()
        if s.endswith("USD") and s[:-3] in ["BTC", "ETH", "XRP", "SOL", "ADA", "BNB"]:
            return s[:-3] + "-USD"
        if len(s) == 6 and s.endswith("USD"):
            return s + "=X"
        if s in ["XAUUSD", "XAGUSD"]:
            return s.replace("USD", "-USD")
        return s

    # --- Historique (inchangé) ---
    async def get_historical_data(self, symbol: str, timeframe: str = DEFAULT_TIMEFRAME,
                                  period: str = HISTORY_PERIOD) -> Optional[pd.DataFrame]:
        symbol = normalize_symbol(symbol)
        cache_k = cache_key(symbol, timeframe, period)
        if cache_k in self.history_cache:
            entry = self.history_cache[cache_k]
            if time.time() - entry["timestamp"] < HISTORY_CACHE_TTL:
                return entry["data"]
        df = await self._fetch_twelvedata_history(symbol, timeframe, period)
        if df is None and FCS_API_KEY:
            df = await self._fetch_fcs_history(symbol, timeframe, period)
        if df is None:
            df = await self._fetch_yahoo_history(symbol, timeframe, period)
        if df is not None and not df.empty:
            self.history_cache[cache_k] = {"data": df, "timestamp": time.time()}
            return df
        return None

    async def _fetch_twelvedata_history(self, symbol: str, timeframe: str, period: str) -> Optional[pd.DataFrame]:
        if not TWELVEDATA_API_KEY:
            return None
        try:
            interval_map = {"1d": "1day", "1h": "1h", "4h": "4h", "1m": "1min"}
            interval = interval_map.get(timeframe, "1day")
            days = 60 if period == "2mo" else 30
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            td_symbol = self._to_twelvedata_symbol(symbol)
            url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval={interval}&start_date={start_date}&apikey={TWELVEDATA_API_KEY}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                values = data.get("values", [])
                if values:
                    rows = []
                    for item in reversed(values):
                        rows.append({
                            "Date": item["datetime"],
                            "Open": float(item["open"]),
                            "High": float(item["high"]),
                            "Low": float(item["low"]),
                            "Close": float(item["close"]),
                            "Volume": float(item.get("volume", 0))
                        })
                    df = pd.DataFrame(rows)
                    df["Date"] = pd.to_datetime(df["Date"])
                    df.set_index("Date", inplace=True)
                    return df
        except Exception as e:
            logger.warning(f"Twelve Data history error: {e}")
        return None

    async def _fetch_yahoo_history(self, symbol: str, timeframe: str, period: str) -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf
            ticker_symbol = self._to_yahoo_symbol(symbol)
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period=period, interval=timeframe)
            if df.empty:
                return None
            return df
        except Exception as e:
            logger.warning(f"Yahoo history error: {e}")
        return None

    async def _fetch_fcs_history(self, symbol: str, timeframe: str, period: str) -> Optional[pd.DataFrame]:
        if not FCS_API_KEY:
            return None
        days = 60 if period == "2mo" else 30
        try:
            url = f"https://fcsapi.com/api-v3/forex/history?symbol={symbol}&period={timeframe}&from={self._date_days_ago(days)}&to={datetime.now().strftime('%Y-%m-%d')}&access_key={FCS_API_KEY}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200 and data.get("response"):
                    rows = []
                    for item in data["response"]:
                        rows.append({
                            "Date": item["date"],
                            "Open": float(item["o"]),
                            "High": float(item["h"]),
                            "Low": float(item["l"]),
                            "Close": float(item["c"]),
                            "Volume": float(item.get("v", 0))
                        })
                    df = pd.DataFrame(rows)
                    df["Date"] = pd.to_datetime(df["Date"])
                    df.set_index("Date", inplace=True)
                    return df
        except Exception as e:
            logger.warning(f"FCS history error: {e}")
        return None

    def _date_days_ago(self, days: int) -> str:
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")