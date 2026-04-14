#!/usr/bin/env python3
"""
Teddy Trading Bot - Bitsure Teddy
FIX stable asyncio + PTB v20+
"""

import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)

from config import TELEGRAM_TOKEN
from bot_handlers import (
    start, help_command, analyse, price, scalp, tick, spread,
    alert, alerts, delalert, clearalerts, watchlist, addwatch,
    removewatch, scan, trend, volatility, correlation, levels,
    settings, settimeframe, setrisk, setlanguage, usage,
    status, about, symbolinfo, myid, broadcast, reload_cmd, stats,
    upgrade, plan_callback, pre_checkout, successful_payment,
    support, setrole, symboles, gift, revoke, redeem
)

from data_fetcher import DataFetcher
from user_manager import UserManager
from alert_manager import AlertManager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


async def post_init(app):
    DataFetcher.get_instance().start_websocket()


def build_app():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    # Commands
    handlers = [
        ("start", start),
        ("help", help_command),
        ("analyse", analyse),
        ("price", price),
        ("scalp", scalp),
        ("tick", tick),
        ("spread", spread),
        ("alert", alert),
        ("alerts", alerts),
        ("delalert", delalert),
        ("clearalerts", clearalerts),
        ("watchlist", watchlist),
        ("addwatch", addwatch),
        ("removewatch", removewatch),
        ("scan", scan),
        ("trend", trend),
        ("volatility", volatility),
        ("correlation", correlation),
        ("levels", levels),
        ("settings", settings),
        ("settimeframe", settimeframe),
        ("setrisk", setrisk),
        ("setlanguage", setlanguage),
        ("usage", usage),
        ("status", status),
        ("about", about),
        ("symbolinfo", symbolinfo),
        ("myid", myid),
        ("broadcast", broadcast),
        ("reload", reload_cmd),
        ("stats", stats),
        ("upgrade", upgrade),
        ("support", support),
        ("setrole", setrole),
        ("symboles", symboles),
        ("gift", gift),
        ("revoke", revoke),
        ("redeem", redeem),
    ]

    for cmd, func in handlers:
        app.add_handler(CommandHandler(cmd, func))

    app.add_handler(CallbackQueryHandler(plan_callback, pattern="^plan_"))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    return app


async def main_async():
    # init singletons
    DataFetcher.get_instance()
    UserManager.get_instance()
    AlertManager.get_instance()

    app = build_app()

    logger.info("Teddy Trading Bot started")

    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    # keep alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main_async())