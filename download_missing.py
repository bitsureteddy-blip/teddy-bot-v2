import yfinance as yf
from datetime import datetime

symbols = {"XAGUSD": "XAGUSD=X", "SPX": "^GSPC", "NDX": "^IXIC"}

for name, ticker in symbols.items():
    print(f"Téléchargement de {name}...")
    df = yf.download(ticker, period="1y", interval="1h")
    if not df.empty:
        df.to_csv(f"data/{name}_1h.csv")
        print(f"  ✅ data/{name}_1h.csv ({len(df)} lignes)")
    else:
        print(f"  ❌ Pas de données pour {name}")