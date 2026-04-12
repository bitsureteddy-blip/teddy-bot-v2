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

    def start_websocket(self):
        # Désactivé pour Railway (plan FREE sans WebSocket)
        pass

    # --- Récupération des prix temps réel ---
    async def get_realtime_price(self, symbol: str) -> Optional[Dict]:
        symbol = normalize_symbol(symbol)
        
        # Essayer Yahoo Finance en premier (plus fiable sur Railway)
        price = await self._fetch_yahoo_price(symbol)
        if price:
            return price
        
        # Essayer RealMarket API
        price = await self._fetch_realmarket_price(symbol)
        if price:
            return price
        
        return None

    async def _fetch_realmarket_price(self, symbol: str) -> Optional[Dict]:
        """Utilise RealMarketAPI comme source secondaire"""
        if not REALMARKET_API_KEY:
            return None
        try:
            url = f"https://api.realmarketapi.com/api/v1/price?ApiKey={REALMARKET_API_KEY}&SymbolCode={symbol}&timeFrame=M1"
            resp = requests.get(url, timeout=10)
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
                logger.warning(f"RealMarket API error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            logger.warning(f"RealMarket error: {e}")
        return None

    async def _fetch_yahoo_price(self, symbol: str) -> Optional[Dict]:
        """Utilise Yahoo Finance via l'API yfinance"""
        try:
            import yfinance as yf
            # Ajouter un suffixe si nécessaire
            if symbol.upper() in ["BTCUSD", "ETHUSD", "XAUUSD"]:
                ticker_symbol = symbol.replace("USD", "-USD")
            elif len(symbol) == 6 and symbol.endswith("USD"):  # Forex
                ticker_symbol = symbol + "=X"
            else:
                ticker_symbol = symbol
            
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
            logger.warning(f"Yahoo Finance error for {symbol}: {e}")
        return None

    # --- Récupération historique ---
    async def get_historical_data(self, symbol: str, timeframe: str = DEFAULT_TIMEFRAME,
                                  period: str = HISTORY_PERIOD) -> Optional[pd.DataFrame]:
        symbol = normalize_symbol(symbol)
        cache_k = cache_key(symbol, timeframe, period)
        if cache_k in self.history_cache:
            entry = self.history_cache[cache_k]
            if time.time() - entry["timestamp"] < HISTORY_CACHE_TTL:
                return entry["data"]

        df = await self._fetch_yahoo_history(symbol, timeframe, period)
        if df is None and FCS_API_KEY:
            df = await self._fetch_fcs_history(symbol, timeframe, period)

        if df is not None and not df.empty:
            self.history_cache[cache_k] = {"data": df, "timestamp": time.time()}
            return df
        return None

    async def _fetch_yahoo_history(self, symbol: str, timeframe: str, period: str) -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf
            if symbol.upper() in ["BTCUSD", "ETHUSD", "XAUUSD"]:
                ticker_symbol = symbol.replace("USD", "-USD")
            elif len(symbol) == 6 and symbol.endswith("USD"):
                ticker_symbol = symbol + "=X"
            else:
                ticker_symbol = symbol
                
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