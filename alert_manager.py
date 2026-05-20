import time
import threading
import asyncio
from typing import Dict, List
from config import ALERTS_FILE, MAX_ALERTS_FREE, MAX_ALERTS_TESTER, MAX_ALERTS_PRO
from utils import load_json, save_json


class AlertManager:
    _instance = None

    def __init__(self):
        self.alerts = load_json(ALERTS_FILE) or {}
        if not isinstance(self.alerts, dict):
            self.alerts = {}
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self._loop = None
        self._last_save = time.time()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # =========================================================
    # MONITORING
    # =========================================================

    def start_monitoring(self, bot_app):
        if self.running:
            return
        self.running = True
        self._loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, args=(bot_app,), daemon=True)
        self.thread.start()

    def _run_loop(self, bot_app):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._monitor_loop(bot_app))

    async def _monitor_loop(self, bot_app):
        from data_fetcher import DataFetcher
        fetcher = DataFetcher.get_instance()

        while self.running:
            try:
                # 1. Grouper les alertes par symbole
                with self.lock:
                    grouped = {}
                    for uid, alerts in self.alerts.items():
                        for a in alerts:
                            if a.get("triggered"):
                                continue
                            symbol = a["symbol"]
                            if symbol not in grouped:
                                grouped[symbol] = []
                            grouped[symbol].append((uid, a))

                # 2. 1 fetch prix par symbole
                for symbol, alert_list in grouped.items():
                    if not alert_list:
                        continue

                    price_data = await fetcher.get_realtime_price(symbol)
                    if not price_data:
                        continue

                    current_price = float(price_data.get("price", 0))
                    if current_price <= 0:
                        continue

                    # 3. Vérifier toutes les alertes de ce symbole
                    for user_id, alert in alert_list:
                        target = float(alert.get("price", 0))
                        if target <= 0:
                            continue

                        condition_met = False
                        if alert["condition"] == "above" and current_price >= target:
                            condition_met = True
                        elif alert["condition"] == "below" and current_price <= target:
                            condition_met = True

                        if condition_met:
                            alert["triggered"] = True
                            alert["triggered_at"] = time.time()
                            await self._notify_user(bot_app, user_id, alert, current_price)

                # 4. Sauvegarde toutes les 30 secondes max
                if time.time() - self._last_save > 30:
                    with self.lock:
                        save_json(ALERTS_FILE, self.alerts)
                    self._last_save = time.time()

                await asyncio.sleep(10)

            except Exception as e:
                print(f"Alert monitoring error: {e}")
                await asyncio.sleep(30)

    # =========================================================
    # NOTIFICATION
    # =========================================================

    async def _notify_user(self, bot_app, user_id: str, alert: Dict, current_price: float):
        try:
            from user_manager import UserManager
            from i18n import get_text
            user_mgr = UserManager.get_instance()
            lang = user_mgr.get_setting(int(user_id), "lang", "en")
            text = get_text(lang, "alert_triggered",
                            symbol=alert['symbol'],
                            condition=alert['condition'],
                            price=alert['price'],
                            current_price=current_price)
            await bot_app.bot.send_message(
                chat_id=int(user_id),
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")

    # =========================================================
    # LIMITES
    # =========================================================

    def get_alert_limit(self, user_id: int) -> int:
        from user_manager import UserManager
        user_mgr = UserManager.get_instance()
        role = user_mgr.get_role(user_id)
        if role == "pro":
            return MAX_ALERTS_PRO
        if role == "tester":
            return MAX_ALERTS_TESTER
        return MAX_ALERTS_FREE

    # =========================================================
    # ADD
    # =========================================================

    def add_alert(self, user_id: int, symbol: str, condition: str, price: float):
        user_id = str(user_id)
        symbol = symbol.upper().strip()

        if condition not in ["above", "below"]:
            return False, "Condition invalide"

        with self.lock:
            if user_id not in self.alerts:
                self.alerts[user_id] = []

            current_alerts = self.alerts[user_id]
            limit = self.get_alert_limit(int(user_id))

            active_alerts = [a for a in current_alerts if not a.get("triggered")]
            if len(active_alerts) >= limit:
                return False, limit

            existing_ids = [a.get("id", 0) for a in current_alerts]
            alert_id = max(existing_ids) + 1 if existing_ids else 1

            alert = {
                "id": alert_id,
                "symbol": symbol,
                "condition": condition,
                "price": float(price),
                "triggered": False,
                "created_at": time.time(),
            }
            self.alerts[user_id].append(alert)
            save_json(ALERTS_FILE, self.alerts)
            return True, alert_id

    # =========================================================
    # GET
    # =========================================================

    def get_alerts(self, user_id: int) -> List[Dict]:
        user_id = str(user_id)
        return sorted(
            self.alerts.get(user_id, []),
            key=lambda x: x.get("created_at", 0),
            reverse=True
        )

    # =========================================================
    # DELETE
    # =========================================================

    def delete_alert(self, user_id: int, alert_id: int) -> bool:
        user_id = str(user_id)
        with self.lock:
            if user_id in self.alerts:
                for i, alert in enumerate(self.alerts[user_id]):
                    if alert.get("id") == alert_id:
                        del self.alerts[user_id][i]
                        save_json(ALERTS_FILE, self.alerts)
                        return True
        return False

    # =========================================================
    # CLEAR
    # =========================================================

    def clear_alerts(self, user_id: int):
        user_id = str(user_id)
        with self.lock:
            if user_id in self.alerts:
                self.alerts[user_id] = []
                save_json(ALERTS_FILE, self.alerts)

    # =========================================================
    # GET ALL (pour le moteur WebSocket)
    # =========================================================

    def get_all_alerts(self):
        """Retourne toutes les alertes non déclenchées, sans mutation."""
        result = []
        with self.lock:
            for uid, alerts in self.alerts.items():
                for a in alerts:
                    if a.get("triggered"):
                        continue
                    result.append({"user_id": uid, **a})
        return result

    # =========================================================
    # MARK TRIGGERED
    # =========================================================

    def mark_triggered(self, alert_id):
        with self.lock:
            for uid, alerts in self.alerts.items():
                for a in alerts:
                    if a.get("id") == alert_id:
                        a["triggered"] = True
                        a["triggered_at"] = time.time()
                        save_json(ALERTS_FILE, self.alerts)
                        return True
        return False

    # =========================================================
    # CLEANUP
    # =========================================================

    def cleanup_triggered_alerts(self, older_than_hours=24):
        cutoff = time.time() - (older_than_hours * 3600)
        with self.lock:
            for uid in list(self.alerts.keys()):
                self.alerts[uid] = [
                    a for a in self.alerts[uid]
                    if not (a.get("triggered") and a.get("triggered_at", 0) < cutoff)
                ]
            save_json(ALERTS_FILE, self.alerts)
