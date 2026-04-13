#!/usr/bin/env python3
"""
Teddy Trading Bot - Bitsure Teddy
Point d'entrée principal
"""

import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters

from config import TELEGRAM_TOKEN
from bot_handlers import (
    start, help_command, analyse, price, scalp, tick, spread,
    alert, alerts, delalert, clearalerts, watchlist, addwatch,
    removewatch, scan, trend, volatility, correlation, levels,
    settings, settimeframe, setrisk, setlanguage, usage,
    status, about, symbolinfo, myid, broadcast, reload_cmd, stats,
    upgrade, plan_callback, pre_checkout, successful_payment,
    support, setrole, symboles   # <--- NOUVEAUX IMPORTS
)
from data_fetcher import DataFetcher
from user_manager import UserManager
from alert_manager import AlertManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    """Initialisation après démarrage du bot"""
    data_fetcher = DataFetcher.get_instance()
    data_fetcher.start_websocket()

def main():
    # Initialisation des singletons
    DataFetcher.get_instance()
    UserManager.get_instance()
    AlertManager.get_instance()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # Commandes principales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyse", analyse))
    app.add_handler(CommandHandler("price", price))

    # Scalping
    app.add_handler(CommandHandler("scalp", scalp))
    app.add_handler(CommandHandler("tick", tick))
    app.add_handler(CommandHandler("spread", spread))

    # Alertes
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("delalert", delalert))
    app.add_handler(CommandHandler("clearalerts", clearalerts))

    # Watchlist
    app.add_handler(CommandHandler("watchlist", watchlist))
    app.add_handler(CommandHandler("addwatch", addwatch))
    app.add_handler(CommandHandler("removewatch", removewatch))
    app.add_handler(CommandHandler("scan", scan))

    # Analyse avancée
    app.add_handler(CommandHandler("trend", trend))
    app.add_handler(CommandHandler("volatility", volatility))
    app.add_handler(CommandHandler("correlation", correlation))
    app.add_handler(CommandHandler("levels", levels))

    # Paramètres utilisateur
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("settimeframe", settimeframe))
    app.add_handler(CommandHandler("setrisk", setrisk))
    app.add_handler(CommandHandler("setlanguage", setlanguage))
    app.add_handler(CommandHandler("usage", usage))

    # Infos & Admin
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("symbolinfo", symbolinfo))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("reload", reload_cmd))
    app.add_handler(CommandHandler("stats", stats))

    # Premium / Paiement
    app.add_handler(CommandHandler("upgrade", upgrade))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern="^plan_"))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Nouvelles commandes
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("setrole", setrole))
    app.add_handler(CommandHandler("symboles", symboles))

    logger.info("Teddy Trading Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()