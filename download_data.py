import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

# Forcer les variables d'environnement manquantes
os.environ["TELEGRAM_TOKEN"] = "dummy"
os.environ["ADMIN_ID"] = "123456789"
os.environ["TWELVEDATA_API_KEY"] = "c7b582eed7b24bff942030a3623c6429"

from data_fetcher import DataFetcher

SYMBOLS = [
    "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "XAUUSD", "WTI", "XAGUSD",
    "AAPL", "TSLA", "NVDA", "SPX", "NDX"
]
TIMEFRAME = "1h"

async def main():
    os.makedirs("data", exist_ok=True)
    fetcher = DataFetcher.get_instance()

    for symbol in SYMBOLS:
        print(f"Téléchargement de {symbol}...")
        df = await fetcher.get_historical_data(symbol, timeframe=TIMEFRAME)
        if df is None or df.empty:
            print(f"  ❌ Pas de données pour {symbol}")
            continue
        df = df.sort_index()
        filename = f"data/{symbol}_{TIMEFRAME}.csv"
        df.to_csv(filename)
        print(f"  ✅ {filename} ({len(df)} lignes)")

if __name__ == "__main__":
    asyncio.run(main())