import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from config import (
    USERS_FILE, USAGE_FILE, SETTINGS_FILE, WATCHLISTS_FILE,
    FREE_DAILY_REQUESTS, ADMIN_ID
)
from utils import load_json, save_json

class UserManager:
    _instance = None

    def __init__(self):
        self.users = load_json(USERS_FILE)          # id -> {"username":..., "premium": bool, "joined": timestamp}
        self.usage = load_json(USAGE_FILE)          # id -> {"date": "YYYY-MM-DD", "count": int}
        self.settings = load_json(SETTINGS_FILE)    # id -> {"timeframe": "1d", "risk": "medium", "lang": "en"}
        self.watchlists = load_json(WATCHLISTS_FILE)# id -> ["SYM1", "SYM2"]

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_user(self, user_id: int) -> Dict:
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                "username": "",
                "premium": False,
                "joined": time.time()
            }
            self.settings[user_id] = {"timeframe": "1d", "risk": "medium", "lang": "en"}
            self.watchlists[user_id] = []
            self._save()
        return self.users[user_id]

    def is_admin(self, user_id: int) -> bool:
        return user_id == ADMIN_ID

    def is_premium(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user.get("premium", False) or self.is_admin(user_id)

    def check_limit(self, user_id: int) -> bool:
        """Retourne True si l'utilisateur peut faire une requête"""
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
            return -1  # illimité
        user_id = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        if user_id not in self.usage or self.usage[user_id].get("date") != today:
            return FREE_DAILY_REQUESTS
        used = self.usage[user_id]["count"]
        return max(0, FREE_DAILY_REQUESTS - used)

    def get_setting(self, user_id: int, key: str, default=None):
        user_id = str(user_id)
        if user_id not in self.settings:
            self.settings[user_id] = {"timeframe": "1d", "risk": "medium", "lang": "en"}
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

    def _save(self):
        save_json(USERS_FILE, self.users)