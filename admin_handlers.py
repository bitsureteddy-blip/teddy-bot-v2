"""
Bitsure Teddy - Admin Handlers
Fonctions réservées à l'administrateur
"""

import logging
import requests
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import ADMIN_ID
from data_fetcher import DataFetcher
from user_manager import UserManager
from alert_manager import AlertManager
from history_manager import HistoryManager
from i18n import get_text

logger = logging.getLogger(__name__)
user_mgr = UserManager.get_instance()
history_mgr = HistoryManager.get_instance()

def get_user_lang(update: Update) -> str:
    user_id = update.effective_user.id
    return user_mgr.get_setting(user_id, "lang", "en")

def check_limit(func):
    """Version simplifiée pour admin - l'admin passe toujours"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        return await func(update, context, *args, **kwargs)
    return wrapper

# =========================================================
# STATS
# =========================================================

@check_limit
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
    total_row = user_mgr.conn.execute("SELECT COUNT(*) as total FROM users").fetchone()
    total = total_row["total"] if total_row else 0
    free_row = user_mgr.conn.execute("SELECT COUNT(*) as c FROM users WHERE role='tester'").fetchone()
    free = free_row["c"] if free_row else 0
    pro_row = user_mgr.conn.execute("SELECT COUNT(*) as c FROM users WHERE role='pro'").fetchone()
    pro = pro_row["c"] if pro_row else 0
    text = f"📊 Statistiques Bitsure Teddy\n👥 Utilisateurs : {total}\n🧪 Testeurs : {free}\n💎 PRO : {pro}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# =========================================================
# APPROUVER UN TESTEUR
# =========================================================

@check_limit
async def teddy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /teddy <user_id>")
        return
    uid = int(context.args[0])
    if user_mgr.confirm_binance_payment(uid):
        await update.message.reply_text(f"✅ Paiement confirmé pour {uid}")
    elif user_mgr.approve_user(uid):
        await update.message.reply_text(f"✅ Utilisateur {uid} approuvé comme testeur")
    else:
        await update.message.reply_text(f"❌ Utilisateur {uid} introuvable")

# =========================================================
# BROADCAST
# =========================================================

@check_limit
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
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

# =========================================================
# SWITCH API
# =========================================================

@check_limit
async def switchapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
    fetcher = DataFetcher.get_instance()
    current = fetcher.active_source or "none"
    if not context.args:
        await update.message.reply_text(
            f"🔄 Source actuelle : {current}\n"
            f"Usage : /switchapi twelve|fcs|real\n"
            f"Échecs : {fetcher.source_failures}"
        )
        return
    target = context.args[0].lower()
    if target not in ("twelve", "fcs", "real"):
        await update.message.reply_text("❌ twelve, fcs ou real")
        return
    if fetcher.ws:
        fetcher.ws.close()
    if target == "twelve":
        fetcher._start_twelve_ws()
    elif target == "fcs":
        fetcher._start_fcs_ws()
    elif target == "real":
        fetcher._start_real_ws()
    await update.message.reply_text(f"✅ Switch vers {target} effectué.")

# =========================================================
# FIND MEMO
# =========================================================

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

# =========================================================
# CONFIRM PAYMENT
# =========================================================

@check_limit
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
    if not context.args:
        await update.message.reply_text(get_text(lang, "confirm_payment_usage"))
        return
    uid = int(context.args[0])
    if user_mgr.confirm_binance_payment(uid):
        await update.message.reply_text(get_text(lang, "confirm_payment_ok", user_id=uid))
    else:
        await update.message.reply_text(get_text(lang, "confirm_payment_missing", user_id=uid))

# =========================================================
# REFRESH HISTORY
# =========================================================

@check_limit
async def refreshhistory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
    await update.message.reply_text(get_text(lang, "refreshhistory_start"))
    from bot_handlers import check_signal_outcomes
    await check_signal_outcomes(context.bot)
    await update.message.reply_text(get_text(lang, "refreshhistory_done"))

# =========================================================
# CLEAR HISTORY
# =========================================================

@check_limit
async def clearhistory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    lang = user_mgr.get_setting(update.effective_user.id, "lang", "en")
    history_mgr.clear_all_signals()
    await update.message.reply_text(get_text(lang, "clearhistory_done"))

# =========================================================
# QUOTA
# =========================================================

@check_limit
async def quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🔍 Vérification du quota...")
    try:
        from config import TWELVEDATA_API_KEY
        url = f"https://api.twelvedata.com/api-usage?apikey={TWELVEDATA_API_KEY}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            used = data.get("current_usage", "?")
            limit = data.get("plan_limit", "?")
            await update.message.reply_text(f"📊 Quota Twelve Data\n🔢 Utilisé : {used}\n📈 Limite : {limit}")
        else:
            await update.message.reply_text("❌ Impossible de vérifier le quota")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")
