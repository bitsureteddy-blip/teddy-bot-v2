import asyncio
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import io
import pandas as pd

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# --- Commandes ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐻 *Teddy Trading Bot* – Bitsure Teddy\n\n"
        "Analyse professionnelle crypto, forex, actions, matières premières.\n"
        "Commandes: /help",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*Commandes disponibles :*\n\n"
        "/analyse SYMBOLE – Analyse technique complète\n"
        "/price SYMBOLE – Prix temps réel\n"
        "/scalp SYMBOLE DURÉE – Micro‑analyse (3,5,10,20s)\n"
        "/tick SYMBOLE – Dernier tick\n"
        "/spread SYMBOLE – Spread bid/ask\n"
        "/alert SYMBOLE above/below PRIX – Créer une alerte\n"
        "/alerts – Lister vos alertes\n"
        "/delalert ID – Supprimer une alerte\n"
        "/clearalerts – Supprimer toutes les alertes\n"
        "/watchlist – Voir votre watchlist\n"
        "/addwatch SYMBOLE – Ajouter un symbole\n"
        "/removewatch SYMBOLE – Retirer un symbole\n"
        "/scan – Scanner votre watchlist\n"
        "/trend SYMBOLE – Tendance globale\n"
        "/volatility SYMBOLE – Volatilité (ATR)\n"
        "/correlation SYMBOLE1 SYMBOLE2 – Corrélation 30j\n"
        "/levels SYMBOLE – Supports/résistances\n"
        "/settings – Voir vos paramètres\n"
        "/settimeframe TF – 1h,4h,1d\n"
        "/setrisk PROFIL – low, medium, high\n"
        "/setlanguage LANG – en/fr\n"
        "/usage – Requêtes restantes\n"
        "/status – État du bot\n"
        "/about – Version et crédits\n"
        "/symbolinfo SYMBOLE – Infos symbole\n"
        "/myid – Obtenir votre ID Telegram"
    )
    if update.effective_user.id == ADMIN_ID:
        text += "\n\n*Admin:*\n/broadcast MESSAGE\n/reload\n/stats"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

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

    # Génération du graphique
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
async def scalp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Implémentation simplifiée : analyse rapide sur timeframe court (pas de données tick réelles)
    await update.message.reply_text("⚡ Fonctionnalité de scalping en cours de développement.")

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

# --- Alertes ---
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

# --- Watchlist ---
@check_limit
async def watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wl = user_mgr.get_watchlist(update.effective_user.id)
    if not wl:
        await update.message.reply_text("Votre watchlist est vide.")
        return
    await update.message.reply_text("📋 *Watchlist:*\n" + "\n".join(wl), parse_mode=ParseMode.MARKDOWN)

@check_limit
async def addwatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addwatch SYMBOLE")
        return
    symbol = context.args[0].upper()
    user_mgr.add_to_watchlist(update.effective_user.id, symbol)
    await update.message.reply_text(f"✅ {symbol} ajouté à votre watchlist.")

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

# --- Analyse avancée (implémentations simplifiées) ---
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

# --- Paramètres ---
@check_limit
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    tf = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
    risk = user_mgr.get_setting(uid, "risk", "medium")
    lang = user_mgr.get_setting(uid, "lang", "en")
    prem = "✅" if user_mgr.is_premium(uid) else "❌"
    await update.message.reply_text(
        f"⚙️ *Paramètres*\nTimeframe: {tf}\nRisque: {risk}\nLangue: {lang}\nPremium: {prem}",
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

# --- Infos & Admin ---
@check_limit
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot opérationnel. APIs: FCS, CoinGecko, Yahoo.")

@check_limit
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Teddy Trading Bot v1.0 – Bitsure Teddy\nDéveloppé pour trading professionnel.")

@check_limit
async def symbolinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Utilisez /analyse pour les infos détaillées.")

@check_limit
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Votre ID Telegram: `{update.effective_user.id}`", parse_mode=ParseMode.MARKDOWN)

# Admin only
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
    # Recharger les configurations (singletons)
    global user_mgr, alert_mgr
    user_mgr = UserManager.get_instance()
    alert_mgr = AlertManager.get_instance()
    await update.message.reply_text("✅ Configuration rechargée.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    total_users = len(user_mgr.users)
    premium_users = sum(1 for u in user_mgr.users.values() if u.get("premium"))
    await update.message.reply_text(f"📊 Statistiques:\nUtilisateurs: {total_users}\nPremium: {premium_users}")