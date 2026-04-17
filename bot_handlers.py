import asyncio
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import io
import pandas as pd
import random
import hashlib
import time
from typing import Dict, Optional, List   # <-- AJOUTE CETTE LIGNE

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
from history_manager import HistoryManager
from challenge_manager import ChallengeManager

logger = logging.getLogger(__name__)

fetcher = DataFetcher.get_instance()
user_mgr = UserManager.get_instance()
alert_mgr = AlertManager.get_instance()
history_mgr = HistoryManager.get_instance()
challenge_mgr = ChallengeManager.get_instance()

# ------------------- DÉCORATEUR DE LIMITE -------------------
def check_limit(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        lang = user_mgr.get_user_lang(user_id)
        if not user_mgr.check_limit(user_id):
            await update.message.reply_text(get_text(lang, "limit_exceeded"))
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def get_user_lang(update: Update) -> str:
    user_id = update.effective_user.id
    return user_mgr.get_user_lang(user_id)

# ------------------- COMMANDES DE BASE -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_mgr.register_user(user_id)
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "welcome"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "help_full"), parse_mode=ParseMode.MARKDOWN)

@check_limit
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "analyse_usage"))
        return
    symbol = normalize_symbol(context.args[0])
    if not is_valid_symbol(symbol):
        await update.message.reply_text(get_text(lang, "invalid_symbol"))
        return
    timeframe = context.args[1] if len(context.args) > 1 else DEFAULT_TIMEFRAME
    msg = await update.message.reply_text(get_text(lang, "analyse_wait").format(symbol=symbol))
    try:
        df = fetcher.get_historical_data(symbol, timeframe, limit=100)
        if df is None or df.empty:
            await msg.edit_text(get_text(lang, "data_error"))
            return
        current_price = df['close'].iloc[-1]
        engine = SignalEngine(df, timeframe)
        signal = engine.analyze()
        response = format_signal_message(signal, symbol, current_price, timeframe, lang)
        # Enregistrer dans l'historique si signal d'achat/vente
        action = signal.get("action", "").upper()
        if action in ["ACHETER", "BUY", "VENDRE", "SELL"]:
            direction = "BUY" if action in ["ACHETER", "BUY"] else "SELL"
            signal_id = history_mgr.add_signal(symbol, direction, current_price, timeframe, "analyse")
            response += f"\n\n🆔 Signal ID: `{signal_id}`"
        await msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(get_text(lang, "error").format(error=str(e)))

def format_signal_message(signal, symbol, price, timeframe, lang):
    action = signal.get("action", "ATTENDRE")
    score = signal.get("score", 50)
    reasons = signal.get("reasons", [])
    emoji = "🟢" if action in ["ACHETER", "BUY"] else "🔴" if action in ["VENDRE", "SELL"] else "🟡"
    lines = [
        f"{emoji} *{symbol}* – {action}",
        f"💰 Prix: {price}",
        f"⏱ Timeframe: {timeframe}",
        f"📊 Teddy Score: {score}/100",
        "",
        "*Raisons:*"
    ]
    for r in reasons:
        lines.append(f"• {r}")
    return "\n".join(lines)

@check_limit
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "price_usage"))
        return
    symbol = normalize_symbol(context.args[0])
    p = fetcher.get_current_price(symbol)
    if p is None:
        await update.message.reply_text(get_text(lang, "price_error"))
        return
    await update.message.reply_text(f"💰 {symbol}: {p}")

# ------------------- COMMANDES PREMIUM -------------------
@check_limit
async def scalp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(update)
    if not user_mgr.is_premium(user_id):
        await update.message.reply_text(get_text(lang, "premium_required"))
        return
    # ... (code existant, à conserver)
    # Pense à enregistrer le signal dans history_mgr comme pour /analyse
    pass

@check_limit
async def tick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def spread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

# ------------------- ALERTES -------------------
@check_limit
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def delalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def clearalerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

# ------------------- WATCHLIST -------------------
@check_limit
async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def removewatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

# ------------------- ANALYSES COMPLÉMENTAIRES -------------------
@check_limit
async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def volatility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def correlation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

# ------------------- PARAMÈTRES UTILISATEUR -------------------
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

async def settimeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

async def setrisk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

async def setlanguage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def symbolinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Votre ID: {update.effective_user.id}")

# ------------------- PREMIUM & SUPPORT -------------------
@check_limit
async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les offres PRO et ELITE."""
    lang = get_user_lang(update)
    user_id = update.effective_user.id
    user = user_mgr.get_user(user_id)
    role = user.get("role", "FREE")
    if role == "FREE":
        status_text = get_text(lang, "upgrade_free_status")
    elif role == "PRO":
        status_text = get_text(lang, "upgrade_pro_status")
    else:
        status_text = get_text(lang, "upgrade_elite_status")
    text = f"{get_text(lang, 'upgrade_message')}\n\n{status_text}"
    keyboard = []
    if role == "FREE":
        keyboard.append([InlineKeyboardButton(get_text(lang, "upgrade_btn_pro_stripe"), callback_data="upgrade_stripe_pro")])
        keyboard.append([InlineKeyboardButton(get_text(lang, "upgrade_btn_pro_stars"), url="https://t.me/BitsureTeddyBot?start=stars_pro")])
        keyboard.append([InlineKeyboardButton(get_text(lang, "upgrade_btn_elite_stripe"), callback_data="upgrade_stripe_elite")])
    elif role == "PRO":
        keyboard.append([InlineKeyboardButton(get_text(lang, "upgrade_btn_elite_stripe"), callback_data="upgrade_stripe_elite")])
        keyboard.append([InlineKeyboardButton(get_text(lang, "upgrade_btn_elite_stars"), url="https://t.me/BitsureTeddyBot?start=stars_elite")])
    else:
        keyboard.append([InlineKeyboardButton(get_text(lang, "upgrade_already_elite"), callback_data="noop")])
    keyboard.append([InlineKeyboardButton(get_text(lang, "support_contact"), url="https://t.me/bitsure_support")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    await update.message.reply_text(get_text(lang, "support_message"))

@check_limit
async def symboles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass
async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Validation de la pré-facture pour les paiements Telegram Stars."""
    query = update.pre_checkout_query
    # Toujours accepter (on peut ajouter des vérifications plus tard)
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Traitement après un paiement réussi."""
    user_id = update.effective_user.id
    lang = get_user_lang(update)
    # Récupérer les infos du paiement
    payment = update.message.successful_payment
    # Mettre à jour le rôle de l'utilisateur selon le produit acheté
    # Exemple simplifié : on active PRO pour 30 jours
    user_mgr.set_role(user_id, "PRO", 30)
    await update.message.reply_text(get_text(lang, "payment_success"))

# ------------------- NOUVELLES COMMANDES -------------------
@check_limit
async def challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Défi scalping interactif."""
    user_id = update.effective_user.id
    lang = get_user_lang(update)
    args = context.args
    if args and args[0].lower() == "top":
        await show_challenge_top(update, lang)
        return
    session = challenge_mgr.get_session(user_id)
    if session and session.get("active"):
        await update.message.reply_text(
            get_text(lang, "challenge_already_active"),
            reply_markup=get_challenge_keyboard(lang, session)
        )
        return
    symbol = args[0].upper() if args else "EURUSD"
    if not is_valid_symbol(symbol):
        symbol = "EURUSD"
    session = challenge_mgr.start_session(user_id, symbol)
    text = get_text(lang, "challenge_intro").format(symbol=symbol)
    keyboard = [[InlineKeyboardButton(get_text(lang, "challenge_start_btn"), callback_data="challenge_start")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def get_challenge_keyboard(lang: str, session: Dict = None):
    if session and session.get("active"):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(get_text(lang, "challenge_continue"), callback_data="challenge_continue")],
            [InlineKeyboardButton(get_text(lang, "challenge_cancel"), callback_data="challenge_cancel")]
        ])
    return None

async def show_challenge_top(update: Update, lang: str):
    top_users = user_mgr.get_top_challenge_scores(5)
    if not top_users:
        await update.message.reply_text(get_text(lang, "challenge_no_scores"))
        return
    lines = [get_text(lang, "challenge_top_header")]
    for i, (uid, score) in enumerate(top_users, 1):
        winrate = (score['wins']/score['total']*100) if score['total']>0 else 0
        lines.append(f"{i}. User {uid}: {score['wins']}/{score['total']} ({winrate:.1f}%)")
    await update.message.reply_text("\n".join(lines))

async def send_next_trade(message, user_id, session, lang):
    trade_num = session["current_trade"]
    symbol = session["symbol"]
    price = fetcher.get_current_price(symbol)
    if price is None:
        await message.reply_text(get_text(lang, "price_error"))
        return
    action = "BUY" if random.random() > 0.5 else "SELL"
    action_text = "📈 ACHETER" if action == "BUY" else "📉 VENDRE"
    text = get_text(lang, "challenge_trade_prompt").format(
        num=trade_num, total=5, symbol=symbol, price=price, action=action_text
    )
    keyboard = [[
        InlineKeyboardButton(get_text(lang, "challenge_follow"), callback_data=f"challenge_action_follow_{action}_{price}"),
        InlineKeyboardButton(get_text(lang, "challenge_skip"), callback_data="challenge_action_skip")
    ]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

async def handle_challenge_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = get_user_lang(update)
    data = query.data
    session = challenge_mgr.get_session(user_id)
    if not session or not session["active"]:
        await query.edit_message_text(get_text(lang, "challenge_expired"))
        return
    symbol = session["symbol"]
    if data == "challenge_action_skip":
        challenge_mgr.add_trade_result(user_id, {"result": "skipped"})
        await query.edit_message_text(get_text(lang, "challenge_trade_skipped"))
        session = challenge_mgr.get_session(user_id)
        if session["current_trade"] > 5:
            await finish_challenge(query.message, user_id, lang)
        else:
            await send_next_trade(query.message, user_id, session, lang)
        return
    parts = data.split("_")
    action = parts[3]
    entry_price = float(parts[4])
    await asyncio.sleep(3)
    new_price = fetcher.get_current_price(symbol)
    if new_price is None:
        await query.edit_message_text(get_text(lang, "price_error"))
        return
    win = (new_price > entry_price) if action == "BUY" else (new_price < entry_price)
    result = "win" if win else "loss"
    result_text = f"+{((new_price-entry_price)/entry_price)*100:.2f}%" if win else f"{((new_price-entry_price)/entry_price)*100:.2f}%"
    challenge_mgr.add_trade_result(user_id, {
        "symbol": symbol, "action": action, "entry": entry_price, "exit": new_price,
        "result": result, "pct": result_text
    })
    await query.edit_message_text(get_text(lang, "challenge_trade_result").format(result=result_text, status="✅ GAGNÉ" if win else "❌ PERDU"))
    session = challenge_mgr.get_session(user_id)
    if session["current_trade"] > 5:
        await finish_challenge(query.message, user_id, lang)
    else:
        await asyncio.sleep(2)
        await send_next_trade(query.message, user_id, session, lang)

async def finish_challenge(message, user_id, lang):
    session = challenge_mgr.get_session(user_id)
    score = session["score"]
    total = len([t for t in session["trades"] if t.get("result") in ("win","loss")])
    win_rate = (score["win"] / total * 100) if total > 0 else 0
    text = get_text(lang, "challenge_finished").format(
        win=score["win"], loss=score["loss"], total=total, rate=win_rate
    )
    user_mgr.update_challenge_score(user_id, score["win"], total)
    challenge_mgr.end_session(user_id)
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def handle_challenge_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = get_user_lang(update)
    challenge_mgr.end_session(user_id)
    await query.edit_message_text(get_text(lang, "challenge_cancelled"))

@check_limit
async def snapshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant (génération d'image)
    pass

@check_limit
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    if not context.args:
        await update.message.reply_text(get_text(lang, "verify_usage"))
        return
    signal_id = context.args[0]
    signal = history_mgr.get_signal_by_id(signal_id)
    if not signal:
        await update.message.reply_text(get_text(lang, "verify_not_found"))
        return
    # Construire message de vérification
    status = signal["status"]
    if status == "pending":
        status_text = get_text(lang, "history_pending")
    elif status == "win":
        status_text = f"✅ +{signal['result_pct']}%"
    else:
        status_text = f"❌ {signal['result_pct']}%"
    text = get_text(lang, "verify_message").format(
        id=signal["id"],
        symbol=signal["symbol"],
        direction="ACHAT" if signal["direction"]=="BUY" else "VENTE",
        entry=signal["entry_price"],
        timeframe=signal["timeframe"],
        date=signal["timestamp"][:10],
        status=status_text
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@check_limit
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Code existant
    pass

@check_limit
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import GEMINI_API_KEY
    lang = get_user_lang(update)
    if not GEMINI_API_KEY:
        await update.message.reply_text("❌ L'IA n'est pas configurée.")
        return
    if not context.args:
        await update.message.reply_text(get_text(lang, "ask_usage"))
        return
    question = " ".join(context.args)
    msg = await update.message.reply_text(get_text(lang, "ask_thinking"))
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        models_to_try = ["gemini-1.5-flash", "gemini-pro"]
        response = None
        last_error = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(question)
                break
            except Exception as e:
                last_error = e
                if "429" in str(e):
                    continue
                else:
                    raise e
        if response is None:
            raise last_error
        reply = response.text
        await msg.edit_text(reply)
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
            reply = get_text(lang, "ask_quota_exceeded")
        else:
            reply = get_text(lang, "ask_error", error=error_str)
        await msg.edit_text(reply)

@check_limit
async def historique(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update)
    history_mgr.check_and_update_pending(fetcher)
    signals = history_mgr.get_recent_signals(5)
    if not signals:
        await update.message.reply_text(get_text(lang, "history_empty"))
        return
    lines = [get_text(lang, "history_header")]
    for s in signals:
        dir_text = "📈 ACHAT" if s["direction"] == "BUY" else "📉 VENTE"
        if s["status"] == "pending":
            status_emoji = "⏳"
            result_text = get_text(lang, "history_pending")
        elif s["status"] == "win":
            status_emoji = "✅"
            result_text = f"+{s['result_pct']}%"
        else:
            status_emoji = "❌"
            result_text = f"{s['result_pct']}%"
        date_str = datetime.fromisoformat(s["timestamp"]).strftime("%d/%m %H:%M")
        line = (
            f"{status_emoji} {s['symbol']} {dir_text} @ {s['entry_price']} ({s['timeframe']})\n"
            f"   {result_text}  |  🆔 `{s['id']}`  |  {date_str}"
        )
        lines.append(line)
    text = "\n\n".join(lines)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ------------------- CALLBACK QUERY HANDLER -------------------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "challenge_start":
        user_id = query.from_user.id
        lang = get_user_lang(update)
        session = challenge_mgr.get_session(user_id)
        if session and session.get("active"):
            await send_next_trade(query.message, user_id, session, lang)
    elif data == "challenge_continue":
        user_id = query.from_user.id
        lang = get_user_lang(update)
        session = challenge_mgr.get_session(user_id)
        if session and session.get("active"):
            await send_next_trade(query.message, user_id, session, lang)
        else:
            await query.edit_message_text(get_text(lang, "challenge_expired"))
    elif data == "challenge_cancel":
        await handle_challenge_cancel(update, context)
    elif data.startswith("challenge_action_"):
        await handle_challenge_action(update, context)
    # ... autres callbacks (upgrade, settings, etc.) à conserver
# ------------------- COMMANDES ADMIN -------------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envoie un message à tous les utilisateurs (admin uniquement)."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès réservé à l'administrateur.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    users = user_mgr.get_all_users()
    success = 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *Message de l'admin :*\n\n{message}", parse_mode=ParseMode.MARKDOWN)
            success += 1
            await asyncio.sleep(0.05)  # Éviter les limites Telegram
        except Exception as e:
            logger.warning(f"Broadcast failed for {uid}: {e}")
    await update.message.reply_text(f"✅ Broadcast envoyé à {success}/{len(users)} utilisateurs.")

async def reload_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recharge la configuration (admin uniquement)."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès réservé à l'administrateur.")
        return
    # Recharger les modules si nécessaire
    await update.message.reply_text("✅ Configuration rechargée.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les statistiques du bot (admin uniquement)."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès réservé à l'administrateur.")
        return
    stats = user_mgr.get_stats()
    lang = get_user_lang(update)
    text = get_text(lang, "stats_info").format(
        total=stats['total'], free=stats['free'], pro=stats['pro'], elite=stats['elite']
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def setrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès réservé à l'administrateur.")
        return
    # Code existant pour /setrole (à conserver si présent)
    pass

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès réservé à l'administrateur.")
        return
    # Code existant pour /gift
    pass

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Accès réservé à l'administrateur.")
        return
    # Code existant pour /revoke
    pass