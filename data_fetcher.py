import asyncio
import json
import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import requests
import websocket
import threading
import pandas as pd

from config import (
    FCS_API_KEY, TWELVEDATA_API_KEY,
    PRICE_CACHE_TTL, HISTORY_CACHE_TTL,
    DEFAULT_TIMEFRAME, HISTORY_PERIOD
)
from utils import cache_key, normalize_symbol

logger = logging.getLogger(__name__)


class DataFetcher:
    _instance = None
def __init__(self):
        self.price_cache = {}
        self.history_cache = {}
        self.ws_twelvedata = None
        self.ws_thread = None
        self.ws_running = False
        self.subscribed_symbols = set()
        self.ws_authenticated = False
        self.tick_history = {}
        self.ws = None              # <-- AJOUTE ICI
        self.ws_thread = None       # <-- ET ICI

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_websocket(self):
        """Méthode de compatibilité appelée par main.py"""
        self.start_twelvedata_websocket()

    def start_twelvedata_websocket(self):
        # Désactivé car le plan gratuit Twelve Data ne supporte pas le WebSocket
        logger.info("Twelve Data WebSocket désactivé (plan gratuit)")
        pass

    def _run_ws(self):
        while self.ws_running:
            try:
                ws = websocket.WebSocketApp(
                    "wss://ws.twelvedata.com/v1/quotes/price",
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self.ws_twelvedata = ws
                self.ws_authenticated = False
                ws.run_forever()
            except Exception as e:
                logger.error(f"WS error: {e}")
            time.sleep(5)

    def _on_open(self, ws):
        logger.info("WS connected")
        ws.send(json.dumps({
            "action": "auth",
            "params": {"apikey": TWELVEDATA_API_KEY}
        }))

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)

            if data.get("event") == "price":
                symbol = data.get("symbol")
                price = float(data.get("price", 0))

                bid = data.get("bid")
                ask = data.get("ask")

                if bid is None or ask is None:
                    spread = max(price * 0.0003, 0.0001)
                    bid = price - spread / 2
                    ask = price + spread / 2
                else:
                    bid = float(bid)
                    ask = float(ask)

                self.price_cache[symbol] = {
                    "price": price,
                    "bid": bid,
                    "ask": ask,
                    "timestamp": time.time()
                }

                self.add_tick(symbol, price)

            elif data.get("status") == "ok":
                self.ws_authenticated = True
                logger.info("WS authenticated")

                if self.subscribed_symbols:
                    ws.send(json.dumps({
                        "action": "subscribe",
                        "params": {"symbols": ",".join(self.subscribed_symbols)}
                    }))

        except Exception as e:
            logger.error(f"WS message error: {e}")

    def _on_error(self, ws, error):
        logger.error(f"WS error: {error}")

    def _on_close(self, ws, *args):
        logger.info("WS closed")
        self.ws_authenticated = False

    def subscribe_twelvedata(self, symbol: str):
        symbol = normalize_symbol(symbol)
        self.subscribed_symbols.add(symbol)

        if self.ws_authenticated and self.ws_twelvedata and self.ws_twelvedata.sock and self.ws_twelvedata.sock.connected:
            self.ws_twelvedata.send(json.dumps({
                "action": "subscribe",
                "params": {"symbols": symbol}
            }))

    def add_tick(self, symbol: str, price: float):
        symbol = normalize_symbol(symbol)
        if symbol not in self.tick_history:
            self.tick_history[symbol] = []
        self.tick_history[symbol].append(price)
        if len(self.tick_history[symbol]) > 30:
            self.tick_history[symbol].pop(0)

    async def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)

        if symbol in self.price_cache:
            if time.time() - self.price_cache[symbol]["timestamp"] < PRICE_CACHE_TTL:
                return self.price_cache[symbol]

        price = await self._fetch_price(symbol)
        if price:
            self.price_cache[symbol] = price
            return price
        return None

    async def _fetch_price(self, symbol: str) -> Optional[Dict]:
        if not TWELVEDATA_API_KEY:
            return None

        try:
            td_symbol = self._format_symbol(symbol)
            url = f"https://api.twelvedata.com/quote?symbol={td_symbol}&apikey={TWELVEDATA_API_KEY}"
            r = requests.get(url, timeout=10)

            if r.status_code == 200:
                data = r.json()
                price = float(data.get("close") or data.get("price", 0))

                bid = data.get("bid")
                ask = data.get("ask")

                if bid is None or ask is None:
                    spread = max(price * 0.0003, 0.0001)
                    bid = price - spread / 2
                    ask = price + spread / 2
                else:
                    bid = float(bid)
                    ask = float(ask)

                return {
                    "price": price,
                    "bid": bid,
                    "ask": ask,
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.warning(f"Price error {symbol}: {e}")
        return None

    def _format_symbol(self, symbol: str) -> str:
        s = symbol.upper()

        crypto_list = ["BTC", "ETH", "XRP", "SOL", "ADA", "BNB", "LTC", "BCH", "DOT", "LINK"]
        for crypto in crypto_list:
            if s == f"{crypto}USD":
                return f"{crypto}/USD"

        if len(s) == 6:
            return f"{s[:3]}/{s[3:]}"

        if s == "XAUUSD":
            return "XAU/USD"
        if s == "XAGUSD":
            return "XAG/USD"

        if s in ["USOIL", "WTI"]:
            return "WTI/USD"
        if s == "UKOIL":
            return "BRENT/USD"

        return s

    async def get_historical_data(self, symbol: str, timeframe: str = DEFAULT_TIMEFRAME,
                                  period: str = HISTORY_PERIOD) -> Optional[pd.DataFrame]:
        symbol = normalize_symbol(symbol)
        key = cache_key(symbol, timeframe, period)

        if key in self.history_cache:
            if time.time() - self.history_cache[key]["timestamp"] < HISTORY_CACHE_TTL:
                return self.history_cache[key]["data"]

        df = await self._fetch_history(symbol, timeframe)
        if df is None and FCS_API_KEY:
            df = await self._fetch_fcs_history(symbol, timeframe, period)
        if df is None:
            df = await self._fetch_yahoo_history(symbol, timeframe, period)

        if df is not None and not df.empty:
            self.history_cache[key] = {"data": df, "timestamp": time.time()}
            return df
        return None

    async def _fetch_history(self, symbol: str, timeframe: str):
        try:
            td_symbol = self._format_symbol(symbol)

            interval_map = {"1m": "1min", "5m": "5min", "1h": "1h", "4h": "4h", "1d": "1day"}
            interval = interval_map.get(timeframe, "1day")

            url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval={interval}&outputsize=200&apikey={TWELVEDATA_API_KEY}"
            r = requests.get(url, timeout=10)

            if r.status_code == 200:
                data = r.json().get("values", [])
                if not data:
                    return None

                df = pd.DataFrame(data)
                df = df.rename(columns={
                    "datetime": "Date", "open": "Open", "high": "High",
                    "low": "Low", "close": "Close", "volume": "Volume"
                })
                df = df.iloc[::-1]
                df["Date"] = pd.to_datetime(df["Date"])
                df.set_index("Date", inplace=True)
                return df.astype(float)
        except Exception as e:
            logger.warning(f"History error {symbol}: {e}")
        return None

    async def _fetch_yahoo_history(self, symbol: str, timeframe: str, period: str):
        try:
            import yfinance as yf
            if symbol.upper() in ["BTCUSD", "ETHUSD", "XAUUSD"]:
                ticker = symbol.replace("USD", "-USD")
            elif len(symbol) == 6 and symbol.endswith("USD"):
                ticker = symbol + "=X"
            else:
                ticker = symbol
            df = yf.Ticker(ticker).history(period=period, interval=timeframe)
            return df if not df.empty else None
        except Exception as e:
            logger.warning(f"Yahoo fallback error: {e}")
        return None

    async def _fetch_fcs_history(self, symbol: str, timeframe: str, period: str):
        if not FCS_API_KEY:
            return None
        try:
            days = 180
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")
            url = f"https://fcsapi.com/api-v3/forex/history?symbol={symbol}&period={timeframe}&from={from_date}&to={to_date}&access_key={FCS_API_KEY}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
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
            logger.warning(f"FCS fallback error: {e}")
        return None
    def on_message(self, ws, message):
        """Reçoit un tick de Binance et le stocke."""
        import json
        data = json.loads(message)
        price = float(data['p'])
        symbol = "BTCUSD"
        self.add_tick(symbol, price)

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("Binance WebSocket closed")

    def on_open(self, ws):
        logger.info("✅ Binance WebSocket connecté")

        def start_binance_ws(self):
        """Lance le flux Binance dans un thread séparé."""
        ws_url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()