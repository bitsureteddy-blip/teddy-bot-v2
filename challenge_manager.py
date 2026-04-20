"""
Gestionnaire du défi scalping pour Bitsure Teddy.
Gère les sessions de challenge par utilisateur.
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

from config import CHALLENGE_SESSIONS_FILE

class ChallengeManager:
    _instance = None

    def __init__(self):
        self.sessions = self._load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> Dict:
        if os.path.exists(CHALLENGE_SESSIONS_FILE):
            try:
                with open(CHALLENGE_SESSIONS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save(self):
        with open(CHALLENGE_SESSIONS_FILE, 'w') as f:
            json.dump(self.sessions, f, indent=2)

    def start_session(self, user_id: int, symbol: str = "EURUSD") -> Dict:
        """Démarre une nouvelle session de challenge pour un utilisateur."""
        session = {
            "user_id": user_id,
            "symbol": symbol.upper(),
            "current_trade": 1,
            "total_trades": 5,
            "score": {"win": 0, "loss": 0},
            "trades": [],
            "started_at": datetime.utcnow().isoformat(),
            "active": True
        }
        self.sessions[str(user_id)] = session
        self._save()
        return session

    def get_session(self, user_id: int) -> Optional[Dict]:
        return self.sessions.get(str(user_id))

    def update_session(self, user_id: int, session: Dict):
        self.sessions[str(user_id)] = session
        self._save()

    def end_session(self, user_id: int):
        if str(user_id) in self.sessions:
            self.sessions[str(user_id)]["active"] = False
            self._save()

    def add_trade_result(self, user_id: int, trade_data: Dict):
        session = self.get_session(user_id)
        if session:
            session["trades"].append(trade_data)
            if trade_data.get("result") == "win":
                session["score"]["win"] += 1
            elif trade_data.get("result") == "loss":
                session["score"]["loss"] += 1
            session["current_trade"] = len(session["trades"]) + 1
            if session["current_trade"] > session["total_trades"]:
                session["active"] = False
            self._save()

    def reset_session(self, user_id: int):
        if str(user_id) in self.sessions:
            del self.sessions[str(user_id)]
            self._save()