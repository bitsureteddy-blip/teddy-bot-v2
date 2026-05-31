with open('admin_handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()

marker = 'async def exportsignals(update: Update, context: ContextTypes.DEFAULT_TYPE):'

new_command = '''# =========================================================
# DB QUERY
# =========================================================

@check_limit
async def dbquery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /dbquery <SQL>")
        return
    sql = " ".join(context.args)
    try:
        from database import get_db
        conn = get_db()
        rows = conn.execute(sql).fetchall()
        if not rows:
            await update.message.reply_text("Requete OK, 0 resultats")
            return
        text = ""
        for r in rows[:20]:
            text += str(dict(r)) + "\\n"
        if len(rows) > 20:
            text += f"\\n... et {len(rows) - 20} de plus"
        await update.message.reply_text(text[:4000])
    except Exception as e:
        await update.message.reply_text(f"Erreur: {e}")

'''

content = content.replace(marker, new_command + marker, 1)

with open('admin_handlers.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK')
