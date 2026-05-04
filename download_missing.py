import asyncio
import os
os.environ["TELEGRAM_TOKEN"] = "dummy"
os.environ["ADMIN_ID"] = "123456789"
os.environ["TWELVEDATA_API_KEY"] = "c7b582eed7b24bff942030a3623c6429"
os.environ["FCS_API_KEY"] = "0ZTAi2MUQCfr1zD6Dfr86DBXCQQKkDKEY"

from data_fetcher import DataFetcher

async def main():
    fetcher = DataFetcher.get_instance()
    # Essayer différents formats de symboles
    tests = {
        "WTI": ["WTI/USD", "USOIL", "WTI", "CL"],
        "XAGUSD": ["XAG/USD", "XAGUSD"],
        "SPX": ["SPX", "SP500", "US500"],
        "NDX": ["NDX", "NAS100", "US100"],
    }
    
    for original, variants in tests.items():
        print(f"\nEssais pour {original}:")
        for variant in variants:
            print(f"  Test de {variant}...")
            df = await fetcher.get_historical_data(variant, timeframe="1h")
            if df is not None and not df.empty:
                df = df.sort_index()
                filename = f"data/{original}_1h.csv"
                df.to_csv(filename)
                print(f"  ✅ {filename} ({len(df)} lignes)")
                break
        else:
            print(f"  ❌ Aucun format n'a fonctionné pour {original}")

if __name__ == "__main__":
    asyncio.run(main())