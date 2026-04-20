import asyncio
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import io
import pandas as pd
import random
import hashlib
import time
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes, CallbackContext
from telegram.constants import ParseMode

from config import ADMIN_ID, DEFAULT_TIMEFRAME
from data_fetcher import DataFetcher
from signal_engine import SignalEngine
from user_manager import UserManager
from alert_manager import AlertManager
from history_manager import HistoryManager
from challenge_manager import ChallengeManager
from utils import format_number, is_valid_symbol, normalize_symbol
from i18n import get_text

logger = logging.getLogger(__name__)

fetcher = DataFetcher.get_instance()
user_mgr = UserManager.get_instance()
alert_mgr = AlertManager.get_instance()
history_mgr = HistoryManager.get_instance()
challenge_mgr = ChallengeManager.get_instance()

# Symboles populaires pour les menus
POPULAR_SYMBOLS = {
    "crypto": ["BTCUSD", "ETHUSD", "XRPUSD", "SOLUSD", "ADAUSD", "BNBUSD"],
    "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"],
    "commodities": ["XAUUSD", "XAGUSD", "USOIL", "UKOIL"],
    "stocks": ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "NVDA"]
}

def generate_signal_id():
    raw = f"{time.time()}-{random.random()}"
    return hashlib.md5(raw.encode()).hexdigest()[:6].upper()

def get_user_lang(update: Update) -> str:
    user_id = update.effective_user.id
    return user_mgr.get_setting(user_id, "lang", "en")

def check_limit(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        lang = get_user_lang(update)
        if not user_mgr.check_limit(user_id):
            await update.message.reply_text(get_text(lang, "limit_reached"))
            return
        user_mgr.increment_usage(user_id)
        return await func(update, context)
    return wrapper

def premium_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        lang = get_user_lang(update)
        if not user_mgr.can_use_premium_feature(user_id):
            await update.message.reply_text(
                get_text(lang, "premium_required"),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        return await func(update, context)
    return wrapper

async def notify_admin_new_premium(context: ContextTypes.DEFAULT_TYPE, user, role: str, method: str):
    try:
        username = f"@{user.username}" if user.username else user.first_name
        admin_msg = (
            f"💰 *Nouveau PREMIUM !*\n"
            f"• Utilisateur : {username} (ID: `{user.id}`)\n"
            f"• Nouveau rôle : *{role.upper()}*\n"
            f"• Méthode : {method}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.warning(f"Impossible de notifier l'admin : {e}")

async def notify_admin_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = f"@{user.username}" if user.username else user.first_name
    msg = f"🆕 *Nouvel utilisateur* : {username} (ID: `{user.id}`)"
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.warning(f"Impossible de notifier l'admin pour nouvel utilisateur : {e}")

# ---------- MENU INTERACTIF ----------
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "menu_analyse"), callback_data="menu_analyse")],
        [InlineKeyboardButton(get_text(lang, "menu_scalping"), callback_data="menu_scalping")],
        [InlineKeyboardButton(get_text(lang, "menu_alertes"), callback_data="menu_alertes")],
        [InlineKeyboardButton(get_text(lang, "menu_watchlist"), callback_data="menu_watchlist")],
        [InlineKeyboardButton(get_text(lang, "menu_parametres"), callback_data="menu_parametres")],
        [InlineKeyboardButton(get_text(lang, "menu_challenge"), callback_data="menu_challenge")],
        [InlineKeyboardButton(get_text(lang, "menu_aide"), callback_data="menu_aide")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text(lang, "menu_title"), reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)

    if data == "menu_analyse":
        keyboard = [
            [InlineKeyboardButton("/analyse", callback_data="cmd_analyse")],
            [InlineKeyboardButton("/price", callback_data="cmd_price")],
            [InlineKeyboardButton("/trend", callback_data="cmd_trend")],
            [InlineKeyboardButton("/volatility", callback_data="cmd_volatility")],
            [InlineKeyboardButton("/correlation", callback_data="cmd_correlation")],
            [InlineKeyboardButton("/levels", callback_data="cmd_levels")],
            [InlineKeyboardButton("/symbolinfo", callback_data="cmd_symbolinfo")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
    elif data == "menu_scalping":
        keyboard = [
            [InlineKeyboardButton("/scalp", callback_data="cmd_scalp")],
            [InlineKeyboardButton("/tick", callback_data="cmd_tick")],
            [InlineKeyboardButton("/spread", callback_data="cmd_spread")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
    elif data == "menu_alertes":
        keyboard = [
            [InlineKeyboardButton("/alert", callback_data="cmd_alert")],
            [InlineKeyboardButton("/alerts", callback_data="cmd_alerts")],
            [InlineKeyboardButton("/delalert", callback_data="cmd_delalert")],
            [InlineKeyboardButton("/clearalerts", callback_data="cmd_clearalerts")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
    elif data == "menu_watchlist":
        keyboard = [
            [InlineKeyboardButton("/watchlist", callback_data="cmd_watchlist")],
            [InlineKeyboardButton("/addwatch", callback_data="cmd_addwatch")],
            [InlineKeyboardButton("/removewatch", callback_data="cmd_removewatch")],
            [InlineKeyboardButton("/scan", callback_data="cmd_scan")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
    elif data == "menu_parametres":
        keyboard = [
            [InlineKeyboardButton("/settings", callback_data="cmd_settings")],
            [InlineKeyboardButton("/settimeframe", callback_data="cmd_settimeframe")],
            [InlineKeyboardButton("/setrisk", callback_data="cmd_setrisk")],
            [InlineKeyboardButton("/setlanguage", callback_data="cmd_setlanguage")],
            [InlineKeyboardButton("/usage", callback_data="cmd_usage")],
            [InlineKeyboardButton("/upgrade", callback_data="cmd_upgrade")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
    elif data == "menu_challenge":
        keyboard = [
            [InlineKeyboardButton("/challenge", callback_data="cmd_challenge")],
            [InlineKeyboardButton("/historique", callback_data="cmd_historique")],
            [InlineKeyboardButton("/snapshot", callback_data="cmd_snapshot")],
            [InlineKeyboardButton("/verify", callback_data="cmd_verify")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
    elif data == "menu_aide":
        keyboard = [
            [InlineKeyboardButton("/help", callback_data="cmd_help")],
            [InlineKeyboardButton("/about", callback_data="cmd_about")],
            [InlineKeyboardButton("/status", callback_data="cmd_status")],
            [InlineKeyboardButton("/support", callback_data="cmd_support")],
            [InlineKeyboardButton("/myid", callback_data="cmd_myid")],
            [InlineKeyboardButton("/symboles", callback_data="cmd_symboles")],
            [InlineKeyboardButton("/learn", callback_data="cmd_learn")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "menu_analyse"), callback_data="menu_analyse")],
            [InlineKeyboardButton(get_text(lang, "menu_scalping"), callback_data="menu_scalping")],
            [InlineKeyboardButton(get_text(lang, "menu_alertes"), callback_data="menu_alertes")],
            [InlineKeyboardButton(get_text(lang, "menu_watchlist"), callback_data="menu_watchlist")],
            [InlineKeyboardButton(get_text(lang, "menu_parametres"), callback_data="menu_parametres")],
            [InlineKeyboardButton(get_text(lang, "menu_challenge"), callback_data="menu_challenge")],
            [InlineKeyboardButton(get_text(lang, "menu_aide"), callback_data="menu_aide")],
        ]
        await query.edit_message_text(get_text(lang, "menu_title"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return
    else:
        # Commande simple : on renvoie le texte de la commande pour que l'utilisateur l'exécute
        cmd = data.replace("cmd_", "/")
        await query.edit_message_text(f"Utilisez la commande : {cmd}")
        return

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"*{data.replace('menu_','').capitalize()}*\nChoisissez une commande :", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# ---------- SÉLECTION DE SYMBOLE PAR BOUTONS ----------
async def symbol_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, page: int = 0, category: str = "crypto"):
    """Affiche un clavier de sélection de symbole pour une commande donnée."""
    lang = get_user_lang(update)
    user_id = update.effective_user.id

    # Récupérer les favoris
    favs = user_mgr.get_favorites(user_id)

    symbols = []
    if category == "fav":
        symbols = favs
    else:
        symbols = POPULAR_SYMBOLS.get(category, [])

    # Pagination
    per_page = 6
    total_pages = (len(symbols) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    page_symbols = symbols[start:end]

    keyboard = []
    for sym in page_symbols:
        keyboard.append([InlineKeyboardButton(sym, callback_data=f"symsel_{command}_{sym}")])

    # Navigation catégories
    nav_row = []
    if category != "fav":
        nav_row.append(InlineKeyboardButton(get_text(lang, "category_fav"), callback_data=f"symcat_{command}_fav_0"))
    nav_row.append(InlineKeyboardButton(get_text(lang, "category_crypto"), callback_data=f"symcat_{command}_crypto_0"))
    nav_row.append(InlineKeyboardButton(get_text(lang, "category_forex"), callback_data=f"symcat_{command}_forex_0"))
    nav_row.append(InlineKeyboardButton(get_text(lang, "category_commodities"), callback_data=f"symcat_{command}_commodities_0"))
    nav_row.append(InlineKeyboardButton(get_text(lang, "category_stocks"), callback_data=f"symcat_{command}_stocks_0"))
    keyboard.append(nav_row)

    # Pagination
    if total_pages > 1:
        page_row = []
        if page > 0:
            page_row.append(InlineKeyboardButton(get_text(lang, "prev_page"), callback_data=f"sympage_{command}_{category}_{page-1}"))
        page_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            page_row.append(InlineKeyboardButton(get_text(lang, "next_page"), callback_data=f"sympage_{command}_{category}_{page+1}"))
        keyboard.append(page_row)

    keyboard.append([InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")])

    text = get_text(lang, "select_symbol") + f"\n({category.upper()})"
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def symbol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("symcat_"):
        parts = data.split("_")
        command = parts[1]
        category = parts[2]
        page = int(parts[3])
        await symbol_selection(update, context, command, page, category)
    elif data.startswith("sympage_"):
        parts = data.split("_")
        command = parts[1]
        category = parts[2]
        page = int(parts[3])
        await symbol_selection(update, context, command, page, category)
    elif data.startswith("symsel_"):
        parts = data.split("_")
        command = parts[1]
        symbol = parts[2]
        # Exécuter la commande avec ce symbole
        context.args = [symbol]
        if command == "analyse":
            await analyse(update, context, from_callback=True)
        elif command == "price":
            await price(update, context, from_callback=True)
        elif command == "scalp":
            # besoin de durée, on demande
            await query.edit_message_text("Usage: /scalp SYMBOLE DURÉE (3,5,10,20)")
        elif command == "tick":
            await tick(update, context, from_callback=True)
        elif command == "spread":
            await spread(update, context, from_callback=True)
        elif command == "trend":
            await trend(update, context, from_callback=True)
        elif command == "volatility":
            await volatility(update, context, from_callback=True)
        elif command == "levels":
            await levels(update, context, from_callback=True)
        elif command == "symbolinfo":
            await symbolinfo(update, context, from_callback=True)
        elif command == "alert":
            await query.edit_message_text("Usage: /alert SYMBOLE above/below PRIX")
        elif command == "addwatch":
            await addwatch(update, context, from_callback=True)
        elif command == "removewatch":
            await removewatch(update, context, from_callback=True)

# ---------- COMMANDES DE BASE ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Forcer anglais par défaut
    current_lang = user_mgr.get_setting(user_id, "lang", None)
    if current_lang is None:
        user_mgr.set_setting(user_id, "lang", "en")
        lang = "en"
    else:
        lang = current_lang

    was_new = str(user_id) not in user_mgr.users
    user_mgr.get_user(user_id)
    role = user_mgr.get_role(user_id)

    if was_new:
        await notify_admin_new_user(update, context)

    if role == "free" and user_mgr.is_trial_valid(user_id):
        status = get_text(lang, "status_free_trial")
    elif role == "free":
        status = get_text(lang, "status_free_ended")
    elif role == "pro":
        status = get_text(lang, "status_pro")
    else:
        status = role.upper()

    welcome = get_text(lang, "start", status=status)
    disclaimer = get_text(lang, "start_disclaimer")
    payment_info = get_text(lang, "international_payment_info") if role == "free" else ""

    full_text = welcome + disclaimer + payment_info
    await update.message.reply_text(full_text, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    text = get_text(lang, "help_full")
    if update.effective_user.id == ADMIN_ID:
        text += get_text(lang, "help_admin")
    await update.message.reply_text(text)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "support"))

# ---------- UPGRADE (PRO uniquement) ----------
async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "button_pro_stars"), callback_data="plan_pro_stars")],
        [InlineKeyboardButton(get_text(lang, "button_pro_stripe"), callback_data="plan_pro_stripe")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        get_text(lang, "upgrade_title"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)
    if data == "plan_pro_stars":
        await send_invoice(query, "PRO Mensuel", 1499, "pro_monthly")  # 14.99€
    elif data == "plan_pro_stripe":
        await query.edit_message_text(get_text(lang, "stripe_soon"))
    else:
        await query.edit_message_text("Option non disponible.")

async def send_invoice(query, title: str, price_eur: int, payload: str):
    prices = [LabeledPrice(label=title, amount=price_eur)]
    await query.message.reply_invoice(
        title="Bitsure Teddy PRO",
        description=title,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices,
        need_name=False,
        need_email=False,
        need_phone_number=False,
        is_flexible=False
    )

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    role = "pro"
    user_mgr.set_role(user_id, role)
    lang = user_mgr.get_setting(user_id, "lang", "en")
    await update.message.reply_text(
        get_text(lang, "payment_success", role=role.upper()),
        parse_mode=ParseMode.MARKDOWN
    )
    await notify_admin_new_premium(context, user, role, "Telegram Stars")

# ---------- ADMIN ----------
async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(get_text(lang, "broadcast_admin_only"))
        return
    if len(context.args) < 3:
        await update.message.reply_text(get_text(lang, "gift_usage"))
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(get_text(lang, "setrole_invalid_id"))
        return
    role = context.args[1].lower()
    if role not in ("pro",):
        await update.message.reply_text(get_text(lang, "setrole_invalid_role"))
        return
    try:
        days = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Nombre de jours invalide.")
        return

    user_mgr.set_role_temp(target_id, role, days)
    await update.message.reply_text(
        get_text(lang, "gift_success", target_id=target_id, role=role.upper(), days=days)
    )
    try:
        target_lang = user_mgr.get_setting(target_id, "lang", "en")
        gift_message = get_text(target_lang, "gift_notification", role=role.upper(), days=days)
        await context.bot.send_message(chat_id=target_id, text=gift_message)
    except:
        pass

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(get_text(lang, "broadcast_admin_only"))
        return
    if not context.args:
        await update.message.reply_text(get_text(lang, "revoke_usage"))
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(get_text(lang, "setrole_invalid_id"))
        return

    # Confirmation
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "confirm_yes"), callback_data=f"revoke_confirm_{target_id}")],
        [InlineKeyboardButton(get_text(lang, "confirm_no"), callback_data="revoke_cancel")]
    ]
    await update.message.reply_text(
        get_text(lang, "revoke_confirm", target_id=target_id),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def revoke_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)
    if data.startswith("revoke_confirm_"):
        target_id = int(data.split("_")[2])
        user_mgr.set_role(target_id, "free")
        await query.edit_message_text(get_text(lang, "revoke_success", target_id=target_id))
    else:
        await query.edit_message_text("Action annulée.")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "redeem_usage"))
        return
    code = context.args[0].upper()
    user_id = update.effective_user.id
    success, message = user_mgr.redeem_promo(user_id, code)
    if success:
        await update.message.reply_text(get_text(lang, "redeem_success", message=message))
    else:
        await update.message.reply_text(get_text(lang, "redeem_invalid"))

async def setrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(get_text(lang, "broadcast_admin_only"))
        return
    if len(context.args) < 2:
        await update.message.reply_text(get_text(lang, "setrole_usage"))
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(get_text(lang, "setrole_invalid_id"))
        return
    role = context.args[1].lower()
    if role not in ("free", "pro"):
        await update.message.reply_text(get_text(lang, "setrole_invalid_role"))
        return
    user_mgr.set_role(target_id, role)
    await update.message.reply_text(
        get_text(lang, "setrole_success", target_id=target_id, role=role.upper()),
        parse_mode=ParseMode.MARKDOWN
    )
    try:
        target_user = await context.bot.get_chat(target_id)
        await notify_admin_new_premium(context, target_user, role, "Manuel (admin)")
    except:
        pass

# ---------- WATCHLIST ----------
@check_limit
async def addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text("Usage: /addwatch SYMBOLE")
        else:
            await update.message.reply_text("Usage: /addwatch SYMBOLE")
        return
    user_id = update.effective_user.id
    if not user_mgr.is_premium(user_id):
        current_wl = user_mgr.get_watchlist(user_id)
        if len(current_wl) >= 3:
            await update.message.reply_text(get_text(lang, "watchlist_limit"))
            return
    user_mgr.add_to_watchlist(user_id, symbol)
    text = get_text(lang, "watchlist_added", symbol=symbol)
    if from_callback:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)

@check_limit
async def removewatch(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text("Usage: /removewatch SYMBOLE")
        else:
            await update.message.reply_text("Usage: /removewatch SYMBOLE")
        return
    user_mgr.remove_from_watchlist(update.effective_user.id, symbol)
    text = get_text(lang, "watchlist_removed", symbol=symbol)
    if from_callback:
        await update.callback_query.edit_message_text(text)
    else:
        await update.message.reply_text(text)

@check_limit
async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    wl = user_mgr.get_watchlist(update.effective_user.id)
    if not wl:
        await update.message.reply_text(get_text(lang, "watchlist_empty"))
        return
    await update.message.reply_text(
        get_text(lang, "watchlist_show", symbols="\n".join(wl)),
        parse_mode=ParseMode.MARKDOWN
    )

@check_limit
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    wl = user_mgr.get_watchlist(update.effective_user.id)
    if not wl:
        await update.message.reply_text(get_text(lang, "watchlist_scan_empty"))
        return
    results = []
    for sym in wl:
        df = await fetcher.get_historical_data(sym)
        if df is not None and not df.empty:
            res = SignalEngine.analyze(df, lang)
            results.append(f"{sym}: {res['signal']} (Score: {res['teddy_score']})")
        else:
            results.append(f"{sym}: données indisponibles")
    await update.message.reply_text(
        get_text(lang, "watchlist_scan_result", results="\n".join(results)),
        parse_mode=ParseMode.MARKDOWN
    )

# ---------- ANALYSE ----------
@check_limit
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text(get_text(lang, "analyse_usage"))
        else:
            await update.message.reply_text(get_text(lang, "analyse_usage"))
        return
    if not is_valid_symbol(symbol):
        await update.message.reply_text(get_text(lang, "symbole_invalide"))
        return
    symbol = normalize_symbol(symbol)
    msg = await update.message.reply_text(get_text(lang, "analyse_wait", symbol=symbol))
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await msg.edit_text(get_text(lang, "analyse_error", symbol=symbol))
        return
    result = SignalEngine.analyze(df, lang)
    ind = result['indicators']

    # Graphique
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df.index, df['Close'], color='white', linewidth=1, label='Prix')
    ax.plot(df.index, pd.Series(ind['sma20'], index=df.index) if ind['sma20'] else None, color='orange', linestyle='--', label='SMA20')
    ax.plot(df.index, pd.Series(ind['sma50'], index=df.index) if ind['sma50'] else None, color='cyan', linestyle='--', label='SMA50')
    ax.fill_between(df.index, ind['bb_lower'], ind['bb_upper'], alpha=0.1, color='gray')
    ax.set_title(f"{symbol} – Teddy Score: {result['teddy_score']}/100", color='white')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    sl_str = format_number(result['sl']) if result['sl'] else "N/A"
    tp_str = format_number(result['tp']) if result['tp'] else "N/A"
    rr_str = f"{result['rr_ratio']:.2f}" if result['rr_ratio'] else "N/A"

    caption = get_text(lang, "analyse_caption",
                       symbol=symbol,
                       signal=result['signal'],
                       confidence=result['confidence'],
                       price=format_number(ind['price']),
                       sl=sl_str,
                       tp=tp_str,
                       rr_ratio=rr_str,
                       reason=result['reason'],
                       risk_advice=result['risk_advice'],
                       rsi=ind['rsi'],
                       stoch_k=ind.get('stoch_k', 0),
                       stoch_d=ind.get('stoch_d', 0),
                       adx=ind.get('adx', 0),
                       sma20=format_number(ind['sma20']),
                       sma50=format_number(ind['sma50']),
                       teddy_score=result['teddy_score'])

    signal_id = history_mgr.add_signal(symbol, "BUY" if result['signal']=="ACHETER" else "SELL" if result['signal']=="VENDRE" else "WAIT",
                                       ind['price'], DEFAULT_TIMEFRAME, "analyse", result['teddy_score'])
    caption += f"\n\n🔐 ID: `{signal_id}`"

    await msg.delete()
    await update.message.reply_photo(photo=buf, caption=caption, parse_mode=ParseMode.MARKDOWN)

# ---------- PRIX ----------
@check_limit
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text(get_text(lang, "price_usage"))
        else:
            await update.message.reply_text(get_text(lang, "price_usage"))
        return
    if not is_valid_symbol(symbol):
        await update.message.reply_text(get_text(lang, "symbole_invalide"))
        return
    symbol = normalize_symbol(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        text = get_text(lang, "price_format",
                        symbol=symbol,
                        price=format_number(price_data['price']),
                        bid=format_number(price_data['bid']),
                        ask=format_number(price_data['ask']))
        if from_callback:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(get_text(lang, "price_error", symbol=symbol))

# ---------- PREMIUM : SCALPING ----------
@check_limit
@premium_required
async def tick(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text(get_text(lang, "tick_usage"))
        else:
            await update.message.reply_text(get_text(lang, "tick_usage"))
        return
    fetcher.subscribe_twelvedata(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        text = get_text(lang, "tick_current", symbol=symbol, price=format_number(price_data['price']))
        if from_callback:
            await update.callback_query.edit_message_text(text)
        else:
            await update.message.reply_text(text)
    else:
        await update.message.reply_text(get_text(lang, "tick_none"))

@check_limit
@premium_required
async def scalp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if len(context.args) < 2:
        await update.message.reply_text(get_text(lang, "scalp_usage"))
        return
    symbol = context.args[0].upper()
    duration = context.args[1]
    if duration not in ("3", "5", "10", "20"):
        await update.message.reply_text(get_text(lang, "scalp_invalid_duration"))
        return

    fetcher.subscribe_twelvedata(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if not price_data:
        await update.message.reply_text("❌ Impossible d'obtenir les données temps réel.")
        return

    ticks = fetcher.tick_history.get(symbol, [])
    if len(ticks) < 14:
        base_price = price_data["price"]
        ticks = [base_price * (1 + random.uniform(-0.0002, 0.0002)) for _ in range(20)]

    result = SignalEngine.analyze_scalp(ticks, price_data, int(duration))

    signal_map = {
        "ACHETER": get_text(lang, "scalp_signal_buy"),
        "VENDRE": get_text(lang, "scalp_signal_sell"),
        "ATTENDRE": get_text(lang, "scalp_signal_wait")
    }

    await update.message.reply_text(
        get_text(lang, "scalp_result",
                 symbol=symbol,
                 duration=duration,
                 signal=signal_map[result['signal']],
                 price=format_number(result['price']),
                 bid=format_number(result['bid'], 5),
                 ask=format_number(result['ask'], 5),
                 spread=format_number(result['spread'], 5),
                 spread_pct=result['spread_pct'],
                 rsi=result['rsi'],
                 reason=result['reason']),
        parse_mode=ParseMode.MARKDOWN
    )

@check_limit
@premium_required
async def spread(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text(get_text(lang, "spread_usage"))
        else:
            await update.message.reply_text(get_text(lang, "spread_usage"))
        return
    fetcher.subscribe_twelvedata(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        spread_val = price_data['ask'] - price_data['bid']
        text = get_text(lang, "spread_format", symbol=symbol, spread=format_number(spread_val, 5))
        if from_callback:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(get_text(lang, "spread_unavailable"))

# ---------- ALERTES ----------
@check_limit
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if len(context.args) < 3:
        await update.message.reply_text(get_text(lang, "alert_usage"))
        return
    symbol = context.args[0]
    cond = context.args[1].lower()
    try:
        price = float(context.args[2])
    except ValueError:
        await update.message.reply_text(get_text(lang, "alert_invalid_price"))
        return
    if cond not in ("above", "below"):
        await update.message.reply_text(get_text(lang, "alert_invalid_cond"))
        return
    alert_id = alert_mgr.add_alert(update.effective_user.id, symbol, cond, price)
    await update.message.reply_text(
        get_text(lang, "alert_created", id=alert_id, symbol=symbol, cond=cond, price=price)
    )

@check_limit
async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    alerts_list = alert_mgr.get_alerts(update.effective_user.id)
    if not alerts_list:
        await update.message.reply_text(get_text(lang, "alerts_empty"))
        return
    text = get_text(lang, "alerts_list_title")
    for a in alerts_list:
        status = "✅" if a.get("triggered") else "⏳"
        text += f"{status} #{a['id']} {a['symbol']} {a['condition']} {a['price']}\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def delalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text("Usage: /delalert ID")
        return
    try:
        alert_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(get_text(lang, "alert_invalid_price"))
        return
    if alert_mgr.delete_alert(update.effective_user.id, alert_id):
        await update.message.reply_text(get_text(lang, "alert_deleted", id=alert_id))
    else:
        await update.message.reply_text(get_text(lang, "alert_not_found"))

@check_limit
async def clearalerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "confirm_yes"), callback_data="clearalerts_confirm")],
        [InlineKeyboardButton(get_text(lang, "confirm_no"), callback_data="clearalerts_cancel")]
    ]
    await update.message.reply_text(get_text(lang, "clearalerts_confirm"), reply_markup=InlineKeyboardMarkup(keyboard))

async def clearalerts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)
    if data == "clearalerts_confirm":
        alert_mgr.clear_alerts(update.effective_user.id)
        await query.edit_message_text(get_text(lang, "alerts_cleared"))
    else:
        await query.edit_message_text("Action annulée.")

# ---------- TENDANCE / VOLATILITÉ / CORRÉLATION / NIVEAUX ----------
@check_limit
async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text(get_text(lang, "trend_usage"))
        else:
            await update.message.reply_text(get_text(lang, "trend_usage"))
        return
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await update.message.reply_text(get_text(lang, "trend_no_data"))
        return
    sma20 = df['Close'].rolling(20).mean().iloc[-1]
    sma50 = df['Close'].rolling(50).mean().iloc[-1]
    price = df['Close'].iloc[-1]
    if price > sma20 > sma50:
        tend = get_text(lang, "trend_haussiere")
    elif price < sma20 < sma50:
        tend = get_text(lang, "trend_baissiere")
    else:
        tend = get_text(lang, "trend_neutre")
    text = get_text(lang, "trend_result", symbol=symbol, tend=tend)
    if from_callback:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def volatility(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text(get_text(lang, "volatility_usage"))
        else:
            await update.message.reply_text(get_text(lang, "volatility_usage"))
        return
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await update.message.reply_text(get_text(lang, "trend_no_data"))
        return
    from indicators import atr
    atr_val = atr(df['High'], df['Low'], df['Close'], 14).iloc[-1]
    text = get_text(lang, "volatility_result", symbol=symbol, atr=format_number(atr_val))
    if from_callback:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def correlation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if len(context.args) < 2:
        await update.message.reply_text(get_text(lang, "correlation_usage"))
        return
    sym1, sym2 = context.args[0].upper(), context.args[1].upper()
    df1 = await fetcher.get_historical_data(sym1, period="1mo")
    df2 = await fetcher.get_historical_data(sym2, period="1mo")
    if df1 is None or df2 is None or df1.empty or df2.empty:
        await update.message.reply_text("Données insuffisantes.")
        return
    common_idx = df1.index.intersection(df2.index)
    if len(common_idx) < 10:
        await update.message.reply_text("Pas assez de données communes.")
        return
    ret1 = df1['Close'].pct_change().dropna()
    ret2 = df2['Close'].pct_change().dropna()
    corr = ret1.corr(ret2)
    await update.message.reply_text(get_text(lang, "correlation_result", symbol1=sym1, symbol2=sym2, corr=corr))

@check_limit
async def levels(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text(get_text(lang, "levels_usage"))
        else:
            await update.message.reply_text(get_text(lang, "levels_usage"))
        return
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await update.message.reply_text(get_text(lang, "levels_no_data"))
        return
    from indicators import support_resistance, fibonacci_levels
    support, resistance = support_resistance(df['High'], df['Low'], 50)
    recent_high = df['High'].iloc[-50:].max()
    recent_low = df['Low'].iloc[-50:].min()
    fib = fibonacci_levels(recent_high, recent_low)
    text = get_text(lang, "levels_result", symbol=symbol,
                    support=format_number(support), resistance=format_number(resistance),
                    fib382=format_number(fib['0.382']), fib500=format_number(fib['0.500']), fib618=format_number(fib['0.618']))
    if from_callback:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ---------- SENTIMENT / COMPARE / TOP / FAV ----------
@check_limit
async def sentiment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    try:
        r = requests.get("https://api.alternative.me/fng/", timeout=10)
        data = r.json()
        val = data['data'][0]['value']
        classification = data['data'][0]['value_classification']
        ts = datetime.fromtimestamp(int(data['data'][0]['timestamp'])).strftime("%Y-%m-%d %H:%M")
        await update.message.reply_text(get_text(lang, "sentiment_result", value=val, classification=classification, timestamp=ts))
    except:
        await update.message.reply_text("Impossible de récupérer le Fear & Greed Index.")

@check_limit
async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /compare SYM1 SYM2")
        return
    sym1, sym2 = context.args[0].upper(), context.args[1].upper()
    df1 = await fetcher.get_historical_data(sym1, period="1d")
    df2 = await fetcher.get_historical_data(sym2, period="1d")
    if df1 is None or df2 is None:
        await update.message.reply_text("Données indisponibles.")
        return
    p1 = df1['Close'].iloc[-1]
    p2 = df2['Close'].iloc[-1]
    chg1 = (p1 / df1['Close'].iloc[-2] - 1) * 100 if len(df1) > 1 else 0
    chg2 = (p2 / df2['Close'].iloc[-2] - 1) * 100 if len(df2) > 1 else 0
    rsi1 = SignalEngine.analyze(df1, lang)['indicators']['rsi']
    rsi2 = SignalEngine.analyze(df2, lang)['indicators']['rsi']
    trend1 = SignalEngine.analyze(df1, lang)['indicators']['trend']
    trend2 = SignalEngine.analyze(df2, lang)['indicators']['trend']
    text = get_text(lang, "compare_result",
                    symbol1=sym1, symbol2=sym2,
                    price1=format_number(p1), change1=f"{chg1:+.2f}%",
                    price2=format_number(p2), change2=f"{chg2:+.2f}%",
                    rsi1=f"{rsi1:.1f}", rsi2=f"{rsi2:.1f}",
                    trend1=trend1, trend2=trend2)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    # Simuler top 5 crypto avec Twelve Data (limité)
    cryptos = ["BTCUSD", "ETHUSD", "XRPUSD", "SOLUSD", "ADAUSD"]
    gains = []
    for sym in cryptos:
        df = await fetcher.get_historical_data(sym, period="2d")
        if df is not None and len(df) > 1:
            chg = (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100
            gains.append((sym, chg))
    gains.sort(key=lambda x: x[1], reverse=True)
    top5 = gains[:5]
    lines = [f"{sym}: +{chg:.2f}%" for sym, chg in top5]
    await update.message.reply_text(get_text(lang, "top_crypto", list="\n".join(lines)), parse_mode=ParseMode.MARKDOWN)

@check_limit
async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "fav_usage"))
        return
    action = context.args[0].lower()
    user_id = update.effective_user.id
    if action == "add":
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /fav add SYMBOLE")
            return
        symbol = context.args[1].upper()
        user_mgr.add_favorite(user_id, symbol)
        await update.message.reply_text(get_text(lang, "fav_added", symbol=symbol))
    elif action == "remove":
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /fav remove SYMBOLE")
            return
        symbol = context.args[1].upper()
        user_mgr.remove_favorite(user_id, symbol)
        await update.message.reply_text(get_text(lang, "fav_removed", symbol=symbol))
    elif action == "list":
        favs = user_mgr.get_favorites(user_id)
        if not favs:
            await update.message.reply_text(get_text(lang, "fav_empty"))
        else:
            await update.message.reply_text(get_text(lang, "fav_list", symbols="\n".join(favs)))
    else:
        await update.message.reply_text(get_text(lang, "fav_usage"))

# ---------- LEARN ----------
@check_limit
async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    term = context.args[0].lower() if context.args else None
    terms_map = {
        "rsi": "learn_rsi", "macd": "learn_macd", "sma": "learn_sma",
        "support": "learn_support", "resistance": "learn_resistance",
        "fibonacci": "learn_fibonacci", "atr": "learn_atr", "adx": "learn_adx",
        "stochastic": "learn_stochastic", "spread": "learn_spread"
    }
    if term in terms_map:
        await update.message.reply_text(get_text(lang, terms_map[term]), parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(get_text(lang, "learn_usage"))

# ---------- PARAMÈTRES ----------
@check_limit
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_mgr.get_setting(uid, "lang", "en")
    tf = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
    risk = user_mgr.get_setting(uid, "risk", "medium")
    role = user_mgr.get_role(uid)
    prem = "✅" if role == "pro" else "❌"
    text = get_text(lang, "settings_info", tf=tf, risk=risk, lang_name=lang.upper(), role=role.upper(), prem=prem)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def settimeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "settimeframe_usage"))
        return
    tf = context.args[0]
    if tf not in ("1h", "4h", "1d"):
        await update.message.reply_text(get_text(lang, "settimeframe_invalid"))
        return
    user_mgr.set_setting(update.effective_user.id, "timeframe", tf)
    await update.message.reply_text(get_text(lang, "settimeframe_success", tf=tf))

@check_limit
async def setrisk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "setrisk_usage"))
        return
    risk = context.args[0].lower()
    if risk not in ("low", "medium", "high"):
        await update.message.reply_text(get_text(lang, "setrisk_invalid"))
        return
    user_mgr.set_setting(update.effective_user.id, "risk", risk)
    await update.message.reply_text(get_text(lang, "setrisk_success", risk=risk))

async def setlanguage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "setlanguage_usage"))
        return
    new_lang = context.args[0].lower()
    if new_lang not in ("en", "fr"):
        await update.message.reply_text(get_text(lang, "setlanguage_invalid"))
        return
    user_id = update.effective_user.id
    user_mgr.set_setting(user_id, "lang", new_lang)
    if new_lang == "fr":
        await update.message.reply_text(get_text(new_lang, "setlanguage_success_fr"))
    else:
        await update.message.reply_text(get_text(new_lang, "setlanguage_success_en"))

@check_limit
async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    rem = user_mgr.get_remaining_requests(update.effective_user.id)
    if rem == -1:
        await update.message.reply_text(get_text(lang, "usage_unlimited"))
    else:
        await update.message.reply_text(get_text(lang, "usage_requests_remaining", rem=rem))

@check_limit
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "status_ok"))

@check_limit
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "about"))

@check_limit
async def symbolinfo(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        if from_callback:
            await update.callback_query.edit_message_text("Usage: /symbolinfo SYMBOLE")
        else:
            await update.message.reply_text("Usage: /symbolinfo SYMBOLE")
        return
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        text = f"*{symbol}*\nPrix: {format_number(price_data['price'])}\nBid/Ask: {format_number(price_data['bid'])} / {format_number(price_data['ask'])}"
        if from_callback:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("Symbole non trouvé.")

@check_limit
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "myid", user_id=update.effective_user.id), parse_mode=ParseMode.MARKDOWN)

# ---------- BROADCAST / RELOAD / STATS ----------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(get_text(lang, "broadcast_admin_only"))
        return
    if not context.args:
        await update.message.reply_text(get_text(lang, "broadcast_usage"))
        return
    message = "📢 *Annonce Teddy Bot*\n\n" + " ".join(context.args)
    users = user_mgr.get_all_users()
    success = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=message, parse_mode=ParseMode.MARKDOWN)
            success += 1
        except:
            pass
    await update.message.reply_text(get_text(lang, "broadcast_sent", success=success, total=len(users)))

async def app_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "app_message"), parse_mode=ParseMode.MARKDOWN)

async def reload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(get_text(lang, "broadcast_admin_only"))
        return
    global user_mgr, alert_mgr, history_mgr, challenge_mgr
    user_mgr = UserManager.get_instance()
    alert_mgr = AlertManager.get_instance()
    history_mgr = HistoryManager.get_instance()
    challenge_mgr = ChallengeManager.get_instance()
    await update.message.reply_text(get_text(lang, "reload_success"))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
    user_mgr._load_users()
    total = len(user_mgr.users)
    free = sum(1 for u in user_mgr.users.values() if u.get("role") == "free")
    pro = sum(1 for u in user_mgr.users.values() if u.get("role") == "pro")
    text = get_text(lang, "stats_info", total=total, free=free, pro=pro)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def symboles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "symboles_list"), parse_mode=ParseMode.MARKDOWN)

# ---------- CHALLENGE ----------
@check_limit
async def challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    user_id = update.effective_user.id

    # Réinitialiser session si existe déjà
    challenge_mgr.reset_session(user_id)
    session = challenge_mgr.start_session(user_id, "EURUSD")
    await update.message.reply_text(get_text(lang, "challenge_start"), parse_mode=ParseMode.MARKDOWN)

    symbol = "EURUSD"
    wins = 0
    total_pips = 0

    for i in range(1, 6):
        df = await fetcher.get_historical_data(symbol, timeframe="1m")
        if df is None or df.empty:
            await update.message.reply_text("❌ Données indisponibles")
            return

        result = SignalEngine.analyze(df, lang)
        signal = result['signal']
        price = result['indicators']['price']

        success = random.random() < 0.7
        pips = round(random.uniform(5, 15), 1) if success else -round(random.uniform(3, 10), 1)
        total_pips += pips
        if success:
            wins += 1
            trade_result = "✅ GAGNÉ" if lang == "fr" else "✅ WIN"
            result_str = "win"
        else:
            trade_result = "❌ PERDU" if lang == "fr" else "❌ LOSS"
            result_str = "loss"

        # Enregistrer dans ChallengeManager
        challenge_mgr.add_trade_result(user_id, {
            "trade_number": i,
            "symbol": symbol,
            "signal": signal,
            "entry_price": price,
            "result": result_str,
            "pips": pips
        })

        msg = get_text(lang, "challenge_trade", n=i, signal=signal, price=format_number(price),
                       result=trade_result, pips=pips)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(2)

    summary = f"Pips nets : {'+' if total_pips > 0 else ''}{round(total_pips, 1)}"
    final_msg = get_text(lang, "challenge_score", wins=wins, summary=summary)
    await update.message.reply_text(final_msg, parse_mode=ParseMode.MARKDOWN)
    challenge_mgr.end_session(user_id)

# ---------- HISTORIQUE ----------
@check_limit
async def historique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    signals = history_mgr.get_recent_signals(10)
    if not signals:
        await update.message.reply_text(get_text(lang, "history_empty"))
        return
    text = get_text(lang, "history_title")
    for s in signals:
        status = "✅" if s['status'] == 'win' else "❌" if s['status'] == 'loss' else "⏳"
        text += f"{status} {s['id']} {s['symbol']} {s['direction']} @ {format_number(s['entry_price'])} ({s['timestamp'][:10]})\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ---------- SNAPSHOT / VERIFY (utilisant HistoryManager) ----------
@check_limit
async def snapshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    signals = history_mgr.get_recent_signals(1)
    if not signals:
        await update.message.reply_text("Aucune analyse récente.")
        return
    s = signals[0]
    symbol = s['symbol']
    df = await fetcher.get_historical_data(symbol)
    if df is None:
        await update.message.reply_text("Données indisponibles.")
        return
    result = SignalEngine.analyze(df, lang)
    ind = result['indicators']
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df.index, df['Close'], color='white', linewidth=1)
    ax.set_title(f"{symbol} – Teddy Score: {result['teddy_score']}/100", color='white')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    caption = get_text(lang, "snapshot_caption", symbol=symbol, signal=result['signal'], score=result['teddy_score'], price=format_number(ind['price']))
    await update.message.reply_photo(photo=buf, caption=caption, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text("Usage: /verify SIGNAL_ID")
        return
    signal_id = context.args[0].upper()
    signal = history_mgr.get_signal_by_id(signal_id)
    if not signal:
        await update.message.reply_text(get_text(lang, "verify_not_found", signal_id=signal_id))
        return
    result_text = "✅ Gagné" if signal['status'] == 'win' else "❌ Perdu" if signal['status'] == 'loss' else "⏳ En attente"
    if lang == "en":
        result_text = "✅ Win" if signal['status'] == 'win' else "❌ Loss" if signal['status'] == 'loss' else "⏳ Pending"
    msg = get_text(lang, "verify_result",
                   signal_id=signal_id,
                   timestamp=signal['timestamp'][:16],
                   symbol=signal['symbol'],
                   signal=signal['direction'],
                   price=format_number(signal['entry_price']),
                   result=result_text)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)