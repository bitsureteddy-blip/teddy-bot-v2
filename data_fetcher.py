import json
import time
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import requests
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
        # WebSocket désactivé par défaut (gratuit)
        self.ws_enabled = False
        self.tick_history = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_websocket(self):
        """Méthode de compatibilité (WebSocket désactivé)."""
        logger.info("WebSocket non activé (plan gratuit).")
        pass

    # =========================
    # 💰 PRIX TEMPS RÉEL
    # =========================
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Retourne le prix actuel (float) pour un symbole."""
        data = self._fetch_price_sync(symbol)
        if data:
            return data.get("price")
        return None

    def get_current_price_full(self, symbol: str) -> Optional[Dict]:
        """Retourne un dict complet avec 'price', 'bid', 'ask'."""
        return self._fetch_price_sync(symbol)

    def _fetch_price_sync(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)

        # Vérifier le cache
        if symbol in self.price_cache:
            if time.time() - self.price_cache[symbol]["timestamp"] < PRICE_CACHE_TTL:
                return self.price_cache[symbol]

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
                    # Spread estimé
                    spread = max(price * 0.0003, 0.0001)
                    bid = price - spread / 2
                    ask = price + spread / 2
                else:
                    bid = float(bid)
                    ask = float(ask)

                result = {
                    "price": price,
                    "bid": bid,
                    "ask": ask,
                    "timestamp": time.time()
                }
                self.price_cache[symbol] = result
                return result
        except Exception as e:
            logger.warning(f"Price error {symbol}: {e}")
        return None

    # =========================
    # 🔧 FORMATAGE SYMBOLE
    # =========================
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

    # =========================
    # 📊 HISTORIQUE (SYNCHRONE)
    # =========================
    def get_historical_data(self, symbol: str, timeframe: str = DEFAULT_TIMEFRAME,
                            limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Récupère les données historiques.
        - timeframe: "1m", "5m", "1h", "4h", "1d"
        - limit: nombre de bougies à récupérer
        """
        symbol = normalize_symbol(symbol)
        key = f"{symbol}_{timeframe}_{limit}"

        if key in self.history_cache:
            if time.time() - self.history_cache[key]["timestamp"] < HISTORY_CACHE_TTL:
                return self.history_cache[key]["data"]

        df = self._fetch_history(symbol, timeframe, limit)
        if df is None and FCS_API_KEY:
            df = self._fetch_fcs_history(symbol, timeframe, limit)
        if df is None:
            df = self._fetch_yahoo_history(symbol, timeframe, limit)

        if df is not None and not df.empty:
            self.history_cache[key] = {"data": df, "timestamp": time.time()}
            return df
        return None

    def _fetch_history(self, symbol: str, timeframe: str, limit: int):
        try:
            td_symbol = self._format_symbol(symbol)

            interval_map = {"1m": "1min", "5m": "5min", "1h": "1h", "4h": "4h", "1d": "1day"}
            interval = interval_map.get(timeframe, "1day")

            url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval={interval}&outputsize={limit}&apikey={TWELVEDATA_API_KEY}"
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
                df = df.iloc[::-1]  # du plus ancien au plus récent
                df["Date"] = pd.to_datetime(df["Date"])
                df.set_index("Date", inplace=True)
                for col in ["Open", "High", "Low", "Close", "Volume"]:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
        except Exception as e:
            logger.warning(f"History error {symbol}: {e}")
        return None

    def _fetch_yahoo_history(self, symbol: str, timeframe: str, limit: int):
        try:
            import yfinance as yf

            # Déterminer la période en fonction du nombre de bougies
            if timeframe in ["1m", "5m"]:
                period = "5d"
            elif timeframe == "1h":
                period = "1mo"
            else:
                period = "3mo"

            if symbol.upper() in ["BTCUSD", "ETHUSD", "XAUUSD"]:
                ticker = symbol.replace("USD", "-USD")
            elif len(symbol) == 6 and symbol.endswith("USD"):
                ticker = symbol + "=X"
            else:
                ticker = symbol

            df = yf.Ticker(ticker).history(period=period, interval=timeframe)
            if df.empty:
                return None
            # Limiter au nombre demandé
            return df.tail(limit)
        except Exception as e:
            logger.warning(f"Yahoo fallback error: {e}")
        return None

    def _fetch_fcs_history(self, symbol: str, timeframe: str, limit: int):
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
                    return df.tail(limit)
        except Exception as e:
            logger.warning(f"FCS fallback error: {e}")
        return None