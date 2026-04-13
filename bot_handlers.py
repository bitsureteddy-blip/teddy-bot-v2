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

logger = logging.getLogger(__name__)

# Initialisation des singletons
fetcher = DataFetcher.get_instance()
user_mgr = UserManager.get_instance()
alert_mgr = AlertManager.get_instance()

# --- Décorateur pour vérifier les limites ---
def check_limit(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not user_mgr.check_limit(user_id):
            await update.message.reply_text("❌ Vous avez atteint votre limite quotidienne de requêtes. Passez premium pour un accès illimité.")
            return
        user_mgr.increment_usage(user_id)
        return await func(update, context)
    return wrapper

# --- Décorateur pour les fonctionnalités premium ---
def premium_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not user_mgr.can_use_premium_feature(user_id):
            await update.message.reply_text(
                "🔒 *Fonctionnalité Premium*\n\n"
                "Cette commande est réservée aux membres PRO et ELITE.\n"
                "Utilisez /upgrade pour découvrir nos offres.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        return await func(update, context)
    return wrapper

# --- Fonction utilitaire pour notifier l'admin ---
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

# --- Commandes ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_mgr.get_user(user_id)
    role = user_mgr.get_role(user_id)
    
    if role == "free" and user_mgr.is_trial_valid(user_id):
        status = "🆓 Essai gratuit (3 jours)"
    elif role == "free":
        status = "🆓 Gratuit (essai terminé)"
    elif role == "pro":
        status = "💎 PRO"
    elif role == "elite":
        status = "👑 ELITE"
    else:
        status = role.upper()
    
    text = (
        f"🐻 *Bitsure Teddy* – Analyse de marché pro\n\n"
        f"Statut : {status}\n"
        f"Commandes : /help\n"
        f"Offres : /upgrade"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧸 Commandes disponibles :\n\n"
        "/analyse SYMBOLE – Analyse complète\n"
        "/price SYMBOLE – Prix actuel\n"
        "/scalp SYMBOLE DUREE – Scalping (Premium)\n"
        "/tick SYMBOLE – Dernier tick\n"
        "/spread SYMBOLE – Spread bid/ask\n"
        "/alert SYMBOLE above/below PRIX – Créer alerte\n"
        "/alerts – Lister alertes\n"
        "/delalert ID – Supprimer alerte\n"
        "/clearalerts – Tout supprimer\n"
        "/watchlist – Voir liste\n"
        "/addwatch SYMBOLE – Ajouter symbole\n"
        "/removewatch SYMBOLE – Retirer\n"
        "/scan – Scanner watchlist\n"
        "/trend SYMBOLE – Tendance\n"
        "/volatility SYMBOLE – Volatilité\n"
        "/correlation S1 S2 – Corrélation\n"
        "/levels SYMBOLE – Supports/Résistances\n"
        "/settings – Paramètres\n"
        "/settimeframe TF – 1h/4h/1d\n"
        "/setrisk PROFIL – low/medium/high\n"
        "/setlanguage LANG – en/fr\n"
        "/usage – Requêtes restantes\n"
        "/status – État du bot\n"
        "/about – Version\n"
        "/symbolinfo SYMBOLE – Infos\n"
        "/myid – Votre ID\n"
        "/upgrade – Offres Premium\n"
        "/support – Contacter admin\n"
        "/symboles – Symboles populaires"
    )
    if update.effective_user.id == ADMIN_ID:
        text += "\n\nAdmin : /broadcast, /reload, /stats, /setrole"
    await update.message.reply_text(text)  # Pas de parse_mode = pas de Markdown
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Besoin d'aide ?*\n\n"
        "Contactez l'administrateur : @btsr_teddy09",
        parse_mode=ParseMode.MARKDOWN
    )


async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 PRO – 29€/mois (Stars)", callback_data="plan_pro_stars")],
        [InlineKeyboardButton("👑 ELITE – 79€/mois (Stars)", callback_data="plan_elite_stars")],
        [InlineKeyboardButton("🚀 LIFETIME – 197€ (Stars)", callback_data="plan_lifetime")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "💳 *Choisissez votre offre :*\n\n"
        "• PRO : illimité, scalping\n"
        "• ELITE : PRO + groupe privé\n"
        "• LIFETIME : ELITE à vie (50 places)",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )


async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "plan_pro_stars":
        await send_invoice(query, "PRO Mensuel", 2900, "pro_monthly")
    elif data == "plan_elite_stars":
        await send_invoice(query, "ELITE Mensuel", 7900, "elite_monthly")
    elif data == "plan_lifetime":
        await send_invoice(query, "LIFETIME (accès à vie)", 19700, "lifetime")
    else:
        await query.edit_message_text("ℹ️ Paiement Stripe bientôt disponible.")


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
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    role = "pro" if "pro" in payload else "elite" if "elite" in payload else "pro"
    if "lifetime" in payload:
        role = "elite"
        user_mgr.increment_lifetime_count()
    user_mgr.set_role(user_id, role)
    await update.message.reply_text(
        f"✅ *Paiement réussi !*\n\n"
        f"Votre compte est maintenant *{role.upper()}*.\n"
        f"Merci de soutenir Bitsure Teddy ! 🧸💸",
        parse_mode=ParseMode.MARKDOWN
    )
    await notify_admin_new_premium(context, user, role, "Telegram Stars")


async def setrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Commande réservée à l'administrateur.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /setrole USER_ID ROLE (free/pro/elite)")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ USER_ID invalide.")
        return
    role = context.args[1].lower()
    if role not in ("free", "pro", "elite"):
        await update.message.reply_text("❌ Rôle invalide. Utilisez free, pro, ou elite.")
        return
    user_mgr.set_role(target_id, role)
    await update.message.reply_text(f"✅ Rôle de l'utilisateur {target_id} mis à jour : *{role.upper()}*", parse_mode=ParseMode.MARKDOWN)
    try:
        target_user = await context.bot.get_chat(target_id)
        await notify_admin_new_premium(context, target_user, role, "Manuel (admin)")
    except:
        pass


@check_limit
async def addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addwatch SYMBOLE")
        return
    symbol = context.args[0].upper()
    user_id = update.effective_user.id
    if not user_mgr.is_premium(user_id):
        current_wl = user_mgr.get_watchlist(user_id)
        if len(current_wl) >= 3:
            await update.message.reply_text(
                "❌ Vous avez atteint la limite de 3 symboles en mode gratuit.\n"
                "Passez Premium pour en ajouter plus : /upgrade"
            )
            return
    user_mgr.add_to_watchlist(user_id, symbol)
    await update.message.reply_text(f"✅ {symbol} ajouté à votre watchlist.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    total_users = len(user_mgr.users)
    free_users = sum(1 for u in user_mgr.users.values() if u.get("role") == "free")
    pro_users = sum(1 for u in user_mgr.users.values() if u.get("role") == "pro")
    elite_users = sum(1 for u in user_mgr.users.values() if u.get("role") == "elite")
    lifetime_count = user_mgr.get_lifetime_count()
    await update.message.reply_text(
        f"📊 *STATISTIQUES BITSURE TEDDY*\n"
        f"👥 Utilisateurs totaux : {total_users}\n"
        f"🆓 FREE : {free_users}\n"
        f"💪 PRO : {pro_users}\n"
        f"👑 ELITE : {elite_users}\n"
        f"🚀 LIFETIME vendus : {lifetime_count}/50",
        parse_mode=ParseMode.MARKDOWN
    )


@check_limit
async def symboles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "📊 *SYMBOLES POPULAIRES*\n\n"
        "🪙 *Cryptos*\n"
        "BTCUSD – Bitcoin\n"
        "ETHUSD – Ethereum\n"
        "XRPUSD – Ripple\n"
        "SOLUSD – Solana\n\n"
        "💱 *Forex*\n"
        "EURUSD – Euro/Dollar\n"
        "GBPUSD – Livre/Dollar\n"
        "USDJPY – Dollar/Yen\n\n"
        "✨ *Matières premières*\n"
        "XAUUSD – Or\n"
        "XAGUSD – Argent\n\n"
        "📈 *Actions*\n"
        "AAPL – Apple\n"
        "TSLA – Tesla\n"
        "MSFT – Microsoft\n\n"
        "💡 Exemple : /analyse BTCUSD"
    )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)


@check_limit
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /analyse SYMBOLE")
        return
    symbol = context.args[0]
    if not is_valid_symbol(symbol):
        await update.message.reply_text("Symbole invalide.")
        return
    symbol = normalize_symbol(symbol)

    msg = await update.message.reply_text(f"🔍 Analyse de {symbol} en cours...")

    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await msg.edit_text(f"❌ Impossible de récupérer les données pour {symbol}.")
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
    if not context.args:
        await update.message.reply_text("Usage: /price SYMBOLE")
        return
    symbol = context.args[0]
    if not is_valid_symbol(symbol):
        await update.message.reply_text("Symbole invalide.")
        return
    symbol = normalize_symbol(symbol)
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        await update.message.reply_text(
            f"*{symbol}*\n"
            f"💰 Prix: {format_number(price_data['price'])}\n"
            f"📊 Bid: {format_number(price_data['bid'])} / Ask: {format_number(price_data['ask'])}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text(f"❌ Prix non disponible pour {symbol}.")


@check_limit
@premium_required
async def scalp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ Fonctionnalité de scalping en cours de développement. (Premium)")


@check_limit
async def tick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /tick SYMBOLE")
        return
    symbol = context.args[0]
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        await update.message.reply_text(f"🕒 Dernier tick {symbol}: {format_number(price_data['price'])}")
    else:
        await update.message.reply_text("❌ Aucun tick récent.")


@check_limit
async def spread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /spread SYMBOLE")
        return
    symbol = context.args[0]
    price_data = await fetcher.get_realtime_price(symbol)
    if price_data:
        spread_val = price_data['ask'] - price_data['bid']
        await update.message.reply_text(
            f"*{symbol}* Spread: {format_number(spread_val, 5)}",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("❌ Spread non disponible.")


@check_limit
async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /alert SYMBOLE above/below PRIX")
        return
    symbol = context.args[0]
    cond = context.args[1].lower()
    try:
        price = float(context.args[2])
    except ValueError:
        await update.message.reply_text("Prix invalide.")
        return
    if cond not in ("above", "below"):
        await update.message.reply_text("Condition doit être 'above' ou 'below'.")
        return
    alert_id = alert_mgr.add_alert(update.effective_user.id, symbol, cond, price)
    await update.message.reply_text(f"✅ Alerte #{alert_id} créée : {symbol} {cond} {price}")


@check_limit
async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alerts_list = alert_mgr.get_alerts(update.effective_user.id)
    if not alerts_list:
        await update.message.reply_text("Aucune alerte active.")
        return
    text = "*Vos alertes :*\n"
    for a in alerts_list:
        status = "✅" if a.get("triggered") else "⏳"
        text += f"{status} #{a['id']} {a['symbol']} {a['condition']} {a['price']}\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@check_limit
async def delalert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delalert ID")
        return
    try:
        alert_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID invalide.")
        return
    if alert_mgr.delete_alert(update.effective_user.id, alert_id):
        await update.message.reply_text(f"✅ Alerte #{alert_id} supprimée.")
    else:
        await update.message.reply_text("❌ Alerte non trouvée.")


@check_limit
async def clearalerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alert_mgr.clear_alerts(update.effective_user.id)
    await update.message.reply_text("✅ Toutes vos alertes ont été supprimées.")


@check_limit
async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wl = user_mgr.get_watchlist(update.effective_user.id)
    if not wl:
        await update.message.reply_text("Votre watchlist est vide.")
        return
    await update.message.reply_text("📋 *Watchlist:*\n" + "\n".join(wl), parse_mode=ParseMode.MARKDOWN)


@check_limit
async def removewatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /removewatch SYMBOLE")
        return
    symbol = context.args[0].upper()
    user_mgr.remove_from_watchlist(update.effective_user.id, symbol)
    await update.message.reply_text(f"✅ {symbol} retiré de votre watchlist.")


@check_limit
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wl = user_mgr.get_watchlist(update.effective_user.id)
    if not wl:
        await update.message.reply_text("Watchlist vide.")
        return
    results = []
    for sym in wl:
        df = await fetcher.get_historical_data(sym)
        if df is not None and not df.empty:
            res = SignalEngine.analyze(df)
            results.append(f"{sym}: {res['signal']} (Score: {res['teddy_score']})")
        else:
            results.append(f"{sym}: données indisponibles")
    await update.message.reply_text("📊 *Scan watchlist:*\n" + "\n".join(results), parse_mode=ParseMode.MARKDOWN)


@check_limit
async def trend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /trend SYMBOLE")
        return
    symbol = context.args[0]
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await update.message.reply_text("Données non disponibles.")
        return
    sma20 = df['Close'].rolling(20).mean().iloc[-1]
    sma50 = df['Close'].rolling(50).mean().iloc[-1]
    price = df['Close'].iloc[-1]
    if price > sma20 > sma50:
        tend = "Haussière"
    elif price < sma20 < sma50:
        tend = "Baissière"
    else:
        tend = "Neutre"
    await update.message.reply_text(f"*{symbol}* Tendance: {tend}", parse_mode=ParseMode.MARKDOWN)


@check_limit
async def volatility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Calcul de la volatilité (ATR) en cours...")


@check_limit
async def correlation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Corrélation en développement.")


@check_limit
async def levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /levels SYMBOLE")
        return
    symbol = context.args[0]
    df = await fetcher.get_historical_data(symbol)
    if df is None or df.empty:
        await update.message.reply_text("Données non disponibles.")
        return
    from indicators import support_resistance
    support, resistance = support_resistance(df['High'], df['Low'], 50)
    await update.message.reply_text(
        f"*{symbol}* Niveaux:\nSupport: {format_number(support)}\nRésistance: {format_number(resistance)}",
        parse_mode=ParseMode.MARKDOWN
    )


@check_limit
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    tf = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
    risk = user_mgr.get_setting(uid, "risk", "medium")
    lang = user_mgr.get_setting(uid, "lang", "en")
    role = user_mgr.get_role(uid)
    prem = "✅" if role in ("pro", "elite") else "❌"
    await update.message.reply_text(
        f"⚙️ *Paramètres*\nTimeframe: {tf}\nRisque: {risk}\nLangue: {lang}\nRôle: {role.upper()}\nPremium: {prem}",
        parse_mode=ParseMode.MARKDOWN
    )


@check_limit
async def settimeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /settimeframe 1h|4h|1d")
        return
    tf = context.args[0]
    if tf not in ("1h", "4h", "1d"):
        await update.message.reply_text("Timeframe invalide.")
        return
    user_mgr.set_setting(update.effective_user.id, "timeframe", tf)
    await update.message.reply_text(f"✅ Timeframe par défaut: {tf}")


@check_limit
async def setrisk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setrisk low|medium|high")
        return
    risk = context.args[0].lower()
    if risk not in ("low", "medium", "high"):
        await update.message.reply_text("Risque invalide.")
        return
    user_mgr.set_setting(update.effective_user.id, "risk", risk)
    await update.message.reply_text(f"✅ Profil de risque: {risk}")


@check_limit
async def setlanguage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setlanguage en|fr")
        return
    lang = context.args[0].lower()
    if lang not in ("en", "fr"):
        await update.message.reply_text("Langue invalide.")
        return
    user_mgr.set_setting(update.effective_user.id, "lang", lang)
    await update.message.reply_text(f"✅ Langue: {lang}")


@check_limit
async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rem = user_mgr.get_remaining_requests(update.effective_user.id)
    if rem == -1:
        await update.message.reply_text("✅ Premium: requêtes illimitées.")
    else:
        await update.message.reply_text(f"📊 Requêtes restantes aujourd'hui: {rem}")


@check_limit
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot opérationnel. APIs: Twelve Data, Yahoo, RealMarket.")


@check_limit
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Teddy Trading Bot v1.0 – Bitsure Teddy\nDéveloppé pour trading professionnel.")


@check_limit
async def symbolinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Utilisez /analyse pour les infos détaillées.")


@check_limit
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Votre ID Telegram: `{update.effective_user.id}`", parse_mode=ParseMode.MARKDOWN)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Commande réservée à l'administrateur.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast MESSAGE")
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
    await update.message.reply_text(f"✅ Broadcast envoyé à {success}/{len(users)} utilisateurs.")


async def reload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    global user_mgr, alert_mgr
    user_mgr = UserManager.get_instance()
    alert_mgr = AlertManager.get_instance()
    await update.message.reply_text("✅ Configuration rechargée.")