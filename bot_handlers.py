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
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes, CallbackContext
from telegram.constants import ParseMode

from config import ADMIN_ID, DEFAULT_TIMEFRAME, HISTORY_PERIOD
from data_fetcher import DataFetcher
from signal_engine import SignalEngine
from indicators import atr
from user_manager import UserManager
from alert_manager import AlertManager
from history_manager import HistoryManager
from challenge_manager import ChallengeManager
from utils import format_number, is_valid_symbol, normalize_symbol
from i18n import get_text
from payments import generate_binance_payment

logger = logging.getLogger(__name__)

fetcher = DataFetcher.get_instance()
user_mgr = UserManager.get_instance()
alert_mgr = AlertManager.get_instance()
history_mgr = HistoryManager.get_instance()
challenge_mgr = ChallengeManager.get_instance()
weekly_scheduler = None

# 15 symboles PRO
SYMBOLS_15 = [
    "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "XAUUSD", "WTI", "XAGUSD",
    "AAPL", "TSLA", "NVDA",
    "SPX", "NDX"
]

BACKTEST_SYMBOLS = ["BTCUSD", "ETHUSD", "EURUSD", "XAUUSD", "AAPL"]
BACKTEST_TIMEFRAME = "1h"
BACKTEST_MIN_BARS = 60
BACKTEST_STEP = 24

def generate_signal_id():
    raw = f"{time.time()}-{random.random()}"
    return hashlib.md5(raw.encode()).hexdigest()[:6].upper()

def get_user_lang(update: Update) -> str:
    user_id = update.effective_user.id
    return user_mgr.get_setting(user_id, "lang", "en")

async def respond(update: Update, text: str, **kwargs):
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, **kwargs)
        except:
            await update.callback_query.message.reply_text(text, **kwargs)
    else:
        await update.message.reply_text(text, **kwargs)

async def backtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    await update.message.reply_text("🚀 Lancement du backtest (peut prendre quelques instants)...")
    engine = SignalEngine()

    for symbol in BACKTEST_SYMBOLS:
        logger.info(f"=== BACKTEST {symbol} ===")
        df = await fetcher.get_historical_data(symbol, timeframe=BACKTEST_TIMEFRAME, period=HISTORY_PERIOD)
        if df is None or df.empty:
            await update.message.reply_text(f"⚠️ Pas de données pour {symbol}")
            continue

        trades = []

        for i in range(BACKTEST_MIN_BARS, len(df), BACKTEST_STEP):
            window = df.iloc[:i]
            result = engine.analyze(window, symbol=symbol)

            if result["signal"] not in ("BUY", "SELL"):
                continue

            entry_price = float(df["Close"].iloc[i])
            sl = float(result["sl"])
            tp = float(result["tp1"])
            if sl is None or tp is None or sl == entry_price:
                continue
            is_buy = result["signal"] == "BUY"
            outcome = None
            exit_price = None
            exit_idx = i

            for j in range(i + 1, len(df)):
                low_j = float(df["Low"].iloc[j])
                high_j = float(df["High"].iloc[j])

                if is_buy:
                    if low_j <= sl:
                        outcome = "LOSS"
                        exit_price = sl
                        exit_idx = j
                        break
                    if high_j >= tp:
                        outcome = "WIN"
                        exit_price = tp
                        exit_idx = j
                        break
                else:
                    if high_j >= sl:
                        outcome = "LOSS"
                        exit_price = sl
                        exit_idx = j
                        break
                    if low_j <= tp:
                        outcome = "WIN"
                        exit_price = tp
                        exit_idx = j
                        break

            if outcome is None:
                exit_price = float(df["Close"].iloc[-1])
                exit_idx = len(df) - 1
                if is_buy:
                    outcome = "WIN" if exit_price > entry_price else "LOSS"
                else:
                    outcome = "WIN" if exit_price < entry_price else "LOSS"

            pnl_pct = ((exit_price - entry_price) / entry_price * 100)
            if not is_buy:
                pnl_pct = -pnl_pct

            trades.append({
                "date": str(df.index[i]),
                "symbol": symbol,
                "signal": result["signal"],
                "score": result["teddy_score"],
                "entry": round(entry_price, 5),
                "exit": round(exit_price, 5),
                "sl": round(sl, 5),
                "tp": round(tp, 5),
                "outcome": outcome,
                "pnl_pct": round(pnl_pct, 4),
                "bars_held": exit_idx - i,
            })

        if not trades:
            await update.message.reply_text(f"ℹ️ {symbol}: Aucun trade.")
            continue

        trades_df = pd.DataFrame(trades)
        total = len(trades_df)
        wins = (trades_df["outcome"] == "WIN").sum()
        losses = total - wins
        win_rate = wins / total * 100
        avg_pnl = trades_df["pnl_pct"].mean()
        total_pnl = trades_df["pnl_pct"].sum()
        best = trades_df["pnl_pct"].max()
        worst = trades_df["pnl_pct"].min()
        avg_bars = trades_df["bars_held"].mean()

        cumul = trades_df["pnl_pct"].cumsum()
        max_drawdown = (cumul.cummax() - cumul).max()

        result_text = f"""
📊 {symbol} – Résultats du backtest
━━━━━━━━━━━━━━━━━━━━━━━━
🔢 Trades        : {total}
✅ Gagnants      : {wins} ({win_rate:.1f}%)
❌ Perdants      : {losses}
📈 Gain moyen    : {avg_pnl:.4f}%
💰 Gain total    : {total_pnl:.2f}%
🏆 Meilleur      : {best:.4f}%
📉 Pire          : {worst:.4f}%
📊 Max drawdown  : {max_drawdown:.2f}%
⏳ Durée moyenne : {avg_bars:.0f} bougies
━━━━━━━━━━━━━━━━━━━━━━━━
"""
        await update.message.reply_text(result_text)

async def handle_pending_alert_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.message or not update.message.text:
        return False
    pending_symbol = context.user_data.get("pending_alert_symbol")
    pending_cond = context.user_data.get("pending_alert_cond")
    if not pending_symbol or not pending_cond:
        return False
    lang = get_user_lang(update)
    try:
        price = float(update.message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(get_text(lang, "alert_price_invalid_retry"))
        return True
    alert_id = alert_mgr.add_alert(update.effective_user.id, pending_symbol, pending_cond, price)
    await update.message.reply_text(get_text(lang, "alert_created", id=alert_id, symbol=pending_symbol, cond=pending_cond, price=price))
    context.user_data.pop("pending_alert_symbol", None)
    context.user_data.pop("pending_alert_cond", None)
    return True

def check_limit(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        lang = get_user_lang(update)
        try:
            member = await context.bot.get_chat_member("@Tsworld", user_id)
            if member.status not in ("member", "administrator", "creator"):
                target = update.callback_query.message if update.callback_query else update.message
                await target.reply_text(get_text(lang, "channel_required"))
                return
        except Exception:
            pass
        if func.__name__ != "start" and not user_mgr.has_accepted_terms(user_id):
            if update.callback_query:
                await update.callback_query.answer(get_text(lang, "terms_must_accept"), show_alert=True)
                return
            else:
                await update.message.reply_text(get_text(lang, "terms_must_accept"))
                return
        if not user_mgr.check_limit(user_id):
            if update.callback_query:
                await update.callback_query.answer(get_text(lang, "limit_reached"), show_alert=True)
                return
            else:
                await update.message.reply_text(get_text(lang, "limit_reached"))
                return
        user_mgr.increment_usage(user_id)
        return await func(update, context, *args, **kwargs)
    return wrapper

def premium_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        lang = get_user_lang(update)
        if not user_mgr.has_accepted_terms(user_id):
            if update.callback_query:
                await update.callback_query.answer(get_text(lang, "terms_must_accept"), show_alert=True)
                return
            else:
                await update.message.reply_text(get_text(lang, "terms_must_accept"))
                return
        if not user_mgr.can_use_premium_feature(user_id):
            text = get_text(lang, "premium_required")
            if update.callback_query:
                await update.callback_query.answer(text, show_alert=True)
                return
            else:
                await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
                return
        return await func(update, context, *args, **kwargs)
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
        [InlineKeyboardButton(get_text(lang, "menu_alertes"), callback_data="menu_alertes")],
        [InlineKeyboardButton(get_text(lang, "menu_watchlist"), callback_data="menu_watchlist")],
        [InlineKeyboardButton(get_text(lang, "menu_parametres"), callback_data="menu_parametres")],
        [InlineKeyboardButton(get_text(lang, "menu_upgrade"), callback_data="menu_upgrade")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text(lang, "menu_title"), reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)
    user_id = update.effective_user.id
    message = query.message

    def safe_edit(text, keyboard):
        try:
            return query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            return query.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )

    # --- Sous-menus ---
    if data == "menu_analyse":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "btn_analyse"), callback_data="cmd_analyse")],
            [InlineKeyboardButton(get_text(lang, "btn_price"), callback_data="cmd_price")],
            [InlineKeyboardButton(get_text(lang, "btn_trend"), callback_data="cmd_trend")],
            [InlineKeyboardButton(get_text(lang, "btn_volatility"), callback_data="cmd_volatility")],
            [InlineKeyboardButton(get_text(lang, "btn_levels"), callback_data="cmd_levels")],
            [InlineKeyboardButton(get_text(lang, "btn_symbolinfo"), callback_data="cmd_symbolinfo")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
        await safe_edit(f"*{get_text(lang, 'menu_analyse')}*\n{get_text(lang, 'menu_choose_command')}", keyboard)

    elif data == "menu_alertes":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "btn_alert"), callback_data="cmd_alert")],
            [InlineKeyboardButton(get_text(lang, "btn_alerts"), callback_data="cmd_alerts")],
            [InlineKeyboardButton(get_text(lang, "btn_delalert"), callback_data="cmd_delalert")],
            [InlineKeyboardButton(get_text(lang, "btn_clearalerts"), callback_data="cmd_clearalerts")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
        await safe_edit(f"*{get_text(lang, 'menu_alertes')}*\n{get_text(lang, 'menu_choose_command')}", keyboard)

    elif data == "menu_watchlist":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "btn_watchlist"), callback_data="cmd_watchlist")],
            [InlineKeyboardButton(get_text(lang, "btn_addwatch"), callback_data="cmd_addwatch")],
            [InlineKeyboardButton(get_text(lang, "btn_removewatch"), callback_data="cmd_removewatch")],
            [InlineKeyboardButton(get_text(lang, "btn_scan"), callback_data="cmd_scan")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
        await safe_edit(f"*{get_text(lang, 'menu_watchlist')}*\n{get_text(lang, 'menu_choose_command')}", keyboard)

    elif data == "menu_parametres":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "btn_settings"), callback_data="cmd_settings")],
            [InlineKeyboardButton(get_text(lang, "btn_settimeframe"), callback_data="cmd_settimeframe")],
            [InlineKeyboardButton(get_text(lang, "btn_setlanguage"), callback_data="cmd_setlanguage")],
            [InlineKeyboardButton(get_text(lang, "btn_usage"), callback_data="cmd_usage")],
            [InlineKeyboardButton(get_text(lang, "btn_historique"), callback_data="cmd_historique")],
            [InlineKeyboardButton(get_text(lang, "btn_support"), callback_data="cmd_support")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
        await safe_edit(f"*{get_text(lang, 'menu_parametres')}*\n{get_text(lang, 'menu_choose_command')}", keyboard)

    elif data == "menu_upgrade":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "button_pro_stars"), callback_data="plan_pro_stars")],
            [InlineKeyboardButton(get_text(lang, "button_binance_usdc"), callback_data="plan_binance")],
            [InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")]
        ]
        await safe_edit(f"*{get_text(lang, 'menu_upgrade')}*\n{get_text(lang, 'menu_choose_command')}", keyboard)

    elif data == "menu_back":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "menu_analyse"), callback_data="menu_analyse")],
                [InlineKeyboardButton(get_text(lang, "menu_alertes"), callback_data="menu_alertes")],
            [InlineKeyboardButton(get_text(lang, "menu_watchlist"), callback_data="menu_watchlist")],
            [InlineKeyboardButton(get_text(lang, "menu_parametres"), callback_data="menu_parametres")],
            [InlineKeyboardButton(get_text(lang, "menu_upgrade"), callback_data="menu_upgrade")],
        ]
        await safe_edit(get_text(lang, "menu_title"), keyboard)

    # --- Exécution réelle des commandes ---
    elif data.startswith("cmd_"):
        cmd = data.replace("cmd_", "")
        if cmd.startswith("alertcond_"):
            _,symbol,cond=cmd.split("_")
            context.user_data["pending_alert_symbol"]=symbol
            context.user_data["pending_alert_cond"]=cond
            await query.message.reply_text(get_text(lang,"alert_enter_price")); return
        if cmd.startswith("settimeframe_"):
            context.args=[cmd.split("_",1)[1]]
            await settimeframe(update, context); return
        if cmd.startswith("setlanguage_"):
            context.args=[cmd.split("_",1)[1]]
            await setlanguage(update, context); return
        if cmd.startswith("delalert_"):
            context.args=[cmd.split("_",1)[1]]
            await delalert(update, context); return
        if cmd in ["analyse", "price", "trend", "volatility", "levels", "symbolinfo", "alert", "addwatch", "removewatch"]:
            await symbol_selection(update, context, cmd)

        elif cmd == "alerts":
            alerts_list = alert_mgr.get_alerts(user_id)
            if not alerts_list:
                await message.reply_text(get_text(lang, "alerts_empty"))
            else:
                text = get_text(lang, "alerts_list_title")
                for a in alerts_list:
                    status = "✅" if a.get("triggered") else "⏳"
                    text += f"{status} #{a['id']} {a['symbol']} {a['condition']} {a['price']}\n"
                await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

        elif cmd == "clearalerts":
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "confirm_yes"), callback_data="clearalerts_confirm")],
                [InlineKeyboardButton(get_text(lang, "confirm_no"), callback_data="clearalerts_cancel")]
            ]
            await message.reply_text(get_text(lang, "clearalerts_confirm"), reply_markup=InlineKeyboardMarkup(keyboard))

        elif cmd == "watchlist":
            wl = user_mgr.get_watchlist(user_id)
            if not wl:
                await message.reply_text(get_text(lang, "watchlist_empty"))
            else:
                await message.reply_text(
                    get_text(lang, "watchlist_show", symbols="\n".join(wl)),
                    parse_mode=ParseMode.MARKDOWN
                )

        elif cmd == "scan":
            wl = user_mgr.get_watchlist(user_id)
            if not wl:
                await message.reply_text(get_text(lang, "watchlist_scan_empty"))
            else:
                results = []
                for sym in wl:
                    df = await fetcher.get_historical_data(sym)
                    if df is not None and not df.empty:
                        res = SignalEngine.analyze(df, lang, symbol=sym)
                        results.append(f"{sym}: {res['signal_text']} (Score: {res['teddy_score']})")
                    else:
                        results.append(f"{sym}: {get_text(lang, 'data_unavailable')}")
                await message.reply_text(
                    get_text(lang, "watchlist_scan_result", results="\n".join(results)),
                    parse_mode=ParseMode.MARKDOWN
                )

        elif cmd == "settimeframe":
            kb=[[InlineKeyboardButton("1h",callback_data="cmd_settimeframe_1h"),InlineKeyboardButton("4h",callback_data="cmd_settimeframe_4h"),InlineKeyboardButton("1d",callback_data="cmd_settimeframe_1d")]]
            await message.reply_text(get_text(lang, "settimeframe_choose"), reply_markup=InlineKeyboardMarkup(kb))

        elif cmd == "setlanguage":
            kb=[[InlineKeyboardButton("FR",callback_data="cmd_setlanguage_fr"),InlineKeyboardButton("EN",callback_data="cmd_setlanguage_en")]]
            await message.reply_text(get_text(lang, "setlanguage_choose"), reply_markup=InlineKeyboardMarkup(kb))

        elif cmd == "delalert":
            alerts_list = alert_mgr.get_alerts(user_id)
            if not alerts_list:
                await message.reply_text(get_text(lang, "alerts_empty"))
            else:
                kb=[[InlineKeyboardButton(f"#{a['id']} {a['symbol']} {a['condition']} {a['price']}", callback_data=f"cmd_delalert_{a['id']}")] for a in alerts_list]
                await message.reply_text(get_text(lang, "delalert_pick"), reply_markup=InlineKeyboardMarkup(kb))

        elif cmd == "settings":
            uid = user_id
            lang2 = user_mgr.get_setting(uid, "lang", "en")
            tf = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
            risk = user_mgr.get_setting(uid, "risk", "medium")
            role = user_mgr.get_role(uid)
            prem = "✅" if role == "pro" else "❌"
            await message.reply_text(
                get_text(lang2, "settings_info", tf=tf, risk=risk, lang_name=lang2.upper(), role=role.upper(), prem=prem),
                parse_mode=ParseMode.MARKDOWN
            )

        elif cmd == "historique":
            await query.message.reply_text(get_text(lang, "history_title"))
            await historique(update, context)

        elif cmd == "usage":
            rem = user_mgr.get_remaining_requests(user_id)
            if rem == -1:
                await message.reply_text(get_text(lang, "usage_unlimited"))
            else:
                await message.reply_text(get_text(lang, "usage_requests_remaining", rem=rem))

        elif cmd == "support":
            await message.reply_text(get_text(lang, "support"))

        elif cmd == "upgrade":
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "btn_upgrade_stars"), callback_data="plan_pro_stars")],
                [InlineKeyboardButton(get_text(lang, "btn_upgrade_binance"), callback_data="plan_binance")],
            ]
            await message.reply_text(
                get_text(lang, "upgrade_title"),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        else:
            usage_map = {
                "alert": "alert_usage",
                "delalert": "delalert_usage",
                "addwatch": "addwatch_usage",
                "removewatch": "removewatch_usage",
                "settimeframe": "settimeframe_usage",
                "setlanguage": "setlanguage_usage",
            }
            await message.reply_text(get_text(lang, usage_map.get(cmd, "unknown_command")))

# ---------- SÉLECTION DE SYMBOLE ----------
async def symbol_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str, page: int = 0):
    query = update.callback_query
    await query.answer()
    lang = get_user_lang(update)

    symbols = SYMBOLS_15
    per_page = 8
    total_pages = (len(symbols) + per_page - 1) // per_page
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    page_symbols = symbols[start:end]

    keyboard = []
    for sym in page_symbols:
        keyboard.append([InlineKeyboardButton(sym, callback_data=f"symsel_{command}_{sym}")])

    if total_pages > 1:
        page_row = []
        if page > 0:
            page_row.append(InlineKeyboardButton("◀️", callback_data=f"sympage_{command}_{page-1}"))
        page_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            page_row.append(InlineKeyboardButton("▶️", callback_data=f"sympage_{command}_{page+1}"))
        keyboard.append(page_row)

    keyboard.append([InlineKeyboardButton(get_text(lang, "back"), callback_data="menu_back")])

    text = get_text(lang, "select_symbol")
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except:
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def symbol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)

    if data.startswith("sympage_"):
        parts = data.split("_")
        if len(parts) >= 3:
            _, command, page = parts[0], parts[1], parts[2]
            await symbol_selection(update, context, command, int(page))
        return

    elif data.startswith("symsel_"):
        parts = data.split("_", 2)
        if len(parts) >= 3:
            _, command, symbol = parts
            context.args = [symbol]

            if command == "analyse":
                await analyse(update, context, from_callback=True)
            elif command == "price":
                await price(update, context, from_callback=True)
            elif command == "trend":
                await trend(update, context, from_callback=True)
            elif command == "volatility":
                await volatility(update, context, from_callback=True)
            elif command == "levels":
                await levels(update, context, from_callback=True)
            elif command == "symbolinfo":
                await symbolinfo(update, context, from_callback=True)
            elif command == "alert":
                kb=[[InlineKeyboardButton(get_text(lang,"cond_above"),callback_data=f"cmd_alertcond_{symbol}_above"),InlineKeyboardButton(get_text(lang,"cond_below"),callback_data=f"cmd_alertcond_{symbol}_below")]]
                await query.message.reply_text(get_text(lang,"alert_choose_condition"), reply_markup=InlineKeyboardMarkup(kb))
            elif command == "addwatch":
                context.args=[symbol]
                await addwatch(update, context)
            elif command == "removewatch":
                context.args=[symbol]
                await removewatch(update, context)
        return

    elif data == "noop":
        return

# ---------- START ----------
@check_limit
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    lang = user_mgr.get_setting(user_id, "lang", "en")
    was_new = str(user_id) not in user_mgr.users
    user_mgr.get_user(user_id)

    if was_new:
        await notify_admin_new_user(update, context)

    # Vérifier si l'utilisateur a déjà accepté les conditions
    if not user_mgr.has_accepted_terms(user_id):
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "terms_button"), callback_data="terms_show")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        welcome = get_text(lang, "start", status=get_text(lang, "status_free_trial"))
        await update.message.reply_text(
            welcome + "\n\n" + get_text(lang, "terms_must_accept"),
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Utilisateur existant qui a déjà accepté → comportement normal
    role = user_mgr.get_role(user_id)
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

async def terms_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)
    user_id = update.effective_user.id

    if data == "terms_show":
        keyboard = [
            [InlineKeyboardButton(get_text(lang, "terms_accept"), callback_data="terms_accept")],
            [InlineKeyboardButton(get_text(lang, "terms_refuse"), callback_data="terms_refuse")],
        ]
        await query.edit_message_text(
            get_text(lang, "terms_text"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "terms_accept":
        user_mgr.accept_terms(user_id)
        await query.edit_message_text(
            get_text(lang, "terms_accepted"),
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "terms_refuse":
        await query.edit_message_text(
            get_text(lang, "terms_refused_msg"),
            parse_mode=ParseMode.MARKDOWN
        )

@check_limit
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    trial_msg = ""
    if user_mgr.get_role(update.effective_user.id) == "free" and user_mgr.is_trial_valid(update.effective_user.id):
        trial_days = user_mgr.is_trial_valid(update.effective_user.id)
        trial_msg = "\n" + get_text(lang, "trial_days_left", days=trial_days)
    await update.message.reply_text(get_text(lang, "help_redirect") + trial_msg, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_text(get_user_lang(update), "support"))

# ---------- UPGRADE ----------
@check_limit
async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "button_pro_stars"), callback_data="plan_pro_stars")],
            [InlineKeyboardButton(get_text(lang, "button_binance_usdc"), callback_data="plan_binance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text(lang, "upgrade_title"), parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

@check_limit
async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = get_user_lang(update)
    if data == "plan_pro_stars":
        await send_invoice(query, "PRO 19,99€/mois", 1999, "pro_monthly")
    elif data == "plan_binance":
        await plan_binance_callback(update, context)
    else:
        await query.edit_message_text(get_text(lang, "unavailable_option"))

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

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

@check_limit
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


@check_limit
async def plan_binance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    user_id = update.effective_user.id
    ident, text = generate_binance_payment(user_id, lang)
    user_mgr.add_pending_binance(user_id, ident)
    if update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def pay_binance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await plan_binance_callback(update, context)

@check_limit
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "confirm_payment_usage"))
        return
    uid = int(context.args[0])
    if user_mgr.confirm_binance_payment(uid):
        await update.message.reply_text(get_text(lang, "confirm_payment_ok", user_id=uid))
    else:
        await update.message.reply_text(get_text(lang, "confirm_payment_missing", user_id=uid))

# ---------- ANALYSE ----------
@check_limit
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        text = get_text(lang, "analyse_usage")
        await respond(update, text, parse_mode=ParseMode.MARKDOWN)
        return
    if not is_valid_symbol(symbol):
        await respond(update, get_text(lang, "symbole_invalide"))
        return
    symbol = normalize_symbol(symbol)
    if from_callback:
        msg = await update.callback_query.edit_message_text(get_text(lang, "analyse_wait", symbol=symbol))
    else:
        msg = await update.message.reply_text(get_text(lang, "analyse_wait", symbol=symbol))
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await msg.edit_text(get_text(lang, "analyse_error", symbol=symbol))
        return
    result = SignalEngine.analyze(df, lang, symbol=symbol)
    ind = result['indicators']

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df.index, df['Close'], color='white', linewidth=1, label='Prix')
    ax.plot(df.index, pd.Series(ind['sma20'], index=df.index) if ind['sma20'] else None, color='orange', linestyle='--', label='SMA20')
    ax.plot(df.index, pd.Series(ind['sma50'], index=df.index) if ind['sma50'] else None, color='cyan', linestyle='--', label='SMA50')
    bb_lower = ind.get('bb_lower')
    bb_upper = ind.get('bb_upper')
    if bb_lower is not None and bb_upper is not None:
        ax.fill_between(df.index, bb_lower, bb_upper, alpha=0.1, color='gray')
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

    signal_emoji = {"BUY": "🟢", "SELL": "🔴", "WAIT": "⚪"}.get(result["signal"], "⚪")
    caption = get_text(lang, "analyse_caption",
                       symbol=symbol,
                       signal_emoji=signal_emoji,
                       signal=result['signal_text'],
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
                       adx=ind.get('adx') if pd.notna(ind.get('adx')) else 0.0,
                       sma20=format_number(ind['sma20']),
                       sma50=format_number(ind['sma50']),
                       teddy_score=result['teddy_score'])

    signal_id = history_mgr.add_signal(symbol, result['signal'],
                                       ind['price'], DEFAULT_TIMEFRAME, "analyse", result['teddy_score'])
    caption += f"\n\n🔐 ID: `{signal_id}`"

    await msg.delete()
    if from_callback and update.callback_query:
        await update.callback_query.message.reply_photo(photo=buf, caption=caption, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_photo(photo=buf, caption=caption, parse_mode=ParseMode.MARKDOWN)

# ---------- PRIX ----------
@check_limit
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await respond(update, get_text(lang, "price_usage"), parse_mode=ParseMode.MARKDOWN)
        return
    if not is_valid_symbol(symbol):
        await respond(update, get_text(lang, "symbole_invalide"))
        return
    symbol = normalize_symbol(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        text = get_text(lang, "price_format",
                        symbol=symbol,
                        price=format_number(price_data['price']),
                        bid=format_number(price_data['bid']),
                        ask=format_number(price_data['ask']))
        await respond(update, text, parse_mode=ParseMode.MARKDOWN)
    else:
        await respond(update, get_text(lang, "price_error", symbol=symbol))

# ---------- PREMIUM : SCALPING ----------

# ---------- ALERTES ----------
@check_limit
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await handle_pending_alert_input(update, context):
        return
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
        await update.message.reply_text(get_text(lang, "delalert_usage"))
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
async def addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await respond(update, get_text(lang, "addwatch_usage"))
        return
    watchlist = user_mgr.get_watchlist(update.effective_user.id)
    if symbol in watchlist:
        await respond(update, get_text(lang, "watchlist_already", symbol=symbol))
        return
    user_mgr.add_to_watchlist(update.effective_user.id, symbol)
    await respond(update, get_text(lang, "watchlist_added_styled", symbol=symbol))

@check_limit
async def removewatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await respond(update, get_text(lang, "removewatch_usage"))
        return
    watchlist = user_mgr.get_watchlist(update.effective_user.id)
    if symbol not in watchlist:
        await respond(update, get_text(lang, "watchlist_missing", symbol=symbol))
        return
    user_mgr.remove_from_watchlist(update.effective_user.id, symbol)
    await respond(update, get_text(lang, "watchlist_removed_styled", symbol=symbol))

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
        await query.edit_message_text(get_text(lang, "action_cancelled"))

# ---------- TENDANCE / VOLATILITÉ / CORRÉLATION / NIVEAUX ----------
@check_limit
async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await respond(update, get_text(lang, "trend_usage"), parse_mode=ParseMode.MARKDOWN)
        return
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await respond(update, get_text(lang, "trend_no_data"))
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
    await respond(update, text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def volatility(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await respond(update, get_text(lang, "volatility_usage"), parse_mode=ParseMode.MARKDOWN)
        return
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await respond(update, get_text(lang, "trend_no_data"))
        return
    atr_val = atr(df['High'], df['Low'], df['Close'], 14).iloc[-1]
    text = get_text(lang, "volatility_result", symbol=symbol, atr=format_number(atr_val))
    await respond(update, text, parse_mode=ParseMode.MARKDOWN)

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
        await update.message.reply_text(get_text(lang, "insufficient_data"))
        return
    common_idx = df1.index.intersection(df2.index)
    if len(common_idx) < 10:
        await update.message.reply_text(get_text(lang, "insufficient_common_data"))
        return
    ret1 = df1['Close'].pct_change().dropna()
    ret2 = df2['Close'].pct_change().dropna()
    corr = ret1.corr(ret2)
    await update.message.reply_text(get_text(lang, "correlation_result", symbol1=sym1, symbol2=sym2, corr=corr))

@check_limit
async def levels(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False):
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await respond(update, get_text(lang, "levels_usage"), parse_mode=ParseMode.MARKDOWN)
        return
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await respond(update, get_text(lang, "levels_no_data"))
        return
    from indicators import support_resistance, fibonacci_levels
    support, resistance = support_resistance(df['High'], df['Low'], 50)
    if support is None or resistance is None:
        await respond(update, get_text(lang, "levels_no_data"))
        return
    recent_high = df['High'].iloc[-50:].max()
    recent_low = df['Low'].iloc[-50:].min()
    fib = fibonacci_levels(recent_high, recent_low) if recent_high > recent_low else {"0.382": 0, "0.500": 0, "0.618": 0}
    text = get_text(lang, "levels_result", symbol=symbol,
                    support=format_number(support), resistance=format_number(resistance),
                    fib382=format_number(fib['0.382']), fib500=format_number(fib['0.500']), fib618=format_number(fib['0.618']))
    await respond(update, text, parse_mode=ParseMode.MARKDOWN)

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
        await update.message.reply_text(get_text(lang, "sentiment_error"))

@check_limit
async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if len(context.args) < 2:
        await update.message.reply_text(get_text(lang, "compare_usage"))
        return
    sym1, sym2 = context.args[0].upper(), context.args[1].upper()
    df1 = await fetcher.get_historical_data(sym1, period="2d")
    df2 = await fetcher.get_historical_data(sym2, period="2d")
    if df1 is None or df2 is None or len(df1) < 2 or len(df2) < 2:
        await update.message.reply_text(get_text(lang, "insufficient_data"))
        return
    res1 = SignalEngine.analyze(df1, lang, symbol=sym1)
    res2 = SignalEngine.analyze(df2, lang, symbol=sym2)
    trend1 = get_text(lang, f"trend_{res1['indicators']['trend'].lower()}")
    trend2 = get_text(lang, f"trend_{res2['indicators']['trend'].lower()}")
    text = get_text(lang, "compare_result", symbol1=sym1, symbol2=sym2, trend1=trend1, trend2=trend2)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
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
            await update.message.reply_text(get_text(lang, "fav_add_usage"))
            return
        symbol = context.args[1].upper()
        user_mgr.add_favorite(user_id, symbol)
        await update.message.reply_text(get_text(lang, "fav_added", symbol=symbol))
    elif action == "remove":
        if len(context.args) < 2:
            await update.message.reply_text(get_text(lang, "fav_remove_usage"))
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
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    if not context.args:
        await respond(update, get_text(lang, "settimeframe_usage"))
        return
    tf = context.args[0]
    if tf not in ("1h", "4h", "1d"):
        await respond(update, get_text(lang, "settimeframe_invalid"))
        return
    user_mgr.set_setting(update.effective_user.id, "timeframe", tf)
    await respond(update, get_text(lang, "settimeframe_success", tf=tf))

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

@check_limit
async def setlanguage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    if not context.args:
        await respond(update, get_text(lang, "setlanguage_usage"))
        return
    new_lang = context.args[0].lower()
    if new_lang not in ("en", "fr"):
        await respond(update, get_text(lang, "setlanguage_invalid"))
        return
    user_id = update.effective_user.id
    user_mgr.set_setting(user_id, "lang", new_lang)
    await respond(update, get_text(new_lang, f"setlanguage_success_{new_lang}"))

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
    if await handle_pending_alert_input(update, context):
        return
    lang = get_user_lang(update)
    symbol = context.args[0].upper() if context.args else None
    if not symbol:
        await respond(update, get_text(lang, "symbolinfo_usage"), parse_mode=ParseMode.MARKDOWN)
        return
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        text = get_text(lang, "symbolinfo_format",
                        symbol=symbol,
                        price=format_number(price_data['price']),
                        bid=format_number(price_data['bid']),
                        ask=format_number(price_data['ask']))
        await respond(update, text, parse_mode=ParseMode.MARKDOWN)
    else:
        await respond(update, get_text(lang, "symbol_not_found"))

@check_limit
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "myid", user_id=update.effective_user.id), parse_mode=ParseMode.MARKDOWN)

# ---------- BROADCAST / RELOAD / STATS ----------
@check_limit
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(get_text(lang, "broadcast_admin_only"))
        return
    if not context.args:
        await update.message.reply_text(get_text(lang, "broadcast_usage"))
        return
    message = "📢 *Bitsure Teddy Announcement*\n\n" + " ".join(context.args)
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

@check_limit
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

@check_limit
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(get_text(user_mgr.get_setting(update.effective_user.id, "lang", "en"), "broadcast_admin_only"))
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
    user_mgr._load_users()
    total = len(user_mgr.users)
    free = sum(1 for u in user_mgr.users.values() if u.get("role") == "free")
    pro = sum(1 for u in user_mgr.users.values() if u.get("role") == "pro")
    text = f"📊 Statistiques Bitsure Teddy\n👥 Utilisateurs : {total}\n🆓 Gratuits : {free}\n💎 PRO : {pro}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if len(context.args) < 2:
        await update.message.reply_text(get_text(lang, "check_usage"))
        return
    symbol = normalize_symbol(context.args[0].upper())
    side = context.args[1].upper()
    if side not in ("BUY", "SELL"):
        await update.message.reply_text(get_text(lang, "check_usage"))
        return
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await update.message.reply_text(get_text(lang, "data_unavailable"))
        return
    result = SignalEngine.analyze(df, lang, symbol=symbol)
    ind = result.get("indicators", {})
    trend = ind.get("trend", "NEUTRAL")
    trend_txt = get_text(lang, f"trend_{trend.lower()}") if isinstance(trend, str) else "N/A"
    score = int(result.get("teddy_score", 0))
    color = get_text(lang, "check_green") if score >= 80 else get_text(lang, "check_orange") if score >= 60 else get_text(lang, "check_red")
    atr_v = float(ind.get("atr") or 0)
    price_v = float(ind.get("price") or 1)
    vol_txt = get_text(lang, "check_vol_high") if price_v and (atr_v / price_v) > 0.03 else get_text(lang, "check_vol_normal")
    msg = get_text(
        lang, "check",
        symbol=symbol, trend=trend_txt, rsi=f"{float(ind.get('rsi') or 0):.1f}",
        volatility=vol_txt, score=score, light=color,
        sl=format_number(result.get('sl')) if result.get('sl') else "N/A",
        tp=format_number(result.get('tp')) if result.get('tp') else "N/A"
    )
    await update.message.reply_text(msg)

async def send_weekly_reports(bot):
    pro_users = [int(uid) for uid, u in user_mgr.users.items() if u.get("role") == "pro"]
    signals = history_mgr.get_recent_signals(50)
    completed = [s for s in signals if s.get("status") in ("win", "loss")]
    total = len(completed)
    wins = sum(1 for s in completed if s.get("status") == "win")
    win_rate = (wins / total * 100) if total else 0
    pcts = [float(s.get("result_pct") or 0) for s in completed]
    best = max(pcts) if pcts else 0
    worst = min(pcts) if pcts else 0
    msg = (
        "📊 RAPPORT HEBDOMADAIRE\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Signaux reçus : {len(signals)}\n"
        f"✅ Gagnés : {wins} ({win_rate:.0f}%)\n"
        f"📉 Meilleur : {best:+.1f}%\n"
        f"💸 Pire : {worst:+.1f}%\n"
        "💡 Conseil : attends un score > 70"
    )
    for uid in pro_users:
        try:
            await bot.send_message(chat_id=uid, text=msg)
        except Exception as e:
            logger.warning(f"Weekly report failed for {uid}: {e}")

def start_weekly_report_scheduler(app):
    global weekly_scheduler
    if weekly_scheduler is not None:
        return
    weekly_scheduler = AsyncIOScheduler(timezone="UTC")
    weekly_scheduler.add_job(
        send_weekly_reports,
        "cron",
        day_of_week="sun",
        hour=18,
        minute=0,
        kwargs={"context": app.bot},
        id="weekly_report_job",
        replace_existing=True,
    )
    weekly_scheduler.start()

@check_limit
async def symboles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "symboles_list"), parse_mode=ParseMode.MARKDOWN)

# ---------- CHALLENGE ----------
@check_limit
async def challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    user_id = update.effective_user.id

    challenge_mgr.reset_session(user_id)
    session = challenge_mgr.start_session(user_id, "EURUSD")
    await update.message.reply_text(get_text(lang, "challenge_start"), parse_mode=ParseMode.MARKDOWN)

    symbol = "EURUSD"
    wins = 0
    total_pips = 0

    for i in range(1, 6):
        df = await fetcher.get_historical_data(symbol, timeframe="1m")
        if df is None or df.empty:
            await update.message.reply_text(get_text(lang, "data_unavailable"))
            return

        result = SignalEngine.analyze(df, lang, symbol=symbol)
        signal_text = result['signal_text']
        price = result['indicators']['price']

        success = random.random() < 0.7
        pips = round(random.uniform(5, 15), 1) if success else -round(random.uniform(3, 10), 1)
        total_pips += pips
        if success:
            wins += 1
            trade_result = "✅ " + (get_text(lang, "win") if lang == "fr" else "WIN")
            result_str = "win"
        else:
            trade_result = "❌ " + (get_text(lang, "loss") if lang == "fr" else "LOSS")
            result_str = "loss"

        challenge_mgr.add_trade_result(user_id, {
            "trade_number": i,
            "symbol": symbol,
            "signal": result['signal'],
            "entry_price": price,
            "result": result_str,
            "pips": pips
        })

        msg = get_text(lang, "challenge_trade", n=i, signal=signal_text, price=format_number(price),
                       result=trade_result, pips=pips)
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(2)

    summary = f"{get_text(lang, 'net_pips')}: {'+' if total_pips > 0 else ''}{round(total_pips, 1)}"
    final_msg = get_text(lang, "challenge_score", wins=wins, summary=summary)
    await update.message.reply_text(final_msg, parse_mode=ParseMode.MARKDOWN)
    challenge_mgr.end_session(user_id)

# ---------- HISTORIQUE ----------
@check_limit
async def historique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    target_message = update.message if update.message else (update.callback_query.message if update.callback_query else None)
    if target_message is None:
        return
    signals = history_mgr.get_recent_signals(20)
    if not signals:
        await target_message.reply_text(get_text(lang, "history_empty"))
        return
    completed = [s for s in signals if s.get("status") in ("win", "loss")]
    wins = sum(1 for s in completed if s.get("status") == "win")
    losses = sum(1 for s in completed if s.get("status") == "loss")
    win_rate = (wins / len(completed) * 100) if completed else 0
    pcts = [float(s.get("result_pct") or 0) for s in completed]
    avg_gain = (sum(pcts) / len(pcts)) if pcts else 0
    worst = min(pcts) if pcts else 0
    best = max(pcts) if pcts else 0
    advice = get_text(lang, "history_advice_high") if win_rate >= 55 else get_text(lang, "history_advice_low")
    text = get_text(lang, "history_stats_header", total=len(signals), wins=wins, win_rate=f"{win_rate:.0f}", losses=losses, avg=f"{avg_gain:+.2f}", worst=f"{worst:+.1f}", best=f"{best:+.1f}", advice=advice)
    for s in signals:
        status = "✅" if s['status'] == 'win' else "❌" if s['status'] == 'loss' else "⏳"
        text += f"{status} {s['id']} {s['symbol']} {s['direction']} @ {format_number(s['entry_price'])} ({s['timestamp'][:10]})\n"
    await target_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def find_memo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /find_memo <memo>")
        return
    memo = context.args[0].upper()
    user_id = user_mgr.find_user_by_memo(memo)
    if user_id:
        await update.message.reply_text(f"✅ Mémo {memo} → User ID: {user_id}")
    else:
        await update.message.reply_text(f"❌ Aucun utilisateur trouvé pour le mémo {memo}")

# ---------- SNAPSHOT / VERIFY ----------
@check_limit
async def snapshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    signals = history_mgr.get_recent_signals(1)
    if not signals:
        await update.message.reply_text(get_text(lang, "no_recent_analysis"))
        return
    s = signals[0]
    symbol = s['symbol']
    df = await fetcher.get_historical_data(symbol)
    if df is None:
        await update.message.reply_text(get_text(lang, "data_unavailable"))
        return
    result = SignalEngine.analyze(df, lang, symbol=symbol)
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
    caption = get_text(lang, "snapshot_caption", symbol=symbol, signal=result['signal_text'], score=result['teddy_score'], price=format_number(ind['price']))
    await update.message.reply_photo(photo=buf, caption=caption, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "verify_usage"))
        return
    signal_id = context.args[0].upper()
    signal = history_mgr.get_signal_by_id(signal_id)
    if not signal:
        await update.message.reply_text(get_text(lang, "verify_not_found", signal_id=signal_id))
        return
    result_text = get_text(lang, "win") if signal['status'] == 'win' else get_text(lang, "loss") if signal['status'] == 'loss' else get_text(lang, "pending")
    msg = get_text(lang, "verify_result",
                   signal_id=signal_id,
                   timestamp=signal['timestamp'][:16],
                   symbol=signal['symbol'],
                   signal=signal['direction'],
                   price=format_number(signal['entry_price']),
                   result=result_text)
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
