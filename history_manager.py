"""
Gestionnaire d'historique des signaux pour Bitsure Teddy.
Enregistre les signaux générés et permet de consulter les résultats passés.
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
        if os.path.exists(SIGNALS_HISTORY_FILE):
            try:
                with open(SIGNALS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading history: {e}")
        return []

    def _save(self):
        try:
            with open(SIGNALS_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.signals, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def add_signal(self, symbol: str, direction: str, price: float, timeframe: str,
                   signal_type: str = "analyse", score: int = 0) -> str:
        """Ajoute un signal à l'historique et retourne son ID unique."""
        signal_id = hashlib.md5(f"{symbol}{direction}{price}{timeframe}{time.time()}".encode()).hexdigest()[:8]
        signal = {
            "id": signal_id,
            "symbol": symbol.upper(),
            "direction": direction,
            "entry_price": price,
            "timeframe": timeframe,
            "type": signal_type,
            "score": score,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
            "result_price": None,
            "result_pct": None
        }
        self.signals.append(signal)
        # Garder les 200 derniers signaux
        self.signals = self.signals[-200:]
        self._save()
        return signal_id

    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Retourne les derniers signaux (du plus récent au plus ancien)."""
        return list(reversed(self.signals[-limit:]))

    def get_signal_by_id(self, signal_id: str) -> Optional[Dict]:
        """Retrouve un signal par son ID."""
        for signal in self.signals:
            if signal["id"] == signal_id:
                return signal
        return None

    def update_signal_result(self, signal_id: str, current_price: float) -> Optional[str]:
        """Met à jour le résultat d'un signal en comparant avec le prix actuel. Retourne le nouveau statut."""
        for signal in self.signals:
            if signal["id"] == signal_id and signal["status"] == "pending":
                entry = signal["entry_price"]
                if signal["direction"] == "BUY":
                    result_pct = ((current_price - entry) / entry) * 100
                    signal["status"] = "win" if current_price > entry else "loss"
                else:  # SELL
                    result_pct = ((entry - current_price) / entry) * 100
                    signal["status"] = "win" if current_price < entry else "loss"
                signal["result_price"] = current_price
                signal["result_pct"] = round(result_pct, 2)
                self._save()
                return signal["status"]
        return None

    def check_and_update_pending(self, fetcher):
        """Parcourt les signaux en attente et met à jour ceux qui sont assez vieux."""
        now = datetime.utcnow()
        for signal in self.signals:
            if signal["status"] != "pending":
                continue
            signal_time = datetime.fromisoformat(signal["timestamp"])
            tf_minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
            required_minutes = tf_minutes.get(signal["timeframe"], 60)
            if now - signal_time >= timedelta(minutes=required_minutes):
                try:
                    df = fetcher.get_historical_data(signal["symbol"], "1d", limit=1)
                    if df is not None and not df.empty:
                        current_price = df['Close'].iloc[-1]
                        self.update_signal_result(signal["id"], current_price)
                except Exception as e:
                    logger.error(f"Failed to update signal {signal['id']}: {e}")

    def clear_old_signals(self, days: int = 30):
        """Supprime les signaux plus vieux que 'days' jours."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        self.signals = [s for s in self.signals if datetime.fromisoformat(s["timestamp"]) > cutoff]
        self._save()