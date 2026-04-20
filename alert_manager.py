import time
import threading
import asyncio
from typing import Dict, List
from config import ALERTS_FILE
from utils import load_json, save_json

class AlertManager:
    _instance = None

    def __init__(self):
        self.alerts = load_json(ALERTS_FILE)
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self._loop = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

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
            with self.lock:
                alerts_copy = {uid: list(alerts) for uid, alerts in self.alerts.items()}
            for user_id, alerts in alerts_copy.items():
                for alert in alerts:
                    if alert.get("triggered"):
                        continue
                    price_data = await fetcher.get_realtime_price(alert["symbol"])
                    if not price_data:
                        continue
                    current_price = price_data["price"]
                    condition_met = False
                    if alert["condition"] == "above" and current_price >= alert["price"]:
                        condition_met = True
                    elif alert["condition"] == "below" and current_price <= alert["price"]:
                        condition_met = True
                    if condition_met:
                        alert["triggered"] = True
                        await self._notify_user(bot_app, user_id, alert, current_price)
            with self.lock:
                save_json(ALERTS_FILE, self.alerts)
            await asyncio.sleep(10)

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

    def add_alert(self, user_id: int, symbol: str, condition: str, price: float) -> int:
        user_id = str(user_id)
        with self.lock:
            if user_id not in self.alerts:
                self.alerts[user_id] = []
            alert_id = len(self.alerts[user_id]) + 1
            alert = {
                "id": alert_id,
                "symbol": symbol.upper(),
                "condition": condition,
                "price": price,
                "triggered": False
            }
            self.alerts[user_id].append(alert)
            save_json(ALERTS_FILE, self.alerts)
            return alert_id

    def get_alerts(self, user_id: int) -> List[Dict]:
        user_id = str(user_id)
        return self.alerts.get(user_id, [])

    def delete_alert(self, user_id: int, alert_id: int) -> bool:
        user_id = str(user_id)
        with self.lock:
            if user_id in self.alerts:
                for i, alert in enumerate(self.alerts[user_id]):
                    if alert["id"] == alert_id:
                        del self.alerts[user_id][i]
                        save_json(ALERTS_FILE, self.alerts)
                        return True
        return False

    def clear_alerts(self, user_id: int):
        user_id = str(user_id)
        with self.lock:
            if user_id in self.alerts:
                self.alerts[user_id] = []
                save_json(ALERTS_FILE, self.alerts)