import time
import threading
from typing import Dict, List
from config import ALERTS_FILE
from utils import load_json, save_json

class AlertManager:
    _instance = None

    def __init__(self):
        self.alerts = load_json(ALERTS_FILE)  # user_id -> [{"id":..., "symbol":..., "condition": "above/below", "price":..., "triggered": bool}]
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_monitoring(self, bot_app):
        """Démarre un thread de vérification des alertes (appelé depuis bot_handlers après init)"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, args=(bot_app,), daemon=True)
        self.thread.start()

    def _monitor_loop(self, bot_app):
        from data_fetcher import DataFetcher
        import asyncio
        fetcher = DataFetcher.get_instance()
        while self.running:
            with self.lock:
                alerts_copy = {uid: list(alerts) for uid, alerts in self.alerts.items()}
            for user_id, alerts in alerts_copy.items():
                for alert in alerts:
                    if alert.get("triggered"):
                        continue
                    # Récupérer le prix courant
                    price_data = asyncio.run(fetcher.get_realtime_price(alert["symbol"]))
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
                        # Envoyer notification
                        asyncio.run(self._notify_user(bot_app, user_id, alert, current_price))
            # Sauvegarde après vérification
            with self.lock:
                save_json(ALERTS_FILE, self.alerts)
            time.sleep(10)  # Vérifier toutes les 10 secondes

    async def _notify_user(self, bot_app, user_id: str, alert: Dict, current_price: float):
        try:
            await bot_app.bot.send_message(
                chat_id=int(user_id),
                text=f"🚨 *Alerte déclenchée* : {alert['symbol']} a atteint {alert['condition']} {alert['price']}\n"
                     f"Prix actuel : {current_price}",
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