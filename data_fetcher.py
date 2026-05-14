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
    FCS_API_KEY, TWELVEDATA_API_KEY, REALMARKET_API_KEY,
    PRICE_CACHE_TTL, HISTORY_CACHE_TTL,
    DEFAULT_TIMEFRAME, HISTORY_PERIOD,
    TWELVEDATA_WS_URL, FCS_WS_URL, REALMARKET_WS_URL, FCS_WS_KEY
)
from utils import cache_key, normalize_symbol

logger = logging.getLogger(__name__)


class DataFetcher:
    _instance = None

    def __init__(self):
        self.price_cache = {}
        self.history_cache = {}
        self.tick_history = {}
        self.subscribed_symbols = set(["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "AAPL", "TSLA", "NVDA"])
        self.ws = None
        self.ws_thread = None
        self.active_source = None
        self.source_failures = {"twelve": 0, "fcs": 0, "real": 0}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _close_active_ws(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None
        self.ws_thread = None

    # ========== DÉMARRAGE PRINCIPAL ==========

    def start_websocket(self):
        """Démarre la source principale (Twelve Data) avec fallback automatique."""
        self._start_twelve_ws()

    # ========== TWELVE DATA ==========

    def _start_twelve_ws(self):
        self._close_active_ws()
        if not TWELVEDATA_API_KEY:
            logger.warning("Twelve Data: pas de clé API, bascule sur FCS")
            self._start_fcs_ws()
            return

        def on_open(ws):
            formatted = [self._format_symbol(s) for s in sorted(self.subscribed_symbols)]
            ws.send(json.dumps({"action": "subscribe", "params": {"symbols": ",".join(formatted)}}))
            self.active_source = "twelve"
            self.source_failures["twelve"] = 0
            logger.info("✅ Twelve Data WebSocket actif")

        def on_error(ws, err):
            logger.error(f"Twelve WS error: {err}")
            self.source_failures["twelve"] += 1
            if self.source_failures["twelve"] >= 3:
                logger.warning("⚠️ Bascule source: twelve -> fcs")
                self._start_fcs_ws()

        self.ws = websocket.WebSocketApp(
            f"{TWELVEDATA_WS_URL}?apikey={TWELVEDATA_API_KEY}",
            on_open=on_open,
            on_message=lambda ws, msg: self._on_twelve_message(msg),
            on_error=on_error,
            on_close=lambda ws, *args: self._on_source_close("twelve")
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def _on_twelve_message(self, message):
        try:
            data = json.loads(message)
            if data.get("event") != "price":
                return
            symbol = normalize_symbol(data.get("symbol", ""))
            price = float(data.get("price", 0))
            raw_bid = data.get("bid")
            raw_ask = data.get("ask")
            if raw_bid is not None and raw_ask is not None:
                bid = float(raw_bid)
                ask = float(raw_ask)
            else:
                spread = max(price * 0.0005, 0.0001)
                bid = price - spread / 2
                ask = price + spread / 2
            self.price_cache[symbol] = {"price": price, "bid": bid, "ask": ask, "timestamp": time.time()}
            self.add_tick(symbol, price)
        except Exception as e:
            logger.debug(f"Twelve WS parse error: {e}")

    # ========== FCS API ==========

    def _start_fcs_ws(self):
        self._close_active_ws()
        if not FCS_WS_KEY:
            logger.warning("FCS: pas de clé WebSocket, bascule sur RealMarket")
            self._start_real_ws()
            return

        def on_open(ws):
            self.active_source = "fcs"
            self.source_failures["fcs"] = 0
            logger.info("✅ FCS WebSocket actif")
            formatted = [self._format_symbol_fcs(s) for s in sorted(self.subscribed_symbols)]
            ws.send(json.dumps({"type": "subscribe", "symbol": ",".join(formatted)}))

        def on_message(ws, message):
            data = json.loads(message)
            if data.get("type") == "price":
                symbol = normalize_symbol(data.get("symbol", "").replace("FX:", "").replace("BINANCE:", "").replace("NASDAQ:", ""))
                prices = data.get("prices", {})
                price = float(prices.get("c", 0))
                bid = float(prices.get("b", price * 0.9995))
                ask = float(prices.get("a", price * 1.0005))
                self.price_cache[symbol] = {"price": price, "bid": bid, "ask": ask, "timestamp": time.time()}
                self.add_tick(symbol, price)

        def on_error(ws, err):
            logger.error(f"FCS WS error: {err}")
            self.source_failures["fcs"] += 1
            if self.source_failures["fcs"] >= 3:
                logger.warning("⚠️ Bascule source: fcs -> real")
                self._start_real_ws()

        self.ws = websocket.WebSocketApp(
            f"{FCS_WS_URL}?access_key={FCS_WS_KEY}"
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=lambda ws, *args: self._on_source_close("fcs")
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def _format_symbol_fcs(self, symbol):
        s = symbol.upper()
        if s in ["BTCUSD", "ETHUSD"]:
            return f"BINANCE:{s}"
        elif s in ["AAPL", "TSLA", "NVDA"]:
            return f"NASDAQ:{s}"
        else:
            return f"FX:{s}"

    # ========== REALMARKET API ==========

    def _start_real_ws(self):
        self._close_active_ws()
        if not REALMARKET_API_KEY:
            logger.error("❌ Aucune source WebSocket disponible")
            self.active_source = None
            return

        def on_open(ws):
            self.active_source = "real"
            self.source_failures["real"] = 0
            logger.info("✅ RealMarket WebSocket actif")
            # Abonnement aux symboles supportés par RealMarket
            real_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "BTCUSD", "ETHUSD", "AAPL", "TSLA", "NVDA"]
            available = [s for s in real_symbols if s in self.subscribed_symbols]
            if available:
                ws.send(json.dumps({"action": "subscribe", "params": {"symbols": ",".join(available)}}))

        def on_message(ws, message):
            try:
                data = json.loads(message)
                symbol = normalize_symbol(data.get("SymbolCode", ""))
                price = float(data.get("ClosePrice", 0))
                bid = float(data.get("Bid", price * 0.9995))
                ask = float(data.get("Ask", price * 1.0005))
                self.price_cache[symbol] = {"price": price, "bid": bid, "ask": ask, "timestamp": time.time()}
                self.add_tick(symbol, price)
            except Exception as e:
                logger.debug(f"RealMarket WS parse error: {e}")

        def on_error(ws, err):
            logger.error(f"RealMarket WS error: {err}")
            self.source_failures["real"] += 1

        self.ws = websocket.WebSocketApp(
            f"{REALMARKET_WS_URL}?ApiKey={REALMARKET_API_KEY}",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=lambda ws, *args: self._on_source_close("real")
        )
        self.ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.ws_thread.start()

    def _on_source_close(self, source):
        logger.warning(f"⚠️ {source} WebSocket fermé")
        if source == "twelve" and self.active_source == "twelve":
            logger.warning("⚠️ Bascule source: twelve -> fcs")
            self._start_fcs_ws()
        elif source == "fcs" and self.active_source == "fcs":
            logger.warning("⚠️ Bascule source: fcs -> real")
            self._start_real_ws()
        elif source == "real" and self.active_source == "real":
            self.active_source = None
            logger.error("❌ Toutes les sources WebSocket sont down; fallback REST actif")

    def subscribe_twelvedata(self, symbol: str):
        symbol = normalize_symbol(symbol)
        self.subscribed_symbols.add(symbol)
        if self.active_source == "twelve" and self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({"action": "subscribe", "params": {"symbols": self._format_symbol(symbol)}}))
        elif self.active_source == "fcs" and self.ws and self.ws.sock and self.ws.sock.connected:
            self.ws.send(json.dumps({"type": "subscribe", "symbol": self._format_symbol_fcs(symbol)}))

    def add_tick(self, symbol: str, price: float):
        symbol = normalize_symbol(symbol)
        self.tick_history.setdefault(symbol, []).append(price)
        self.tick_history[symbol] = self.tick_history[symbol][-100:]

    def get_ticks(self, symbol: str):
        symbol = normalize_symbol(symbol)
        return list(self.tick_history.get(symbol, []))

    def get_cached_price(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)
        if symbol in self.price_cache:
            if time.time() - self.price_cache[symbol]["timestamp"] < PRICE_CACHE_TTL:
                return self.price_cache[symbol]
        return None

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
        if s == "XAGUSD":
            return "XAG/USD"
        if s == "XAUUSD":
            return "XAU/USD"
        if s in ["AAPL", "TSLA", "NVDA"]:
            return s
        if s == "SPX":
            return "SPX"
        if s == "NDX":
            return "NDX"
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
            url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval={interval}&outputsize=5000&apikey={TWELVEDATA_API_KEY}"
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
