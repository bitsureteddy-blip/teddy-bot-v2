import time
import threading
import asyncio
from typing import Dict, List

from config import ALERTS_FILE
from utils import load_json, save_json

class AlertManager:
    _instance = None

    def __init__(self):
        self.alerts = load_json(ALERTS_FILE) or {}
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self.bot_app = None  # Sera défini au démarrage

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start_monitoring(self, bot_app):
        """Démarre un thread de vérification des alertes."""
        if self.running:
            return
        self.bot_app = bot_app
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def _monitor_loop(self):
        from data_fetcher import DataFetcher
        fetcher = DataFetcher.get_instance()

        while self.running:
            with self.lock:
                # Copie pour éviter les modifications pendant l'itération
                alerts_copy = {uid: list(alerts) for uid, alerts in self.alerts.items()}

            for user_id_str, alerts in alerts_copy.items():
                for alert in alerts:
                    if alert.get("triggered"):
                        continue

                    # Récupération du prix actuel (synchrone)
                    price_data = fetcher.get_current_price_full(alert["symbol"])
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
                        # Planifier l'envoi du message dans la boucle asyncio principale
                        self._schedule_notification(int(user_id_str), alert, current_price)

            with self.lock:
                save_json(ALERTS_FILE, self.alerts)

            time.sleep(10)

    def _schedule_notification(self, user_id: int, alert: Dict, current_price: float):
        """Ajoute une tâche asynchrone pour notifier l'utilisateur."""
        if self.bot_app:
            # On utilise call_soon_threadsafe pour exécuter du code asynchrone depuis un thread
            loop = self.bot_app.loop
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._notify_user(user_id, alert, current_price),
                    loop
                )

    async def _notify_user(self, user_id: int, alert: Dict, current_price: float):
        """Envoie le message de notification (exécuté dans la boucle principale)."""
        try:
            from user_manager import UserManager
            from i18n import get_text
            user_mgr = UserManager.get_instance()
            lang = user_mgr.get_user_lang(user_id)
            text = get_text(lang, "alert_triggered",
                            symbol=alert['symbol'],
                            condition=alert['condition'],
                            price=alert['price'],
                            current_price=current_price)
            await self.bot_app.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")

    def add_alert(self, user_id: int, symbol: str, condition: str, price: float) -> int:
        user_id_str = str(user_id)
        with self.lock:
            if user_id_str not in self.alerts:
                self.alerts[user_id_str] = []

            # Générer un ID simple
            alert_id = len(self.alerts[user_id_str]) + 1
            alert = {
                "id": alert_id,
                "symbol": symbol.upper(),
                "condition": condition,
                "price": price,
                "triggered": False
            }
            self.alerts[user_id_str].append(alert)
            save_json(ALERTS_FILE, self.alerts)
            return alert_id

    def get_alerts(self, user_id: int) -> List[Dict]:
        user_id_str = str(user_id)
        return self.alerts.get(user_id_str, [])

    def delete_alert(self, user_id: int, alert_id: int) -> bool:
        user_id_str = str(user_id)
        with self.lock:
            if user_id_str in self.alerts:
                for i, alert in enumerate(self.alerts[user_id_str]):
                    if alert.get("id") == alert_id:
                        del self.alerts[user_id_str][i]
                        save_json(ALERTS_FILE, self.alerts)
                        return True
        return False

    def clear_alerts(self, user_id: int):
        user_id_str = str(user_id)
        with self.lock:
            if user_id_str in self.alerts:
                self.alerts[user_id_str] = []
                save_json(ALERTS_FILE, self.alerts)