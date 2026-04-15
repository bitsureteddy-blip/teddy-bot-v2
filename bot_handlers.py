import asyncio
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import io
import pandas as pd

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import ADMIN_ID, DEFAULT_TIMEFRAME
from data_fetcher import DataFetcher
from signal_engine import SignalEngine
from user_manager import UserManager
from alert_manager import AlertManager
from utils import format_number, is_valid_symbol, normalize_symbol
from i18n import get_text

logger = logging.getLogger(__name__)

fetcher = DataFetcher.get_instance()
user_mgr = UserManager.get_instance()
alert_mgr = AlertManager.get_instance()


def ensure_twelvedata_ws(user_id: int):
    if user_mgr.can_use_premium_feature(user_id):
        fetcher.start_twelvedata_websocket()


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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    tg_lang = user.language_code
    default_lang = "en" if tg_lang and tg_lang.startswith("en") else "fr"

    current_lang = user_mgr.get_setting(user_id, "lang", None)
    if current_lang is None:
        user_mgr.set_setting(user_id, "lang", default_lang)
        lang = default_lang
    else:
        lang = current_lang

    # Détection nouvel utilisateur AVANT création
    was_new = str(user_id) not in user_mgr.users

    # Création ou récupération de l'utilisateur
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
    elif role == "elite":
        status = get_text(lang, "status_elite")
    else:
        status = role.upper()

    welcome = get_text(lang, "start", status=status)
    disclaimer = get_text(lang, "start_disclaimer")

    if role == "free":
        payment_info = get_text(lang, "international_payment_info")
    else:
        payment_info = ""

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


async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    keyboard = [
        [InlineKeyboardButton(get_text(lang, "button_pro_stars"), callback_data="plan_pro_stars")],
        [InlineKeyboardButton(get_text(lang, "button_elite_stars"), callback_data="plan_elite_stars")],
        [InlineKeyboardButton(get_text(lang, "button_pro_stripe"), callback_data="plan_pro_stripe")],
        [InlineKeyboardButton(get_text(lang, "button_elite_stripe"), callback_data="plan_elite_stripe")],
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
        await send_invoice(query, "PRO Mensuel", 1599, "pro_monthly")
    elif data == "plan_elite_stars":
        await send_invoice(query, "ELITE Mensuel", 3999, "elite_monthly")
    else:
        await query.edit_message_text(get_text(lang, "stripe_soon"))

async def send_invoice(query, title: str, price_eur: int, payload: str):
    prices = [LabeledPrice(label=title, amount=price_eur)]
    await query.message.reply_invoice(
        title="Bitsure Teddy Premium",
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
    role = "pro" if "pro" in payload else "elite" if "elite" in payload else "pro"
    user_mgr.set_role(user_id, role)
    lang = user_mgr.get_setting(user_id, "lang", "en")
    await update.message.reply_text(
        get_text(lang, "payment_success", role=role.upper()),
        parse_mode=ParseMode.MARKDOWN
    )
    await notify_admin_new_premium(context, user, role, "Telegram Stars")


# --- Commandes Admin ---
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
    if role not in ("pro", "elite"):
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
    if len(context.args) < 1:
        await update.message.reply_text(get_text(lang, "revoke_usage"))
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(get_text(lang, "setrole_invalid_id"))
        return
    user_mgr.set_role(target_id, "free")
    await update.message.reply_text(get_text(lang, "revoke_success", target_id=target_id))


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
    if role not in ("free", "pro", "elite"):
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


@check_limit
async def addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text("Usage: /addwatch SYMBOLE")
        return
    symbol = context.args[0].upper()
    user_id = update.effective_user.id
    if not user_mgr.is_premium(user_id):
        current_wl = user_mgr.get_watchlist(user_id)
        if len(current_wl) >= 3:
            await update.message.reply_text(get_text(lang, "watchlist_limit"))
            return
    user_mgr.add_to_watchlist(user_id, symbol)
    await update.message.reply_text(get_text(lang, "watchlist_added", symbol=symbol))


@check_limit
async def removewatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text("Usage: /removewatch SYMBOLE")
        return
    symbol = context.args[0].upper()
    user_mgr.remove_from_watchlist(update.effective_user.id, symbol)
    await update.message.reply_text(get_text(lang, "watchlist_removed", symbol=symbol))


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
            res = SignalEngine.analyze(df)
            results.append(f"{sym}: {res['signal']} (Score: {res['teddy_score']})")
        else:
            results.append(f"{sym}: données indisponibles")
    await update.message.reply_text(
        get_text(lang, "watchlist_scan_result", results="\n".join(results)),
        parse_mode=ParseMode.MARKDOWN
    )


@check_limit
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "analyse_usage"))
        return
    symbol = context.args[0]
    if not is_valid_symbol(symbol):
        await update.message.reply_text(get_text(lang, "symbole_invalide"))
        return
    symbol = normalize_symbol(symbol)
    msg = await update.message.reply_text(get_text(lang, "analyse_wait", symbol=symbol))
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await msg.edit_text(get_text(lang, "analyse_error", symbol=symbol))
        return
    result = SignalEngine.analyze(df)
    ind = result['indicators']
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df.index, df['Close'], color='white', linewidth=1, label='Prix')
    ax.plot(df.index, ind['sma20'] * pd.Series(1, index=df.index) if ind['sma20'] else None, color='orange', linestyle='--', label='SMA20')
    ax.plot(df.index, ind['sma50'] * pd.Series(1, index=df.index) if ind['sma50'] else None, color='cyan', linestyle='--', label='SMA50')
    ax.fill_between(df.index, ind['bb_lower'], ind['bb_upper'], alpha=0.1, color='gray')
    ax.set_title(f"{symbol} – Teddy Score: {result['teddy_score']}/100", color='white')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    caption = (
        f"*{symbol}* – Signal: *{result['signal']}*\n"
        f"{result['reason']}\n"
        f"{result['risk_advice']}\n\n"
        f"💰 Prix: {format_number(ind['price'])}\n"
        f"📊 RSI: {ind['rsi']:.2f}\n"
        f"📈 SMA20: {format_number(ind['sma20'])}, SMA50: {format_number(ind['sma50'])}\n"
        f"🧸 Teddy Score: {result['teddy_score']}/100"
    )
    await msg.delete()
    await update.message.reply_photo(photo=buf, caption=caption, parse_mode=ParseMode.MARKDOWN)


@check_limit
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "price_usage"))
        return
    symbol = context.args[0]
    if not is_valid_symbol(symbol):
        await update.message.reply_text(get_text(lang, "symbole_invalide"))
        return
    symbol = normalize_symbol(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        await update.message.reply_text(
            get_text(lang, "price_format",
                     symbol=symbol,
                     price=format_number(price_data['price']),
                     bid=format_number(price_data['bid']),
                     ask=format_number(price_data['ask'])),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(get_text(lang, "price_error", symbol=symbol))


@check_limit
@premium_required
async def tick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "tick_usage"))
        return
    symbol = context.args[0].upper()
    ensure_twelvedata_ws(update.effective_user.id)
    fetcher.subscribe_twelvedata(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        await update.message.reply_text(
            get_text(lang, "tick_current", symbol=symbol, price=format_number(price_data['price']))
        )
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

    ensure_twelvedata_ws(update.effective_user.id)
    fetcher.subscribe_twelvedata(symbol)

    # Récupérer les derniers ticks via WebSocket ou fallback REST
    price_data = await fetcher.get_realtime_price(symbol)
    if not price_data:
        await update.message.reply_text("❌ Impossible d'obtenir les données temps réel.")
        return

    # Analyse micro (calcul de volatilité instantanée simulée)
    price = price_data['price']
    bid = price_data['bid']
    ask = price_data['ask']
    spread = ask - bid

    # Volatilité estimée (spread relatif en %)
    volatility = (spread / price) * 100 if price > 0 else 0

    # Logique de scalping simple : si spread serré, suivre la tendance du tick précédent (simulé)
    # Pour une vraie analyse, il faudrait un historique de ticks
    signal_key = "scalp_signal_wait"
    reason = ""
    if volatility < 0.05:   # marché calme, suivre micro-tendance
        # simulation : si bid > dernier prix (fictif), acheter
        # en l'absence d'historique, on génère un signal neutre
        signal_key = "scalp_signal_wait"
        reason = "Volatilité très faible, attendez un mouvement."
    elif volatility < 0.2:
        signal_key = "scalp_signal_buy" if bid > ask * 0.999 else "scalp_signal_sell"
        reason = "Scalping sur micro-spread."
    else:
        signal_key = "scalp_signal_wait"
        reason = "Volatilité élevée, risque important."

    signal_text = get_text(lang, signal_key)

    await update.message.reply_text(
        get_text(lang, "scalp_result",
                 symbol=symbol,
                 duration=duration,
                 signal=signal_text,
                 price=format_number(price),
                 bid=format_number(bid),
                 ask=format_number(ask),
                 volatility=round(volatility, 4),
                 reason=reason),
        parse_mode=ParseMode.MARKDOWN
    )


@check_limit
@premium_required
async def spread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "spread_usage"))
        return
    symbol = context.args[0].upper()
    ensure_twelvedata_ws(update.effective_user.id)
    fetcher.subscribe_twelvedata(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        spread_val = price_data['ask'] - price_data['bid']
        await update.message.reply_text(
            get_text(lang, "spread_format", symbol=symbol, spread=format_number(spread_val, 5)),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(get_text(lang, "spread_unavailable"))


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
    alert_mgr.clear_alerts(update.effective_user.id)
    await update.message.reply_text(get_text(lang, "alerts_cleared"))


@check_limit
async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "trend_usage"))
        return
    symbol = context.args[0]
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
    await update.message.reply_text(
        get_text(lang, "trend_result", symbol=symbol, tend=tend),
        parse_mode=ParseMode.MARKDOWN
    )


@check_limit
async def volatility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "volatility_wip"))


@check_limit
async def correlation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "correlation_wip"))


@check_limit
async def levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "levels_usage"))
        return
    symbol = context.args[0]
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await update.message.reply_text(get_text(lang, "levels_no_data"))
        return
    from indicators import support_resistance
    support, resistance = support_resistance(df['High'], df['Low'], 50)
    await update.message.reply_text(
        get_text(lang, "levels_result", symbol=symbol, support=format_number(support), resistance=format_number(resistance)),
        parse_mode=ParseMode.MARKDOWN
    )


@check_limit
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_mgr.get_setting(uid, "lang", "en")
    tf = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
    risk = user_mgr.get_setting(uid, "risk", "medium")
    role = user_mgr.get_role(uid)
    prem = "✅" if role in ("pro", "elite") else "❌"
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
async def symbolinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "symbolinfo"))


@check_limit
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(
        get_text(lang, "myid", user_id=update.effective_user.id),
        parse_mode=ParseMode.MARKDOWN
    )


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
    global user_mgr, alert_mgr
    user_mgr = UserManager.get_instance()
    alert_mgr = AlertManager.get_instance()
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
    elite = sum(1 for u in user_mgr.users.values() if u.get("role") == "elite")
    text = get_text(lang, "stats_info", total=total, free=free, pro=pro, elite=elite)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@check_limit
async def symboles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "symboles_list"), parse_mode=ParseMode.MARKDOWN)