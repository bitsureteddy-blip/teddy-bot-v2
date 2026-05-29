"""
Backtest Bitsure Teddy - strict, transparent, 100% reproductible
Utilise les CSV locaux (pas d'API).
"""

import os
os.environ["TELEGRAM_TOKEN"] = "dummy"
os.environ["ADMIN_ID"] = "123456789"

import pandas as pd
import numpy as np
from signal_engine import SignalEngine
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backtest")

SYMBOLS = [
    "BTCUSD", "ETHUSD",
    "AUDUSD",
    "XAUUSD",
    "AAPL", "TSLA", "NVDA"
]
TIMEFRAME = "1h"
MIN_BARS = 60
STEP = 24
SL_ATR_MULT = 1.5
TP_ATR_MULT = 2.0

def run_backtest():
    engine = SignalEngine()

    for symbol in SYMBOLS:
        logger.info(f"=== BACKTEST {symbol} ===")
        filename = f"data/{symbol}_{TIMEFRAME}.csv"
        if not os.path.exists(filename):
            logger.warning(f"Fichier introuvable : {filename}")
            continue

        df = pd.read_csv(filename, parse_dates=["Date"], index_col="Date")
        df = df.sort_index()

        logger.info(f"{len(df)} bougies chargées.")
        trades = []

        for i in range(MIN_BARS, len(df) - 1, STEP):
            window = df.iloc[:i]
            result = engine.analyze(window, symbol=symbol)

            if result["signal"] not in ("BUY", "SELL"):
                continue

            entry_price = float(df["Open"].iloc[i + 1])
            sl = float(result["sl"])
            tp = float(result["tp1"])
            if sl is None or tp is None or sl == entry_price:
                continue

            is_buy = result["signal"] == "BUY"
            outcome = None
            exit_price = None
            exit_idx = i + 1

            for j in range(i + 1, len(df)):
                low_j = float(df["Low"].iloc[j])
                high_j = float(df["High"].iloc[j])

                if is_buy:
                    if low_j <= sl:
                        outcome = "LOSS"
                        exit_price = sl
                        exit_idx = j
                        break
                    if high_j >= tp:
                        outcome = "WIN"
                        exit_price = tp
                        exit_idx = j
                        break
                else:
                    if high_j >= sl:
                        outcome = "LOSS"
                        exit_price = sl
                        exit_idx = j
                        break
                    if low_j <= tp:
                        outcome = "WIN"
                        exit_price = tp
                        exit_idx = j
                        break

            if outcome is None:
                exit_price = float(df["Close"].iloc[-1])
                exit_idx = len(df) - 1
                if is_buy:
                    outcome = "WIN" if exit_price > entry_price else "LOSS"
                else:
                    outcome = "WIN" if exit_price < entry_price else "LOSS"

            pnl_pct = ((exit_price - entry_price) / entry_price * 100)
            if not is_buy:
                pnl_pct = -pnl_pct

            trades.append({
                "date": str(df.index[i + 1]),
                "symbol": symbol,
                "signal": result["signal"],
                "score": result["teddy_score"],
                "entry": round(entry_price, 5),
                "exit": round(exit_price, 5),
                "sl": round(sl, 5),
                "tp": round(tp, 5),
                "outcome": outcome,
                "pnl_pct": round(pnl_pct, 4),
                "bars_held": exit_idx - (i + 1),
            })

        if not trades:
            logger.info("Aucun trade.")
            continue

        trades_df = pd.DataFrame(trades)
        total = len(trades_df)
        wins = (trades_df["outcome"] == "WIN").sum()
        losses = total - wins
        win_rate = wins / total * 100
        avg_pnl = trades_df["pnl_pct"].mean()
        total_pnl = trades_df["pnl_pct"].sum()
        best = trades_df["pnl_pct"].max()
        worst = trades_df["pnl_pct"].min()
        avg_bars = trades_df["bars_held"].mean()

        cumul = trades_df["pnl_pct"].cumsum()
        max_drawdown = (cumul.cummax() - cumul).max()

        print(f"""
📊 {symbol} – Résultats du backtest
━━━━━━━━━━━━━━━━━━━━━━━━
🔢 Trades        : {total}
✅ Gagnants      : {wins} ({win_rate:.1f}%)
❌ Perdants      : {losses}
📈 Gain moyen    : {avg_pnl:.4f}%
💰 Gain total    : {total_pnl:.2f}%
🏆 Meilleur      : {best:.4f}%
📉 Pire          : {worst:.4f}%
📊 Max drawdown  : {max_drawdown:.2f}%
⏳ Durée moyenne : {avg_bars:.0f} bougies
━━━━━━━━━━━━━━━━━━━━━━━━
""")
        trades_df.to_csv(f"backtest_{symbol}_{TIMEFRAME}.csv", index=False)
        logger.info(f"Résultats sauvegardés : backtest_{symbol}_{TIMEFRAME}.csv")

if __name__ == "__main__":
    run_backtest()
