import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from config import (
    USERS_FILE, USAGE_FILE, SETTINGS_FILE, WATCHLISTS_FILE,
    FREE_DAILY_REQUESTS, ADMIN_ID, TRIAL_DAYS
)
from utils import load_json, save_json
from i18n import get_text

class UserManager:
    _instance = None

    def __init__(self):
        self.users = load_json(USERS_FILE)
        self.usage = load_json(USAGE_FILE)
        self.settings = load_json(SETTINGS_FILE)
        self.watchlists = load_json(WATCHLISTS_FILE)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_users(self):
        self.users = load_json(USERS_FILE)

    def get_user(self, user_id: int) -> Dict:
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                "username": "",
                "role": "free",
                "joined": time.time(),
                "used_promo_codes": []   # suivi des codes promo utilisés
            }
            self.settings[user_id] = {"timeframe": "1d", "risk": "medium", "lang": "en"}
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
        if "premium_expiry" in self.users[user_id]:
            del self.users[user_id]["premium_expiry"]
        save_json(USERS_FILE, self.users)

    def set_role_temp(self, user_id: int, role: str, days: int):
        user_id = str(user_id)
        if user_id not in self.users:
            self.get_user(user_id)
        self.users[user_id]["role"] = role
        expiry = time.time() + (days * 24 * 3600)
        self.users[user_id]["premium_expiry"] = expiry
        save_json(USERS_FILE, self.users)

    def check_premium_expiry(self, user_id: int) -> bool:
        user_id = str(user_id)
        user = self.users.get(user_id)
        if user and "premium_expiry" in user:
            if time.time() > user["premium_expiry"]:
                user["role"] = "free"
                del user["premium_expiry"]
                save_json(USERS_FILE, self.users)
                return True
        return False

    def is_premium(self, user_id: int) -> bool:
        self.check_premium_expiry(user_id)
        if self.is_admin(user_id):
            return True
        role = self.get_role(user_id)
        return role == "pro"

    def is_trial_valid(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        joined = user.get("joined", time.time())
        trial_end = joined + (TRIAL_DAYS * 24 * 3600)
        return time.time() < trial_end

    def can_use_premium_feature(self, user_id: int) -> bool:
        # Combine trial et premium
        if self.is_premium(user_id):
            return True
        return self.is_trial_valid(user_id)

    def has_accepted_terms(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user.get("terms_accepted", False)

    def accept_terms(self, user_id: int):
        user = self.get_user(user_id)
        user["terms_accepted"] = True
        self._save()

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

    def get_favorites(self, user_id: int) -> List[str]:
        user_id = str(user_id)
        return self.settings.get(user_id, {}).get("favorites", [])

    def add_favorite(self, user_id: int, symbol: str):
        user_id = str(user_id)
        if user_id not in self.settings:
            self.settings[user_id] = {}
        favs = self.settings[user_id].get("favorites", [])
        if symbol not in favs:
            favs.append(symbol)
            self.settings[user_id]["favorites"] = favs
            save_json(SETTINGS_FILE, self.settings)

    def remove_favorite(self, user_id: int, symbol: str):
        user_id = str(user_id)
        if user_id in self.settings:
            favs = self.settings[user_id].get("favorites", [])
            if symbol in favs:
                favs.remove(symbol)
                self.settings[user_id]["favorites"] = favs
                save_json(SETTINGS_FILE, self.settings)

    def redeem_promo(self, user_id: int, code: str) -> tuple:
        promos = {
            "TRADERBURUNDI": {"type": "trial_extension", "days": 5, "max_uses": 1},
        }
        code = code.upper()
        lang = self.get_setting(user_id, "lang", "en")
        if code not in promos:
            return False, get_text(lang, "redeem_invalid")
        
        user_id = str(user_id)
        user = self.get_user(user_id)
        used_codes = user.get("used_promo_codes", [])
        if code in used_codes:
            return False, get_text(lang, "redeem_already_used")
        
        promo = promos[code]
        if promo["type"] == "trial_extension":
            user["joined"] = user.get("joined", time.time()) - (promo["days"] * 24 * 3600)
            used_codes.append(code)
            user["used_promo_codes"] = used_codes
            self._save()
            return True, get_text(lang, "redeem_success", message=f"{promo['days']} jours")
        return False, get_text(lang, "redeem_invalid")


    def add_pending_binance(self, user_id: int, ident: str):
        user = self.get_user(user_id)
        user["pending_binance_payment"] = {"id": ident, "created_at": time.time()}
        user["pending_binance_id"] = ident
        self._save()

    def confirm_binance_payment(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user.get("pending_binance_payment"):
            return False
        user["role"] = "pro"
        user.pop("pending_binance_payment", None)
        user.pop("pending_binance_id", None)
        self._save()
        return True

    def find_user_by_memo(self, memo: str):
        for uid, data in self.users.items():
            if data.get("pending_binance_id") == memo:
                return uid
        return None

    def _save(self):
        save_json(USERS_FILE, self.users)
