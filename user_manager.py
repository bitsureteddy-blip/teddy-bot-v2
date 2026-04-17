import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

USER_FILE = "users.json"
FREE_DAILY_REQUESTS = 5
TRIAL_DAYS = 3

class UserManager:
    _instance = None

    def __init__(self):
        self.users = self._load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self) -> Dict:
        if os.path.exists(USER_FILE):
            try:
                with open(USER_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading users: {e}")
        return {}

    def _save(self):
        try:
            with open(USER_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def register_user(self, user_id: int) -> Dict:
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            now = datetime.utcnow().isoformat()
            self.users[user_id_str] = {
                "id": user_id,
                "registered_at": now,
                "role": "FREE",
                "trial_start": now,
                "trial_active": True,
                "daily_requests": 0,
                "last_request_date": datetime.utcnow().date().isoformat(),
                "language": "en",
                "timeframe": "1d",
                "risk_profile": "medium",
                "watchlist": [],
                "premium_expiry": None
            }
            self._save()
        return self.users[user_id_str]

    def get_user(self, user_id: int) -> Optional[Dict]:
        return self.users.get(str(user_id))

    def update_user(self, user_id: int, updates: Dict):
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str].update(updates)
            self._save()

    def get_user_lang(self, user_id: int) -> str:
        user = self.get_user(user_id)
        return user.get("language", "en") if user else "en"

    def set_user_lang(self, user_id: int, lang: str):
        self.update_user(user_id, {"language": lang})

    def is_premium(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        if user.get("role") in ("PRO", "ELITE"):
            return True
        # Vérifier l'essai gratuit
        if user.get("trial_active", False):
            trial_start = datetime.fromisoformat(user["trial_start"])
            if datetime.utcnow() - trial_start < timedelta(days=TRIAL_DAYS):
                return True
            else:
                user["trial_active"] = False
                self._save()
        return False

    def check_limit(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        if self.is_premium(user_id):
            return True
        today = datetime.utcnow().date().isoformat()
        last_date = user.get("last_request_date")
        if last_date != today:
            user["daily_requests"] = 0
            user["last_request_date"] = today
            self._save()
        if user["daily_requests"] < FREE_DAILY_REQUESTS:
            user["daily_requests"] += 1
            self._save()
            return True
        return False

    def get_remaining_requests(self, user_id: int) -> int:
        user = self.get_user(user_id)
        if not user:
            return 0
        if self.is_premium(user_id):
            return -1  # illimité
        today = datetime.utcnow().date().isoformat()
        last_date = user.get("last_request_date")
        if last_date != today:
            return FREE_DAILY_REQUESTS
        return max(0, FREE_DAILY_REQUESTS - user.get("daily_requests", 0))

    def set_role(self, user_id: int, role: str, expiry_days: int = 0):
        user = self.get_user(user_id)
        if not user:
            return
        user["role"] = role.upper()
        if expiry_days > 0:
            expiry = datetime.utcnow() + timedelta(days=expiry_days)
            user["premium_expiry"] = expiry.isoformat()
        else:
            user["premium_expiry"] = None
        if role.upper() != "FREE":
            user["trial_active"] = False
        self._save()

    def revoke_premium(self, user_id: int):
        self.set_role(user_id, "FREE", 0)

    def add_to_watchlist(self, user_id: int, symbol: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        if "watchlist" not in user:
            user["watchlist"] = []
        limit = 3 if not self.is_premium(user_id) else 999
        if len(user["watchlist"]) >= limit:
            return False
        symbol = symbol.upper()
        if symbol not in user["watchlist"]:
            user["watchlist"].append(symbol)
            self._save()
        return True

    def remove_from_watchlist(self, user_id: int, symbol: str):
        user = self.get_user(user_id)
        if user and "watchlist" in user:
            symbol = symbol.upper()
            if symbol in user["watchlist"]:
                user["watchlist"].remove(symbol)
                self._save()

    def get_watchlist(self, user_id: int) -> List[str]:
        user = self.get_user(user_id)
        return user.get("watchlist", []) if user else []

    def update_challenge_score(self, user_id: int, wins: int, total: int):
        user = self.get_user(user_id)
        if not user:
            return
        if "challenge_scores" not in user:
            user["challenge_scores"] = []
        user["challenge_scores"].append({
            "wins": wins,
            "total": total,
            "date": datetime.utcnow().isoformat()
        })
        # Garder les 10 derniers scores
        user["challenge_scores"] = user["challenge_scores"][-10:]
        self._save()

    def get_top_challenge_scores(self, limit: int = 5):
        scores = []
        for uid, data in self.users.items():
            if "challenge_scores" in data and data["challenge_scores"]:
                # Prendre le meilleur score (meilleur taux de réussite)
                best = max(data["challenge_scores"], key=lambda x: x["wins"]/x["total"] if x["total"]>0 else 0)
                scores.append((uid, best))
        scores.sort(key=lambda x: x[1]["wins"]/x[1]["total"] if x[1]["total"]>0 else 0, reverse=True)
        return scores[:limit]

    def get_all_users(self) -> Dict:
        return self.users

    def get_stats(self) -> Dict:
        total = len(self.users)
        free = sum(1 for u in self.users.values() if u.get("role") == "FREE")
        pro = sum(1 for u in self.users.values() if u.get("role") == "PRO")
        elite = sum(1 for u in self.users.values() if u.get("role") == "ELITE")
        return {"total": total, "free": free, "pro": pro, "elite": elite}