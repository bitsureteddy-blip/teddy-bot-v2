import requests
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID
from bot_handlers import check_limit


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
