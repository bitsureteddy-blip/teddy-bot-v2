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
    PRICE_CACHE_TTL, HISTORY_CACHE_TTL, DEFAULT_TIMEFRAME, HISTORY_PERIOD
)
from utils import cache_key, normalize_symbol

logger = logging.getLogger(__name__)


class DataFetcher:
    _instance = None

    def __init__(self):
        self.price_cache = {}
        self.history_cache = {}
        self.ws_twelvedata = None
        self.ws_twelvedata_thread = None
        self.ws_twelvedata_running = False
        self.subscribed_symbols = set()
        self.twelvedata_callbacks = {}
        self.ws_twelvedata_authenticated = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # =========================
    # WEBSOCKET (OPTIONNEL)
    # =========================
    def start_websocket(self):
        pass

    def start_twelvedata_websocket(self):
        if self.ws_twelvedata_running:
            return

        self.ws_twelvedata_running = True
        self.ws_twelvedata_thread = threading.Thread(
            target=self._run_twelvedata_websocket,
            daemon=True
        )
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
                self.ws_twelvedata_authenticated = False
                ws.run_forever()
            except Exception as e:
                logger.error(f"WebSocket error: {e}")

            time.sleep(5)

        def _on_open_twelvedata(self, ws):
        logger.info("Twelve Data WebSocket connected, sending authentication...")
        auth_msg = {
            "action": "auth",
            "params": {
                "apikey": TWELVEDATA_API_KEY
            }
        }
        ws.send(json.dumps(auth_msg))
    def _on_message_twelvedata(self, ws, message):
        try:
            data = json.loads(message)

            if data.get("event") == "price":
                symbol = data.get("symbol")
                price = float(data.get("price", 0))

                bid = data.get("bid")
                ask = data.get("ask")

                # FIX IMPORTANT : toujours avoir bid != ask
                if bid is None or ask is None:
                    spread = price * 0.0005
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

                if symbol in self.twelvedata_callbacks:
                    for cb in self.twelvedata_callbacks[symbol]:
                        cb(symbol, price, bid, ask)

            elif not self.ws_twelvedata_authenticated and data.get("status") == "ok":
                self.ws_twelvedata_authenticated = True
                logger.info("WS authenticated")

                if self.subscribed_symbols:
                    ws.send(json.dumps({
                        "action": "subscribe",
                        "params": {"symbols": ",".join(self.subscribed_symbols)}
                    }))

        except Exception as e:
            logger.error(f"WS message error: {e}")

    def _on_error_twelvedata(self, ws, error):
        logger.error(f"WS error: {error}")

    def _on_close_twelvedata(self, ws, *args):
        logger.info("WS closed")
        self.ws_twelvedata_authenticated = False

    def subscribe_twelvedata(self, symbol: str, callback=None):
        symbol = normalize_symbol(symbol)
        self.subscribed_symbols.add(symbol)

        if callback:
            self.twelvedata_callbacks.setdefault(symbol, []).append(callback)

    # =========================
    # PRICE
    # =========================
    async def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)

        cache = self.price_cache.get(symbol)
        if cache and time.time() - cache["timestamp"] < PRICE_CACHE_TTL:
            return cache

        price = await self._fetch_twelvedata_price(symbol)

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

            if resp.status_code != 200:
                return None

            data = resp.json()

            price_str = data.get("close") or data.get("price")
            if price_str is None:
                return None

            price = float(price_str)

            bid = data.get("bid")
            ask = data.get("ask")

            # FIX CRITIQUE
            if bid is not None and ask is not None:
                bid = float(bid)
                ask = float(ask)
            else:
                spread = price * 0.0005
                bid = price - spread / 2
                ask = price + spread / 2

            return {
                "price": price,
                "bid": bid,
                "ask": ask,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.warning(f"Price error {symbol}: {e}")
            return None

    # =========================
    # SYMBOL FIX (AMÉLIORÉ)
    # =========================
    def _to_twelvedata_symbol(self, symbol: str) -> str:
        s = symbol.upper()

        # CRYPTO
        if s.endswith("USD") and s[:-3] in ["BTC", "ETH", "XRP", "SOL", "ADA", "BNB"]:
            return s[:-3] + "/USD"

        # FOREX (support massif)
        if len(s) == 6:
            return f"{s[:3]}/{s[3:]}"

        # GOLD / SILVER
        if s == "XAUUSD":
            return "XAU/USD"
        if s == "XAGUSD":
            return "XAG/USD"

        # OIL
        if s in ["USOIL", "WTI"]:
            return "WTI/USD"
        if s == "UKOIL":
            return "BRENT/USD"

        # ACTIONS → IMPORTANT
        return s

    # =========================
    # HISTORY
    # =========================
    async def get_historical_data(self, symbol: str,
                                 timeframe: str = DEFAULT_TIMEFRAME,
                                 period: str = HISTORY_PERIOD) -> Optional[pd.DataFrame]:

        symbol = normalize_symbol(symbol)
        cache_k = cache_key(symbol, timeframe, period)

        entry = self.history_cache.get(cache_k)
        if entry and time.time() - entry["timestamp"] < HISTORY_CACHE_TTL:
            return entry["data"]

        df = await self._fetch_twelvedata_history(symbol, timeframe)

        if df is None:
            df = await self._fetch_yahoo_history(symbol, timeframe, period)

        if df is not None and not df.empty:
            self.history_cache[cache_k] = {
                "data": df,
                "timestamp": time.time()
            }
            return df

        return None

    async def _fetch_twelvedata_history(self, symbol: str, timeframe: str):
        try:
            interval_map = {
                "1d": "1day",
                "1h": "1h",
                "4h": "4h"
            }

            interval = interval_map.get(timeframe, "1day")

            url = f"https://api.twelvedata.com/time_series?symbol={self._to_twelvedata_symbol(symbol)}&interval={interval}&outputsize=200&apikey={TWELVEDATA_API_KEY}"

            resp = requests.get(url, timeout=10)
            data = resp.json()

            values = data.get("values")
            if not values:
                return None

            df = pd.DataFrame(values)
            df.rename(columns={
                "datetime": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            }, inplace=True)

            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)

            return df[::-1]

        except Exception as e:
            logger.warning(f"History error: {e}")
            return None

    async def _fetch_yahoo_history(self, symbol: str, timeframe: str, period: str):
        try:
            import yfinance as yf

            if len(symbol) == 6:
                ticker_symbol = symbol + "=X"
            elif symbol.endswith("USD"):
                ticker_symbol = symbol.replace("USD", "-USD")
            else:
                ticker_symbol = symbol

            df = yf.Ticker(ticker_symbol).history(period=period, interval=timeframe)

            return df if not df.empty else None

        except Exception as e:
            logger.warning(f"Yahoo error: {e}")
            return None