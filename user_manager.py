import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from config import (
    USERS_FILE, USAGE_FILE, SETTINGS_FILE, WATCHLISTS_FILE,
    FREE_DAILY_REQUESTS, ADMIN_ID, TRIAL_DAYS
)
from utils import load_json, save_json

class UserManager:
    _instance = None

    def __init__(self):
        self.users = load_json(USERS_FILE)
        self.usage = load_json(USAGE_FILE)
        self.settings = load_json(SETTINGS_FILE)
        self.watchlists = load_json(WATCHLISTS_FILE)
        self.lifetime_count = self._count_lifetime_from_users()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_users(self):
        """Recharge les utilisateurs depuis le fichier JSON."""
        self.users = load_json(USERS_FILE)

    def _count_lifetime_from_users(self) -> int:
        count = 0
        for u in self.users.values():
            if u.get("role") == "elite" and u.get("lifetime", False):
                count += 1
        return count

    def get_user(self, user_id: int) -> Dict:
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                "username": "",
                "role": "free",
                "joined": time.time()
            }
            self.settings[user_id] = {"timeframe": "1d", "risk": "medium", "lang": "fr"}
            self.watchlists[user_id] = []
            self._save()
        return self.users[user_id]

    def is_admin(self, user_id: int) -> bool:
        return user_id == ADMIN_ID

    def get_role(self, user_id: int) -> str:
        user = self.get_user(user_id)
        return user.get("role", "free")

    def set_role(self, user_id: int, role: str):
        user_id = str(user_id)
        if user_id not in self.users:
            self.get_user(user_id)
        self.users[user_id]["role"] = role
        save_json(USERS_FILE, self.users)

    def is_premium(self, user_id: int) -> bool:
        if self.is_admin(user_id):
            return True
        role = self.get_role(user_id)
        return role in ("pro", "elite")

    def is_trial_valid(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        joined = user.get("joined", time.time())
        trial_end = joined + (TRIAL_DAYS * 24 * 3600)
        return time.time() < trial_end

    def can_use_premium_feature(self, user_id: int) -> bool:
        return self.is_premium(user_id)

    def check_limit(self, user_id: int) -> bool:
        if self.is_premium(user_id) or self.is_admin(user_id):
            return True
        user_id = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user_id not in self.usage or self.usage[user_id].get("date") != today:
            self.usage[user_id] = {"date": today, "count": 0}
        return self.usage[user_id]["count"] < FREE_DAILY_REQUESTS

    def increment_usage(self, user_id: int):
        if self.is_premium(user_id) or self.is_admin(user_id):
            return
        user_id = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user_id not in self.usage or self.usage[user_id].get("date") != today:
            self.usage[user_id] = {"date": today, "count": 1}
        else:
            self.usage[user_id]["count"] += 1
        save_json(USAGE_FILE, self.usage)

    def get_remaining_requests(self, user_id: int) -> int:
        if self.is_premium(user_id) or self.is_admin(user_id):
            return -1
        user_id = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user_id not in self.usage or self.usage[user_id].get("date") != today:
            return FREE_DAILY_REQUESTS
        used = self.usage[user_id]["count"]
        return max(0, FREE_DAILY_REQUESTS - used)

    def get_setting(self, user_id: int, key: str, default=None):
        user_id = str(user_id)
        if user_id not in self.settings:
            self.settings[user_id] = {"timeframe": "1d", "risk": "medium", "lang": "fr"}
        return self.settings[user_id].get(key, default)

    def set_setting(self, user_id: int, key: str, value):
        user_id = str(user_id)
        if user_id not in self.settings:
            self.settings[user_id] = {}
        self.settings[user_id][key] = value
        save_json(SETTINGS_FILE, self.settings)

    def get_watchlist(self, user_id: int) -> list:
        user_id = str(user_id)
        return self.watchlists.get(user_id, [])

    def add_to_watchlist(self, user_id: int, symbol: str):
        user_id = str(user_id)
        if user_id not in self.watchlists:
            self.watchlists[user_id] = []
        if symbol not in self.watchlists[user_id]:
            self.watchlists[user_id].append(symbol)
            save_json(WATCHLISTS_FILE, self.watchlists)

    def remove_from_watchlist(self, user_id: int, symbol: str):
        user_id = str(user_id)
        if user_id in self.watchlists and symbol in self.watchlists[user_id]:
            self.watchlists[user_id].remove(symbol)
            save_json(WATCHLISTS_FILE, self.watchlists)

    def get_all_users(self) -> list:
        return list(self.users.keys())

    def increment_lifetime_count(self):
        self.lifetime_count += 1

    def get_lifetime_count(self) -> int:
        return self.lifetime_count

    def _save(self):
        save_json(USERS_FILE, self.users)