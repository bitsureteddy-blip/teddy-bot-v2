"""
Gestionnaire d'historique des signaux pour Bitsure Teddy.
Stockage SQLite avec fallback JSON.
"""

import json
import os
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

from config import SIGNALS_HISTORY_FILE


class HistoryManager:
    _instance = None

    def __init__(self):
        self.signals = self._load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> List[Dict]:
        from database import get_db
        conn = get_db()
        rows = conn.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT 200").fetchall()
        if rows:
            signals = []
            for r in rows:
                signals.append({
                    "id": r["id"],
                    "symbol": r["symbol"],
                    "direction": r["direction"],
                    "entry_price": r["entry_price"],
                    "timeframe": "1h",
                    "type": "analyse",
                    "score": r["score"],
                    "timestamp": datetime.utcfromtimestamp(r["created_at"]).isoformat() if r["created_at"] else "",
                    "status": r["status"],
                    "sl": r["sl"],
                    "tp": r["tp"],
                    "result_price": None,
                    "result_pct": r["result_pct"]
                })
            conn.close()
            return signals
        conn.close()
        # Fallback JSON
        if os.path.exists(SIGNALS_HISTORY_FILE):
            try:
                with open(SIGNALS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        pass  # SQLite gère la persistance

    def add_signal(self, symbol: str, direction: str, price: float, timeframe: str,
                   signal_type: str = "analyse", score: int = 0,
                   sl: Optional[float] = None, tp: Optional[float] = None) -> str:
        signal_id = hashlib.md5(f"{symbol}{direction}{price}{timeframe}{time.time()}".encode()).hexdigest()[:8]
        now = time.time()
        signal = {
            "id": signal_id,
            "symbol": symbol.upper(),
            "direction": direction,
            "entry_price": price,
            "timeframe": timeframe,
            "type": signal_type,
            "score": score,
            "timestamp": datetime.utcfromtimestamp(now).isoformat(),
            "status": "pending",
            "sl": sl,
            "tp": tp,
            "result_price": None,
            "result_pct": None
        }
        self.signals.insert(0, signal)
        self.signals = self.signals[:200]

        from database import get_db
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO signals (id, symbol, direction, entry_price, sl, tp, score, status, result_pct, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (signal_id, symbol.upper(), direction, price, sl, tp, score, "pending", None, now)
        )
        conn.commit()
        conn.close()
        return signal_id

    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        self._load()
        return self.signals[:limit]

    def get_signal_by_id(self, signal_id: str) -> Optional[Dict]:
        for signal in self.signals:
            if signal["id"] == signal_id:
                return signal
        return None

    def update_signal_result(self, signal_id: str, current_price: float) -> Optional[str]:
        for signal in self.signals:
            if signal["id"] == signal_id and signal["status"] == "pending":
                entry = signal["entry_price"]
                if signal["direction"] == "BUY":
                    result_pct = ((current_price - entry) / entry) * 100
                    signal["status"] = "win" if current_price > entry else "loss"
                else:
                    result_pct = ((entry - current_price) / entry) * 100
                    signal["status"] = "win" if current_price < entry else "loss"
                signal["result_price"] = current_price
                signal["result_pct"] = round(result_pct, 2)
                return signal["status"]
        return None

    def update_signal_status(self, signal_id, status, result_pct):
        for s in self.signals:
            if s["id"] == signal_id:
                s["status"] = status
                s["result_pct"] = result_pct
        from database import get_db
        conn = get_db()
        conn.execute(
            "UPDATE signals SET status=?, result_pct=?, closed_at=? WHERE id=?",
            (status, result_pct, time.time(), signal_id)
        )
        conn.commit()
        conn.close()

    def clear_old_signals(self, days: int = 30):
        cutoff = datetime.utcnow() - timedelta(days=days)
        self.signals = [s for s in self.signals if datetime.fromisoformat(s["timestamp"]) > cutoff]