import time
from datetime import datetime
from typing import Dict, Optional

from config import ADMIN_ID, FREE_DAILY_REQUESTS, TRIAL_DAYS, ACCESS_MODE
from database import get_db


class UserManager:

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # =========================================================
    # GET USER
    # =========================================================

    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM users WHERE user_id=?",
            (user_id,),
        ).fetchone()
        conn.close()

        if row:
            return dict(row)

        # AUTO CREATE USER
        now = time.time()

        conn = get_db()
        conn.execute(
            """
            INSERT INTO users (
                user_id,
                role,
                lang,
                timeframe,
                risk,
                terms_accepted,
                trial_start,
                created_at
            )
            VALUES (?, 'tester', 'en', '1h', 'medium', 0, ?, ?)
            """,
            (user_id, now, now),
        )
        conn.commit()
        conn.close()

        return self.get_user(user_id)

    # =========================================================
    # ADMIN
    # =========================================================

    def is_admin(self, user_id: int) -> bool:
        return int(user_id) == ADMIN_ID

    # =========================================================
    # ROLE
    # =========================================================

    def get_role(self, user_id: int) -> str:
        user = self.get_user(user_id)
        return user["role"] if user else "blocked"

    def is_premium(self, user_id: int) -> bool:
        if self.is_admin(user_id):
            return True
        return self.get_role(user_id) in ("pro", "admin")

    # =========================================================
    # ACCESS
    # =========================================================

    def is_approved(self, user_id: int) -> bool:
        if self.is_admin(user_id):
            return True

        user = self.get_user(user_id)
        return bool(user and user["terms_accepted"])

    def can_access_bot(self, user_id: int) -> bool:
        if ACCESS_MODE == "open":
            return True
        return self.is_approved(user_id)

    # =========================================================
    # TERMS
    # =========================================================

    def accept_terms(self, user_id: int):
        conn = get_db()
        conn.execute(
            "UPDATE users SET terms_accepted=1 WHERE user_id=?",
            (user_id,),
        )
        conn.commit()
        conn.close()

    # =========================================================
    # TRIAL
    # =========================================================

    def is_trial_valid(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False

        start = float(user["trial_start"])
        return time.time() < start + (TRIAL_DAYS * 86400)

    def can_use_premium_feature(self, user_id: int) -> bool:
        return self.is_premium(user_id) or self.is_trial_valid(user_id)

    # =========================================================
    # LIMIT USAGE (SIMPLE SQLITE FIELD)
    # =========================================================

    def check_limit(self, user_id: int) -> bool:
        if self.is_admin(user_id) or self.is_premium(user_id):
            return True

        user = self.get_user(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        if not user["created_at"]:
            return True

        return True  # (à améliorer si tu veux quota SQL propre)

    def increment_usage(self, user_id: int):
        pass  # à migrer si tu veux quota propre SQL

    # =========================================================
    # SETTINGS (SQL VERSION)
    # =========================================================

    def get_setting(self, user_id: int, key: str, default=None):
        user = self.get_user(user_id)
        return user.get(key, default)

    def set_setting(self, user_id: int, key: str, value):
        conn = get_db()
        conn.execute(
            f"UPDATE users SET {key}=? WHERE user_id=?",
            (value, user_id),
        )
        conn.commit()
        conn.close()

    # =========================================================
    # WATCHLIST (SQL TABLE)
    # =========================================================

    def get_watchlist(self, user_id: int):
        conn = get_db()
        rows = conn.execute(
            "SELECT symbol FROM watchlists WHERE user_id=?",
            (user_id,),
        ).fetchall()
        conn.close()

        return [r["symbol"] for r in rows]

    def add_to_watchlist(self, user_id: int, symbol: str):
        symbol = symbol.upper()

        conn = get_db()
        conn.execute(
            "INSERT OR IGNORE INTO watchlists (user_id, symbol) VALUES (?, ?)",
            (user_id, symbol),
        )
        conn.commit()
        conn.close()

    def remove_from_watchlist(self, user_id: int, symbol: str):
        conn = get_db()
        conn.execute(
            "DELETE FROM watchlists WHERE user_id=? AND symbol=?",
            (user_id, symbol.upper()),
        )
        conn.commit()
        conn.close()
