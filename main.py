"""
Teddy Trading Bot - Bitsure Teddy
"""

import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters

from config import TELEGRAM_TOKEN
from bot_handlers import (
    start, help_command, analyse, price, scalp, tick, spread,
    alert, alerts, delalert, clearalerts, watchlist, addwatch,
    removewatch, scan, trend, volatility, correlation, levels,
    settings, settimeframe, setrisk, setlanguage, usage,
    status, about, symbolinfo, myid, upgrade, support, symboles,
    challenge, snapshot, verify, redeem, ask, historique,
    broadcast, reload_config, stats, setrole, gift, revoke,
    pre_checkout, successful_payment, app_command,
    button_callback
)
from data_fetcher import DataFetcher
from user_manager import UserManager
from alert_manager import AlertManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Commandes utilisateur
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("analyse", analyse))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("scalp", scalp))
    application.add_handler(CommandHandler("tick", tick))
    application.add_handler(CommandHandler("spread", spread))
    application.add_handler(CommandHandler("alert", alert))
    application.add_handler(CommandHandler("alerts", alerts))
    application.add_handler(CommandHandler("delalert", delalert))
    application.add_handler(CommandHandler("clearalerts", clearalerts))
    application.add_handler(CommandHandler("watchlist", watchlist))
    application.add_handler(CommandHandler("addwatch", addwatch))
    application.add_handler(CommandHandler("removewatch", removewatch))
    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CommandHandler("trend", trend))
    application.add_handler(CommandHandler("volatility", volatility))
    application.add_handler(CommandHandler("correlation", correlation))
    application.add_handler(CommandHandler("levels", levels))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("settimeframe", settimeframe))
    application.add_handler(CommandHandler("setrisk", setrisk))
    application.add_handler(CommandHandler("setlanguage", setlanguage))
    application.add_handler(CommandHandler("usage", usage))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("symbolinfo", symbolinfo))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("upgrade", upgrade))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("symboles", symboles))
    application.add_handler(CommandHandler("challenge", challenge))
    application.add_handler(CommandHandler("snapshot", snapshot))
    application.add_handler(CommandHandler("verify", verify))
    application.add_handler(CommandHandler("redeem", redeem))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(CommandHandler("historique", historique))
    application.add_handler(CommandHandler("app", app_command))

    # Commandes admin
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("reload", reload_config))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("setrole", setrole))
    application.add_handler(CommandHandler("gift", gift))
    application.add_handler(CommandHandler("revoke", revoke))

    # Handlers pour les paiements Telegram Stars
    application.add_handler(PreCheckoutQueryHandler(pre_checkout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Callback pour les boutons inline
    application.add_handler(CallbackQueryHandler(button_callback))

    alert_mgr.start_monitoring(application)
    application.run_polling()

if __name__ == "__main__":
    main()