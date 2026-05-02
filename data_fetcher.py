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
        self.tick_history = {}
        self.subscribed_symbols = set(["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "WTI", "XAGUSD", "AAPL", "TSLA", "NVDA", "SPX", "NDX"])
        self.ws = None
        self.ws_thread = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_websocket(self):
        self.start_twelvedata_websocket()

    def start_twelvedata_websocket(self):
        if not TWELVEDATA_API_KEY or (self.ws_thread and self.ws_thread.is_alive()):
            return

        def on_open(ws):
            ws.send(json.dumps({"action": "auth", "params": {"apikey": TWELVEDATA_API_KEY}}))

        self.ws = websocket.WebSocketApp(
            "wss://ws.twelvedata.com/v1/quotes/price",
            on_open=on_open,
            on_message=lambda ws, msg: self._on_twelve_message(msg),
            on_error=lambda ws, err: logger.error(f"Twelve WS error: {err}"),
            on_close=lambda ws, *args: logger.info("Twelve WS closed")
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def _on_twelve_message(self, message):
        try:
            data = json.loads(message)
            event = data.get("event")

            if event == "subscribe-status" and data.get("status") == "ok" and self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(json.dumps({"action": "subscribe", "params": {"symbols": ",".join(sorted(self.subscribed_symbols))}}))
                return

            if event != "price":
                return

            symbol = normalize_symbol(data.get("symbol", ""))
            price = float(data.get("price", 0))
            bid = float(data.get("bid", price - max(price * 0.0005, 0.0001)))
            ask = float(data.get("ask", price + max(price * 0.0005, 0.0001)))
            self.price_cache[symbol] = {"price": price, "bid": bid, "ask": ask, "timestamp": time.time()}
            self.add_tick(symbol, price)
        except Exception as e:
            logger.debug(f"WS parse error: {e}")

    def subscribe_twelvedata(self, symbol: str):
        symbol = normalize_symbol(symbol)
        self.subscribed_symbols.add(symbol)
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({"action": "subscribe", "params": {"symbols": symbol}}))

    def add_tick(self, symbol: str, price: float):
        symbol = normalize_symbol(symbol)
        self.tick_history.setdefault(symbol, []).append(price)
        self.tick_history[symbol] = self.tick_history[symbol][-100:]

    def get_ticks(self, symbol: str):
        symbol = normalize_symbol(symbol)
        return list(self.tick_history.get(symbol, []))

    async def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)
        if symbol in self.price_cache and time.time() - self.price_cache[symbol]["timestamp"] < PRICE_CACHE_TTL:
            p = self.price_cache[symbol]
            if p["ask"] <= p["bid"]:
                spread = max(p["price"] * 0.0005, 0.0001)
                p["bid"] = p["price"] - spread / 2
                p["ask"] = p["price"] + spread / 2
            return p
        price = await self._fetch_price(symbol)
        if price:
            self.price_cache[symbol] = price
        return price

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
                bid = float(data.get("bid", price - max(price * 0.0005, 0.0001)))
                ask = float(data.get("ask", price + max(price * 0.0005, 0.0001)))
                return {"price": price, "bid": bid, "ask": ask, "timestamp": time.time()}
        except Exception as e:
            logger.warning(f"Price error {symbol}: {e}")
        return None

    def _format_symbol(self, symbol: str) -> str:
        s = symbol.upper()
        if len(s) == 6:
            return f"{s[:3]}/{s[3:]}"
        if s == "WTI":
            return "WTI/USD"
        return s

    async def get_historical_data(self, symbol: str, timeframe: str = DEFAULT_TIMEFRAME, period: str = HISTORY_PERIOD) -> Optional[pd.DataFrame]:
        symbol = normalize_symbol(symbol)
        key = cache_key(symbol, timeframe, period)
        if key in self.history_cache and time.time() - self.history_cache[key]["timestamp"] < HISTORY_CACHE_TTL:
            return self.history_cache[key]["data"]
        df = await self._fetch_history(symbol, timeframe)
        if df is None and FCS_API_KEY:
            df = await self._fetch_fcs_history(symbol, timeframe, period)
        if df is not None and not df.empty:
            self.history_cache[key] = {"data": df, "timestamp": time.time()}
            return df
        return None

    async def _fetch_history(self, symbol: str, timeframe: str):
        try:
            td_symbol = self._format_symbol(symbol)
            interval = {"1m": "1min", "5m": "5min", "1h": "1h", "4h": "4h", "1d": "1day"}.get(timeframe, "1day")
            url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval={interval}&outputsize=200&apikey={TWELVEDATA_API_KEY}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json().get("values", [])
                if not data:
                    return None
                df = pd.DataFrame(data).rename(columns={"datetime": "Date", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
                df = df.iloc[::-1]
                df["Date"] = pd.to_datetime(df["Date"])
                df.set_index("Date", inplace=True)
                return df.astype(float)
        except Exception as e:
            logger.warning(f"History error {symbol}: {e}")
        return None

    async def _fetch_fcs_history(self, symbol: str, timeframe: str, period: str):
        try:
            from_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")
            url = f"https://fcsapi.com/api-v3/forex/history?symbol={symbol}&period={timeframe}&from={from_date}&to={to_date}&access_key={FCS_API_KEY}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("code") == 200 and data.get("response"):
                    rows = [{"Date": i["date"], "Open": float(i["o"]), "High": float(i["h"]), "Low": float(i["l"]), "Close": float(i["c"]), "Volume": float(i.get("v", 0))} for i in data["response"]]
                    df = pd.DataFrame(rows)
                    df["Date"] = pd.to_datetime(df["Date"])
                    df.set_index("Date", inplace=True)
                    return df
        except Exception as e:
            logger.warning(f"FCS fallback error: {e}")
        return None
