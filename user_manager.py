import time
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

        self.usage = load_json(USAGE_FILE)
        self.settings = load_json(SETTINGS_FILE)
        self.watchlists = load_json(WATCHLISTS_FILE)

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
            self.users = load_json(USERS_FILE)

            for uid, data in self.users.items():
                conn.execute(
                    """
                    INSERT OR IGNORE INTO users
                    (
                        user_id,
                        role,
                        lang,
                        timeframe,
                        risk,
                        terms_accepted,
                        trial_start,
                        created_at
                    )
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        int(uid),
                        data.get("role", "tester"),
                        data.get("lang", "en"),
                        data.get("timeframe", "1h"),
                        data.get("risk", "medium"),
                        int(data.get("terms_accepted", False)),
                        data.get("trial_start"),
                        data.get("created_at"),
                    ),
                )

            conn.commit()

        conn.close()

    # =========================================================
    # SAVE
    # =========================================================

    def _save(self):
        save_json(USERS_FILE, self.users)

    # =========================================================
    # USER ACCESS
    # =========================================================

    def user_exists(self, user_id: int) -> bool:
        return str(user_id) in self.users

    def is_admin(self, user_id: int) -> bool:
        return int(user_id) == ADMIN_ID

    def is_approved(self, user_id: int) -> bool:
        if self.is_admin(user_id):
            return True

        user = self.users.get(str(user_id))

        if not user:
            return False

        return user.get("approved", False)

    def can_access_bot(self, user_id: int) -> bool:
        if ACCESS_MODE == "open":
            return True

        return self.is_approved(user_id)

    # =========================================================
    # GET USER
    # =========================================================

    def get_user(self, user_id: int) -> Optional[Dict]:

        user_id = str(user_id)

        if user_id not in self.users:

            if not ALLOW_AUTO_REGISTER:
                return None

            now = time.time()

            self.users[user_id] = {
                "username": "",
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

            self.settings[user_id] = {
                "timeframe": "1h",
                "risk": "medium",
                "lang": "en",
            }

            self.watchlists[user_id] = []

            self._save()

            from database import get_db

            conn = get_db()

            conn.execute(
                """
                INSERT OR IGNORE INTO users
                (
                    user_id,
                    role,
                    lang,
                    timeframe,
                    risk,
                    terms_accepted,
                    trial_start,
                    created_at
                )
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    int(user_id),
                    "tester",
                    "en",
                    "1h",
                    "medium",
                    0,
                    now,
                    now,
                ),
            )

            conn.commit()
            conn.close()

        return self.users.get(user_id)

    # =========================================================
    # ROLE MANAGEMENT
    # =========================================================

    def get_role(self, user_id: int) -> str:
        user = self.get_user(user_id)

        if not user:
            return "blocked"

        return user.get("role", "tester")

    def set_role(self, user_id: int, role: str):

        user_id = str(user_id)

        if user_id not in self.users:
            return

        self.users[user_id]["role"] = role

        if "premium_expiry" in self.users[user_id]:
            del self.users[user_id]["premium_expiry"]

        self._save()

        from database import get_db

        conn = get_db()

        conn.execute(
            "UPDATE users SET role=? WHERE user_id=?",
            (role, int(user_id)),
        )

        conn.commit()
        conn.close()

    def approve_user(self, user_id: int):

        user_id = str(user_id)

        if user_id not in self.users:
            return False

        self.users[user_id]["approved"] = True

        self._save()

        return True

    # =========================================================
    # PREMIUM
    # =========================================================

    def set_role_temp(self, user_id: int, role: str, days: int):

        user_id = str(user_id)

        if user_id not in self.users:
            return

        expiry = time.time() + (days * 24 * 3600)

        self.users[user_id]["role"] = role
        self.users[user_id]["premium_expiry"] = expiry

        self._save()

    def check_premium_expiry(self, user_id: int) -> bool:

        user_id = str(user_id)

        user = self.users.get(user_id)

        if not user:
            return False

        if "premium_expiry" in user:

            if time.time() > user["premium_expiry"]:

                user["role"] = "tester"

                del user["premium_expiry"]

                self._save()

                return True

        return False

    def is_premium(self, user_id: int) -> bool:

        self.check_premium_expiry(user_id)

        if self.is_admin(user_id):
            return True

        role = self.get_role(user_id)

        return role in ["pro", "admin"]

    # =========================================================
    # TRIAL
    # =========================================================

    def is_trial_valid(self, user_id: int) -> bool:

        user = self.get_user(user_id)

        if not user:
            return False

        trial_start = user.get("trial_start", time.time())

        trial_end = trial_start + (TRIAL_DAYS * 24 * 3600)

        return time.time() < trial_end

    def can_use_premium_feature(self, user_id: int) -> bool:

        if self.is_premium(user_id):
            return True

        return self.is_trial_valid(user_id)

    # =========================================================
    # TERMS
    # =========================================================

    def has_accepted_terms(self, user_id: int) -> bool:

        user = self.get_user(user_id)

        if not user:
            return False

        return user.get("terms_accepted", False)

    def accept_terms(self, user_id: int):

        user = self.get_user(user_id)

        if not user:
            return

        user["terms_accepted"] = True

        self._save()

        from database import get_db

        conn = get_db()

        conn.execute(
            """
            UPDATE users
            SET terms_accepted=1
            WHERE user_id=?
            """,
            (int(user_id),),
        )

        conn.commit()
        conn.close()

    # =========================================================
    # REQUEST LIMITS
    # =========================================================

    def check_limit(self, user_id: int) -> bool:

        if self.is_premium(user_id) or self.is_admin(user_id):
            return True

        user_id = str(user_id)

        today = datetime.now().strftime("%Y-%m-%d")

        if (
            user_id not in self.usage
            or self.usage[user_id].get("date") != today
        ):
            self.usage[user_id] = {
                "date": today,
                "count": 0,
            }

        return self.usage[user_id]["count"] < FREE_DAILY_REQUESTS

    def increment_usage(self, user_id: int):

        if self.is_premium(user_id) or self.is_admin(user_id):
            return

        user_id = str(user_id)

        today = datetime.now().strftime("%Y-%m-%d")

        if (
            user_id not in self.usage
            or self.usage[user_id].get("date") != today
        ):
            self.usage[user_id] = {
                "date": today,
                "count": 1,
            }
        else:
            self.usage[user_id]["count"] += 1

        save_json(USAGE_FILE, self.usage)

    # =========================================================
    # SETTINGS
    # =========================================================

    def get_setting(self, user_id: int, key: str, default=None):

        user_id = str(user_id)

        if user_id not in self.settings:
            self.settings[user_id] = {}

        return self.settings[user_id].get(key, default)

    def set_setting(self, user_id: int, key: str, value):

        user_id = str(user_id)

        if user_id not in self.settings:
            self.settings[user_id] = {}

        self.settings[user_id][key] = value

        save_json(SETTINGS_FILE, self.settings)

    # =========================================================
    # WATCHLIST
    # =========================================================

    def get_watchlist_limit(self, user_id: int) -> int:

        role = self.get_role(user_id)

        if role == "pro":
            return MAX_WATCHLIST_SYMBOLS_PRO

        if role == "tester":
            return MAX_WATCHLIST_SYMBOLS_TESTER

        return MAX_WATCHLIST_SYMBOLS_FREE

    def get_watchlist(self, user_id: int) -> list:

        user_id = str(user_id)

        return self.watchlists.get(user_id, [])

    def add_to_watchlist(self, user_id: int, symbol: str):

        user_id = str(user_id)

        if user_id not in self.watchlists:
            self.watchlists[user_id] = []

        current = self.watchlists[user_id]

        limit = self.get_watchlist_limit(int(user_id))

        if len(current) >= limit:
            return False, limit

        if symbol not in current:
            current.append(symbol)

            save_json(WATCHLISTS_FILE, self.watchlists)

        return True, limit

    def remove_from_watchlist(self, user_id: int, symbol: str):

        user_id = str(user_id)

        if (
            user_id in self.watchlists
            and symbol in self.watchlists[user_id]
        ):
            self.watchlists[user_id].remove(symbol)

            save_json(WATCHLISTS_FILE, self.watchlists)

    # =========================================================
    # USERS
    # =========================================================

    def get_all_users(self) -> list:
        return list(self.users.keys())

    # =========================================================
    # FAVORITES
    # =========================================================

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

    # =========================================================
    # PROMOS
    # =========================================================

    def redeem_promo(self, user_id: int, code: str) -> tuple:

        promos = {
            "TRADERBURUNDI": {
                "type": "trial_extension",
                "days": 5,
                "max_uses": 1,
            },
        }

        code = code.upper()

        lang = self.get_setting(user_id, "lang", "en")

        if code not in promos:
            return False, get_text(lang, "redeem_invalid")

        user = self.get_user(user_id)

        if not user:
            return False, "Utilisateur introuvable."

        used_codes = user.get("used_promo_codes", [])

        if code in used_codes:
            return False, get_text(lang, "redeem_already_used")

        promo = promos[code]

        if promo["type"] == "trial_extension":

            user["trial_start"] -= (
                promo["days"] * 24 * 3600
            )

            used_codes.append(code)

            user["used_promo_codes"] = used_codes

            self._save()

            return (
                True,
                get_text(
                    lang,
                    "redeem_success",
                    message=f"{promo['days']} jours",
                ),
            )

        return False, get_text(lang, "redeem_invalid")