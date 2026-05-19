cimport time
from datetime import datetime
from typing import Dict, List, Optional

from config import (
    USERS_FILE,
    USAGE_FILE,
    SETTINGS_FILE,
    WATCHLISTS_FILE,
    FREE_DAILY_REQUESTS,
    ADMIN_ID,
    TRIAL_DAYS,
    ACCESS_MODE,
    ALLOW_AUTO_REGISTER,
    MAX_WATCHLIST_SYMBOLS_FREE,
    MAX_WATCHLIST_SYMBOLS_TESTER,
    MAX_WATCHLIST_SYMBOLS_PRO,
)

from utils import load_json, save_json
from i18n import get_text


class UserManager:

    _instance = None

    def __init__(self):

        self.users = {}
        self._load_users()

        self.usage = load_json(USAGE_FILE) or {}
        self.settings = load_json(SETTINGS_FILE) or {}
        self.watchlists = load_json(WATCHLISTS_FILE) or {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # =========================================================
    # LOAD USERS
    # =========================================================

    def _load_users(self):

        from database import get_db

        conn = get_db()

        try:
            rows = conn.execute("SELECT * FROM users").fetchall()

            self.users = {}

            if rows:
                for r in rows:
                    self.users[str(r["user_id"])] = {
                        "role": r["role"],
                        "lang": r["lang"],
                        "timeframe": r["timeframe"],
                        "risk": r["risk"],
                        "terms_accepted": bool(r["terms_accepted"]),
                        "trial_start": r["trial_start"],
                        "created_at": r["created_at"],
                        "approved": True,
                    }

            else:
                data = load_json(USERS_FILE) or {}

                self.users = data

                for uid, u in data.items():
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO users
                        (user_id, role, lang, timeframe, risk, terms_accepted, trial_start, created_at)
                        VALUES (?,?,?,?,?,?,?,?)
                        """,
                        (
                            int(uid),
                            u.get("role", "tester"),
                            u.get("lang", "en"),
                            u.get("timeframe", "1h"),
                            u.get("risk", "medium"),
                            int(u.get("terms_accepted", False)),
                            u.get("trial_start", time.time()),
                            u.get("created_at", time.time()),
                        ),
                    )

                conn.commit()

        finally:
            conn.close()

    # =========================================================
    # SAVE
    # =========================================================

    def _save(self):
        save_json(USERS_FILE, self.users)

    # =========================================================
    # SAFE GET USER
    # =========================================================

    def get_user(self, user_id: int) -> Optional[Dict]:

        uid = str(user_id)

        if uid in self.users and isinstance(self.users[uid], dict):
            return self.users[uid]

        if not ALLOW_AUTO_REGISTER:
            return None

        now = time.time()

        self.users[uid] = {
            "role": "tester",
            "joined": now,
            "trial_start": now,
            "created_at": now,
            "used_promo_codes": [],
            "lang": "en",
            "timeframe": "1h",
            "risk": "medium",
            "terms_accepted": False,
            "approved": False,
        }

        self.settings[uid] = {
            "timeframe": "1h",
            "risk": "medium",
            "lang": "en",
        }

        self.watchlists[uid] = []

        self._save()

        return self.users[uid]

    # =========================================================
    # ACCESS
    # =========================================================

    def user_exists(self, user_id: int) -> bool:
        return str(user_id) in self.users

    def is_admin(self, user_id: int) -> bool:
        return int(user_id) == ADMIN_ID

    def is_approved(self, user_id: int) -> bool:

        if self.is_admin(user_id):
            return True

        user = self.get_user(user_id)

        return bool(user and user.get("approved", False))

    def can_access_bot(self, user_id: int) -> bool:

        if ACCESS_MODE == "open":
            return True

        return self.is_approved(user_id)

    # =========================================================
    # ROLE
    # =========================================================

    def get_role(self, user_id: int) -> str:

        user = self.get_user(user_id)

        if not user:
            return "blocked"

        return user.get("role", "tester")

    def is_premium(self, user_id: int) -> bool:

        if self.is_admin(user_id):
            return True

        return self.get_role(user_id) in ["pro", "admin"]

    # =========================================================
    # TRIAL SAFE
    # =========================================================

    def is_trial_valid(self, user_id: int) -> bool:

        user = self.get_user(user_id)

        if not user:
            return False

        start = user.get("trial_start")

        try:
            start = float(start)
        except (TypeError, ValueError):
            start = time.time()
            user["trial_start"] = start
            self._save()

        return time.time() < start + (TRIAL_DAYS * 86400)

    def can_use_premium_feature(self, user_id: int) -> bool:
        return self.is_premium(user_id) or self.is_trial_valid(user_id)

    # =========================================================
    # TERMS
    # =========================================================

    def has_accepted_terms(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return bool(user and user.get("terms_accepted", False))

    def accept_terms(self, user_id: int):

        user = self.get_user(user_id)
        if not user:
            return

        user["terms_accepted"] = True
        self._save()

    # =========================================================
    # LIMITS SAFE
    # =========================================================

    def check_limit(self, user_id: int) -> bool:

        if self.is_admin(user_id) or self.is_premium(user_id):
            return True

        uid = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        if uid not in self.usage or not isinstance(self.usage.get(uid), dict):
            self.usage[uid] = {"date": today, "count": 0}

        if self.usage[uid].get("date") != today:
            self.usage[uid] = {"date": today, "count": 0}

        return self.usage[uid]["count"] < FREE_DAILY_REQUESTS

    def increment_usage(self, user_id: int):

        if self.is_admin(user_id) or self.is_premium(user_id):
            return

        uid = str(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        if uid not in self.usage or self.usage[uid].get("date") != today:
            self.usage[uid] = {"date": today, "count": 1}
        else:
            self.usage[uid]["count"] += 1

        save_json(USAGE_FILE, self.usage)

    # =========================================================
    # WATCHLIST SAFE (FIX FINAL)
    # =========================================================

    def get_watchlist(self, user_id: int) -> List[str]:

        uid = str(user_id)

        if uid not in self.watchlists or not isinstance(self.watchlists[uid], list):
            self.watchlists[uid] = []
            self._save()

        return self.watchlists[uid]

    def get_watchlist_limit(self, user_id: int) -> int:

        role = self.get_role(user_id)

        if role == "pro":
            return MAX_WATCHLIST_SYMBOLS_PRO

        if role == "tester":
            return MAX_WATCHLIST_SYMBOLS_TESTER

        return MAX_WATCHLIST_SYMBOLS_FREE

    def add_to_watchlist(self, user_id: int, symbol: str):

        uid = str(user_id)

        if uid not in self.watchlists:
            self.watchlists[uid] = []

        limit = self.get_watchlist_limit(user_id)

        if len(self.watchlists[uid]) >= limit:
            return False, limit

        if symbol not in self.watchlists[uid]:
            self.watchlists[uid].append(symbol)

        save_json(WATCHLISTS_FILE, self.watchlists)

        return True, limit

    def remove_from_watchlist(self, user_id: int, symbol: str):

        uid = str(user_id)

        if uid in self.watchlists and symbol in self.watchlists[uid]:
            self.watchlists[uid].remove(symbol)
            save_json(WATCHLISTS_FILE, self.watchlists)

    # =========================================================
    # SETTINGS SAFE
    # =========================================================

    def get_setting(self, user_id: int, key: str, default=None):

        uid = str(user_id)

        if uid not in self.settings or not isinstance(self.settings[uid], dict):
            self.settings[uid] = {}

        return self.settings[uid].get(key, default)

    def set_setting(self, user_id: int, key: str, value):

        uid = str(user_id)

        if uid not in self.settings:
            self.settings[uid] = {}

        self.settings[uid][key] = value

        save_json(SETTINGS_FILE, self.settings)

    # =========================================================
    # PROMO SAFE
    # =========================================================

    def redeem_promo(self, user_id: int, code: str):

        promos = {
            "TRADERBURUNDI": {"days": 5}
        }

        code = code.upper()
        lang = self.get_setting(user_id, "lang", "en")

        if code not in promos:
            return False, get_text(lang, "redeem_invalid")

        user = self.get_user(user_id)

        if not user:
            return False, "User not found"

        user["trial_start"] = user.get("trial_start", time.time()) - promos[code]["days"] * 86400

        self._save()

        return True, get_text(lang, "redeem_success")