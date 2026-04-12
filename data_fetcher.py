import asyncio
import json
import time
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import requests
import websocket
import threading
import yfinance as yf
import pandas as pd

from config import (
    FCS_API_KEY, REALMARKET_API_KEY, WS_URL,
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

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # --- WebSocket RealMarket ---
    def start_websocket(self):
        if self.ws_running:
            return
        self.ws_running = True
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()

    def _run_websocket(self):
        while self.ws_running:
            try:
                ws = websocket.WebSocketApp(
                    WS_URL,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self.ws = ws
                ws.run_forever()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            time.sleep(5)

    def _on_open(self, ws):
        logger.info("WebSocket connected")
        auth_msg = {
            "type": "auth",
            "api_key": REALMARKET_API_KEY
        }
        ws.send(json.dumps(auth_msg))
        for sym in self.subscribed_symbols:
            self._subscribe_symbol(ws, sym)

    def _subscribe_symbol(self, ws, symbol: str):
        sub_msg = {
            "type": "subscribe",
            "symbol": symbol
        }
        ws.send(json.dumps(sub_msg))

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            if "symbol" in data and "price" in data:
                symbol = data["symbol"]
                self.price_cache[symbol] = {
                    "price": float(data["price"]),
                    "bid": float(data.get("bid", data["price"])),
                    "ask": float(data.get("ask", data["price"])),
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.error(f"WebSocket message error: {e}")

    def _on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket closed")

    def subscribe_symbol(self, symbol: str):
        symbol = normalize_symbol(symbol)
        self.subscribed_symbols.add(symbol)
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self._subscribe_symbol(self.ws, symbol)

    # --- Récupération des prix temps réel ---
    async def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)
        # 1. WebSocket cache
        if symbol in self.price_cache:
            cache = self.price_cache[symbol]
            if time.time() - cache["timestamp"] < PRICE_CACHE_TTL:
                return cache
        # 2. RealMarket API (via _fetch_fcs_price)
        price = await self._fetch_fcs_price(symbol)
        if price:
            return price
        # 3. CoinGecko (crypto seulement)
        if self._is_crypto(symbol):
            price = await self._fetch_coingecko_price(symbol)
            if price:
                return price
        # 4. Yahoo Finance
        price = await self._fetch_yahoo_price(symbol)
        if price:
            return price
        return None

    async def _fetch_fcs_price(self, symbol: str) -> Optional[Dict]:
        """Utilise RealMarketAPI comme source prioritaire"""
        if not REALMARKET_API_KEY:
            return None
        try:
            url = f"https://api.realmarketapi.com/api/v1/price?ApiKey={REALMARKET_API_KEY}&SymbolCode={symbol}&timeFrame=M1"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get("closePrice")
                if price is not None:
                    return {
                        "price": float(price),
                        "bid": float(data.get("bid", price)),
                        "ask": float(data.get("ask", price)),
                        "timestamp": time.time()
                    }
            else:
                logger.debug(f"RealMarket API error: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.debug(f"RealMarket price error: {e}")
        return None

    async def _fetch_coingecko_price(self, symbol: str) -> Optional[Dict]:
        cg_map = {"BTC": "bitcoin", "ETH": "ethereum", "XRP": "ripple"}
        coin_id = cg_map.get(symbol.upper())
        if not coin_id:
            return None
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get(coin_id, {}).get("usd")
                if price:
                    return {
                        "price": float(price),
                        "bid": float(price),
                        "ask": float(price),
                        "timestamp": time.time()
                    }
        except Exception as e:
            logger.debug(f"CoinGecko error: {e}")
        return None

    async def _fetch_yahoo_price(self, symbol: str) -> Optional[Dict]:
        try:
            ticker = yf.Ticker(symbol)
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
            logger.debug(f"Yahoo price error: {e}")
        return None

    def _is_crypto(self, symbol: str) -> bool:
        cryptos = {"BTC", "ETH", "XRP", "LTC", "BCH", "ADA", "DOT", "LINK", "UNI", "SOL"}
        return symbol.upper() in cryptos

    # --- Récupération historique ---
    async def get_historical_data(self, symbol: str, timeframe: str = DEFAULT_TIMEFRAME,
                                  period: str = HISTORY_PERIOD) -> Optional[pd.DataFrame]:
        symbol = normalize_symbol(symbol)
        cache_k = cache_key(symbol, timeframe, period)
        if cache_k in self.history_cache:
            entry = self.history_cache[cache_k]
            if time.time() - entry["timestamp"] < HISTORY_CACHE_TTL:
                return entry["data"]

        df = None
        if FCS_API_KEY:
            df = await self._fetch_fcs_history(symbol, timeframe, period)
        if df is None:
            df = await self._fetch_yahoo_history(symbol, timeframe, period)

        if df is not None and not df.empty:
            self.history_cache[cache_k] = {"data": df, "timestamp": time.time()}
            return df
        return None

    async def _fetch_fcs_history(self, symbol: str, timeframe: str, period: str) -> Optional[pd.DataFrame]:
        # Utilise FCS API pour l'historique
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
            logger.debug(f"FCS history error: {e}")
        return None

    async def _fetch_yahoo_history(self, symbol: str, timeframe: str, period: str) -> Optional[pd.DataFrame]:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=timeframe)
            if df.empty:
                return None
            df.rename(columns={
                "Open": "Open", "High": "High", "Low": "Low",
                "Close": "Close", "Volume": "Volume"
            }, inplace=True)
            return df
        except Exception as e:
            logger.debug(f"Yahoo history error: {e}")
        return None

    def _date_days_ago(self, days: int) -> str:
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")