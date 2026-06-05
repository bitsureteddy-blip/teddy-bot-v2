from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, date
from threading import Lock
from typing import Optional, Mapping, Any


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _to_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


@dataclass
class TwelveDataQuotaTracker:
    daily_limit: int = 800
    used_today: Optional[int] = None
    left_today: Optional[int] = None
    last_update_utc: Optional[datetime] = None
    current_day: date = field(default_factory=utc_today)
    alert_sent_today: bool = False
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def _reset_if_new_day(self) -> None:
        today = utc_today()
        if self.current_day != today:
            self.current_day = today
            self.used_today = None
            self.left_today = None
            self.last_update_utc = None
            self.alert_sent_today = False

    def update_from_headers(self, headers: Mapping[str, Any]) -> None:
        with self._lock:
            self._reset_if_new_day()

            used = _to_int(headers.get("api-credits-used"))
            left = _to_int(headers.get("api-credits-left"))

            if used is not None:
                self.used_today = used
            if left is not None:
                self.left_today = left

            self.last_update_utc = datetime.now(timezone.utc)

    def snapshot(self) -> dict:
        with self._lock:
            self._reset_if_new_day()

            if self.used_today is None or self.left_today is None:
                return {
                    "available": False,
                    "used": None,
                    "left": None,
                    "limit": self.daily_limit,
                    "remaining_pct": None,
                    "last_update_utc": self.last_update_utc,
                    "reset_at_utc": self._next_midnight_utc(),
                }

            total = self.used_today + self.left_today
            if total <= 0:
                total = self.daily_limit

            remaining_pct = round((self.left_today / total) * 100, 1)

            return {
                "available": True,
                "used": self.used_today,
                "left": self.left_today,
                "limit": total,
                "remaining_pct": remaining_pct,
                "last_update_utc": self.last_update_utc,
                "reset_at_utc": self._next_midnight_utc(),
            }

    def _next_midnight_utc(self) -> datetime:
        now = datetime.now(timezone.utc)
        tomorrow = now.date().fromordinal(now.date().toordinal() + 1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=timezone.utc)

    def format_message(self) -> str:
        data = self.snapshot()

        if not data["available"]:
            return (
                "📊 Quota Twelve Data\n"
                "🔢 Données non disponibles\n"
                "⏳ Réinitialisation à minuit UTC\n"
                "⚠️ Impossible de lire les headers `api-credits-used` / `api-credits-left`"
            )

        used = data["used"]
        limit = data["limit"]
        left = data["left"]
        pct = data["remaining_pct"]

        return (
            "📊 Quota Twelve Data\n"
            f"🔢 {used} / {limit} appels utilisés aujourd'hui\n"
            "⏳ Réinitialisation à minuit UTC\n"
            f"⚠️ {pct}% restants"
        )

    def should_alert_low_quota(self, threshold_pct: float = 20.0) -> bool:
        with self._lock:
            self._reset_if_new_day()

            if self.used_today is None or self.left_today is None:
                return False

            total = self.used_today + self.left_today
            if total <= 0:
                total = self.daily_limit

            remaining_pct = (self.left_today / total) * 100
            return remaining_pct < threshold_pct and not self.alert_sent_today

    def mark_alert_sent(self) -> None:
        with self._lock:
            self.alert_sent_today = True
