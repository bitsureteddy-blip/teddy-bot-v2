#!/usr/bin/env python3
"""
Teddy Trading Bot - Bitsure Teddy
"""

import logging
import os
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

from config import TELEGRAM_TOKEN
from bot_handlers import (
    start, help_command, analyse, price,
    alert, alerts, delalert, clearalerts, trend, volatility, correlation, levels,
    settings, settimeframe, setrisk, setlanguage, usage,
    status, about, symbolinfo, myid, broadcast, reload_cmd, stats, find_memo,
    upgrade, plan_callback, pre_checkout, successful_payment, pay_binance, confirm_payment,
    support, challenge, snapshot, verify, historique,
    menu_command, menu_callback, symbol_callback, clearalerts_callback, backtest, terms_callback,
    sentiment, compare, top, fav, learn, check, start_weekly_report_scheduler
)
from data_fetcher import DataFetcher
from user_manager import UserManager
from alert_manager import AlertManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN manquant dans l'environnement")

    DataFetcher.get_instance()
    UserManager.get_instance()
    AlertManager.get_instance()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    AlertManager.get_instance().start_monitoring(app)
    start_weekly_report_scheduler(app)

    # Commandes
    handlers = [
        ("start", start), ("help", help_command), ("menu", menu_command),
        ("analyse", analyse), ("price", price),
        ("alert", alert), ("alerts", alerts), ("delalert", delalert), ("clearalerts", clearalerts),
        ("trend", trend), ("volatility", volatility), ("correlation", correlation), ("levels", levels),
        ("settings", settings), ("settimeframe", settimeframe), ("setrisk", setrisk), ("setlanguage", setlanguage),
        ("usage", usage), ("status", status), ("about", about), ("symbolinfo", symbolinfo), ("myid", myid),
        ("broadcast", broadcast), ("reload", reload_cmd), ("stats", stats), ("find_memo", find_memo), ("upgrade", upgrade),
        ("support", support), ("pay_binance", pay_binance), ("confirm_payment", confirm_payment),
        ("challenge", challenge), ("snapshot", snapshot), ("verify", verify), ("historique", historique),
        ("sentiment", sentiment), ("compare", compare), ("top", top), ("fav", fav), ("learn", learn), ("check", check),
        ("backtest", backtest)
    ]
    for cmd, func in handlers:
        app.add_handler(CommandHandler(cmd, func))

    # Callbacks
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^(menu_|cmd_)"))
    app.add_handler(CallbackQueryHandler(symbol_callback, pattern="^(symcat_|sympage_|symsel_|noop)"))
    app.add_handler(CallbackQueryHandler(clearalerts_callback, pattern="^clearalerts_"))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern="^plan_"))
    app.add_handler(CallbackQueryHandler(terms_callback, pattern="^terms_"))

    logger.info("Teddy Trading Bot started")
    DataFetcher.get_instance().start_websocket()
    # Utiliser webhook si configuré, sinon polling
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", "8443")),
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{webhook_url}/{TELEGRAM_TOKEN}"
        )
        logger.info(f"Webhook set to {webhook_url}")
    else:
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
