#!/usr/bin/env python3
"""
Bitsure Teddy - Main Entry Point
"""

import logging
import os

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_TOKEN

from data_fetcher import DataFetcher
from user_manager import UserManager
from alert_manager import AlertManager
from database import init_db

# =========================================================
# INIT DATABASE
# =========================================================

init_db()

# =========================================================
# IMPORT HANDLERS
# =========================================================

from admin_handlers import (
    quota,
)

from bot_handlers import (
    start,
    help_command,
    analyse,
    price,
    alert,
    alerts,
    delalert,
    clearalerts,
    trend,
    volatility,
    correlation,
    levels,
    settings,
    settimeframe,
    setrisk,
    setlanguage,
    usage,
    status,
    about,
    myid,
    broadcast,
    reload_cmd,
    stats,
    find_memo,
    upgrade,
    plan_callback,
    pre_checkout,
    successful_payment,
    pay_binance,
    confirm_payment,
    support,
    snapshot,
    verify,
    historique,
    clearhistory,
    menu_command,
    menu_callback,
    symbol_callback,
    clearalerts_callback,
    backtest,
    terms_callback,
    sentiment,
    compare,
    top,
    fav,
    teddy,
    learn,
    check,
    ask,
    start_weekly_report_scheduler,
    start_signal_monitoring,
    handle_pending_alert_input,
    paper,
    switchapi,
    check_signal_outcomes,
    refreshhistory,
)

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# =========================================================
# MAIN
# =========================================================

def main():

    if not TELEGRAM_TOKEN:
        raise ValueError(
            "❌ TELEGRAM_TOKEN manquant."
        )

    logger.info("Initializing services...")

    # =====================================================
    # SINGLETONS
    # =====================================================

    fetcher = DataFetcher.get_instance()

    user_mgr = UserManager.get_instance()

    alert_mgr = AlertManager.get_instance()

    # =====================================================
    # TELEGRAM APP
    # =====================================================

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    # =====================================================
    # BACKGROUND TASKS
    # =====================================================

    try:

        start_weekly_report_scheduler(app)

        logger.info(
            "Weekly scheduler started."
        )

    except Exception as e:

        logger.warning(
            f"Scheduler start failed: {e}"
        )

    try:

        start_signal_monitoring(app)

        logger.info(
            "Signal monitoring started."
        )

    except Exception as e:

        logger.warning(
            f"Signal monitoring failed: {e}"
        )

    try:

        alert_mgr.start_monitoring(app)

        logger.info(
            "Alert monitoring started."
        )

    except Exception as e:

        logger.warning(
            f"Alert monitoring failed: {e}"
        )

    # =====================================================
    # COMMANDS
    # =====================================================

    handlers = [

        ("start", start),
        ("help", help_command),
        ("menu", menu_command),

        ("paper", paper),

        ("switchapi", switchapi),

        ("refreshhistory", refreshhistory),

        ("analyse", analyse),
        ("price", price),

        ("alert", alert),
        ("alerts", alerts),
        ("delalert", delalert),
        ("clearalerts", clearalerts),

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

        ("myid", myid),

        ("broadcast", broadcast),

        ("reload", reload_cmd),

        ("stats", stats),

        ("quota", quota),

        ("find_memo", find_memo),

        ("upgrade", upgrade),

        ("support", support),

        ("pay_binance", pay_binance),

        ("confirm_payment", confirm_payment),

        ("snapshot", snapshot),

        ("verify", verify),

        ("historique", historique),

        ("clearhistory", clearhistory),

        ("sentiment", sentiment),

        ("compare", compare),

        ("top", top),

        ("fav", fav),

        ("learn", learn),

        ("check", check),

        ("ask", ask),

        ("backtest", backtest),

        ("teddy", teddy),
    ]

    seen = set()

    for cmd, func in handlers:

        if cmd in seen:

            logger.warning(
                f"Duplicate command skipped: /{cmd}"
            )

            continue

        seen.add(cmd)

        app.add_handler(
            CommandHandler(cmd, func)
        )

    # =====================================================
    # TEXT INPUTS
    # =====================================================

    app.add_handler(

        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_pending_alert_input
        )
    )

    # =====================================================
    # CALLBACKS
    # =====================================================

    app.add_handler(

        CallbackQueryHandler(
            menu_callback,
            pattern=(
                "^(menu_|cmd_|checkdir_|"
                "paperdir_|check_subscription|"
                "clearhistory_|switchapi_)"
            )
        )
    )

    app.add_handler(

        CallbackQueryHandler(
            symbol_callback,
            pattern="^(symcat_|sympage_|symsel_|noop)"
        )
    )

    app.add_handler(

        CallbackQueryHandler(
            clearalerts_callback,
            pattern="^clearalerts_"
        )
    )

    app.add_handler(

        CallbackQueryHandler(
            plan_callback,
            pattern="^plan_"
        )
    )

    app.add_handler(

        CallbackQueryHandler(
            terms_callback,
            pattern="^terms_"
        )
    )

    # =====================================================
    # START BOT
    # =====================================================

    logger.info(
        "Bitsure Teddy started successfully."
    )

    # =====================================================
    # START WEBSOCKET
    # =====================================================

    try:

        fetcher.start_websocket()

        logger.info(
            "Realtime websocket started."
        )

    except Exception as e:

        logger.warning(
            f"Websocket startup failed: {e}"
        )

    # =====================================================
    # WEBHOOK / POLLING
    # =====================================================

    webhook_url = os.environ.get(
        "WEBHOOK_URL"
    )

    if webhook_url:

        logger.info(
            f"Starting webhook mode: {webhook_url}"
        )

        app.run_webhook(
            listen="0.0.0.0",
            port=int(
                os.environ.get(
                    "PORT",
                    "8443"
                )
            ),
            url_path=TELEGRAM_TOKEN,
            webhook_url=(
                f"{webhook_url}/"
                f"{TELEGRAM_TOKEN}"
            ),
        )

    else:

        logger.info(
            "Starting polling mode."
        )

        app.run_polling(
            drop_pending_updates=True
        )

# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":

    main()