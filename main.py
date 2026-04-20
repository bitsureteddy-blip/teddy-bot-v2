#!/usr/bin/env python3
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
    status, about, symbolinfo, myid, broadcast, reload_cmd, stats,
    upgrade, plan_callback, pre_checkout, successful_payment,
    support, setrole, symboles, gift, revoke, redeem,
    app_command, challenge, snapshot, verify, historique,
    menu_command, menu_callback, symbol_callback, clearalerts_callback, revoke_callback,
    sentiment, compare, top, fav, learn
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
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared, ready to poll")
    DataFetcher.get_instance().start_twelvedata_websocket()

def main():
    DataFetcher.get_instance()
    UserManager.get_instance()
    AlertManager.get_instance()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    handlers = [
        ("start", start), ("help", help_command), ("menu", menu_command),
        ("analyse", analyse), ("price", price), ("scalp", scalp), ("tick", tick), ("spread", spread),
        ("alert", alert), ("alerts", alerts), ("delalert", delalert), ("clearalerts", clearalerts),
        ("watchlist", watchlist), ("addwatch", addwatch), ("removewatch", removewatch), ("scan", scan),
        ("trend", trend), ("volatility", volatility), ("correlation", correlation), ("levels", levels),
        ("settings", settings), ("settimeframe", settimeframe), ("setrisk", setrisk), ("setlanguage", setlanguage),
        ("usage", usage), ("status", status), ("about", about), ("symbolinfo", symbolinfo), ("myid", myid),
        ("broadcast", broadcast), ("reload", reload_cmd), ("stats", stats), ("upgrade", upgrade),
        ("support", support), ("setrole", setrole), ("symboles", symboles), ("gift", gift),
        ("revoke", revoke), ("redeem", redeem), ("app", app_command),
        ("challenge", challenge), ("snapshot", snapshot), ("verify", verify), ("historique", historique),
        ("sentiment", sentiment), ("compare", compare), ("top", top), ("fav", fav), ("learn", learn)
    ]
    for cmd, func in handlers:
        app.add_handler(CommandHandler(cmd, func))

    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    app.add_handler(CallbackQueryHandler(symbol_callback, pattern="^sym"))
    app.add_handler(CallbackQueryHandler(clearalerts_callback, pattern="^clearalerts_"))
    app.add_handler(CallbackQueryHandler(revoke_callback, pattern="^revoke_"))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern="^plan_"))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logger.info("Teddy Trading Bot started")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()