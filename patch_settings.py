"""
patch_settings.py
─────────────────
Corrige la fonction settings() et le callback menu_parametres
dans bot_handlers.py.

Usage (depuis le dossier du projet) :
    python3 patch_settings.py

Ce que fait ce script :
  1. Remplace settings() par une version qui affiche recap + boutons
  2. Injecte la fonction helper send_settings_menu()
  3. Remplace le bloc menu_parametres dans le callback pour appeler send_settings_menu()
  4. Valide la syntaxe avant d'écrire
  5. Crée un backup .bak automatiquement
"""

import re
import shutil
import sys

TARGET = "bot_handlers.py"
BACKUP = "bot_handlers.py.bak"

# ══════════════════════════════════════════════════════════════════════════════
# 1. Fonction helper centrale — à injecter juste avant settings()
# ══════════════════════════════════════════════════════════════════════════════
HELPER_FUNCTION = '''
async def send_settings_menu(lang: str, tf: str, style: str, uid: int,
                             send_fn, edit_fn=None):
    """
    Construit le récapitulatif + les boutons settings.
    - send_fn  : coroutine pour envoyer un nouveau message (ex: update.message.reply_text)
    - edit_fn  : coroutine pour éditer un message existant (ex: safe_edit) — optionnel
    Appelle edit_fn si fourni, sinon send_fn.
    """
    style_names = {
        "day":      "Day Trader",
        "swing":    "Swing Trader",
        "position": "Position Trader",
    }
    style_display = style_names.get(style, style)

    recap_lines = [
        f"*{get_text(lang, 'settings_title')}*",
        f"{get_text(lang, 'settings_timeframe')} : `{tf}`",
        f"{get_text(lang, 'settings_style')} : {style_display}",
        f"{get_text(lang, 'settings_lang')} : {lang.upper()}",
        "",
        get_text(lang, "settings_edit"),
    ]
    recap = "\\n".join(recap_lines)

    keyboard = [
        [InlineKeyboardButton(get_text(lang, "btn_settimeframe"), callback_data="cmd_settimeframe")],
        [InlineKeyboardButton(get_text(lang, "btn_setlanguage"),  callback_data="cmd_setlanguage")],
        [InlineKeyboardButton("🎯 Trading Style",                  callback_data="cmd_setstyle")],
        [InlineKeyboardButton(get_text(lang, "btn_historique"),   callback_data="cmd_historique")],
        [InlineKeyboardButton(get_text(lang, "btn_support"),      callback_data="cmd_support")],
        [InlineKeyboardButton(get_text(lang, "back"),             callback_data="menu_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit_fn is not None:
        await edit_fn(recap, keyboard)
    else:
        await send_fn(recap, parse_mode="Markdown", reply_markup=reply_markup)

'''

# ══════════════════════════════════════════════════════════════════════════════
# 2. Nouvelle fonction settings() — commande directe /settings
# ══════════════════════════════════════════════════════════════════════════════
NEW_SETTINGS_FUNCTION = '''async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = user_mgr.get_setting(uid, "lang", "en")
    tf   = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
    style = user_mgr.get_setting(uid, "trading_style", "day")

    await send_settings_menu(
        lang=lang,
        tf=tf,
        style=style,
        uid=uid,
        send_fn=update.message.reply_text,
    )
'''

# ══════════════════════════════════════════════════════════════════════════════
# 3. Remplacement du bloc menu_parametres dans le callback
# ══════════════════════════════════════════════════════════════════════════════
# Ancien bloc (regex flexible aux espaces / guillemets)
OLD_MENU_PARAMETRES_PATTERN = re.compile(
    r'elif\s+data\s*==\s*["\']menu_parametres["\']\s*:(.*?)'
    r'(?=elif\s+data\s*==|else\s*:|$)',
    re.DOTALL
)

NEW_MENU_PARAMETRES_BLOCK = '''elif data == "menu_parametres":
        uid   = query.from_user.id
        lang  = user_mgr.get_setting(uid, "lang", "en")
        tf    = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
        style = user_mgr.get_setting(uid, "trading_style", "day")
        await send_settings_menu(
            lang=lang,
            tf=tf,
            style=style,
            uid=uid,
            send_fn=None,
            edit_fn=safe_edit,
        )
    '''


# ══════════════════════════════════════════════════════════════════════════════
# Utilitaires
# ══════════════════════════════════════════════════════════════════════════════

def find_function_bounds(content: str, func_name: str) -> tuple[int, int]:
    """Retourne (start, end) de la définition complète d'une fonction."""
    pattern = re.compile(
        r'^(async\s+)?def\s+' + re.escape(func_name) + r'\s*\(',
        re.MULTILINE
    )
    m = pattern.search(content)
    if not m:
        print(f"[ERREUR] Fonction '{func_name}' introuvable dans {TARGET}")
        sys.exit(1)

    start = m.start()
    after = content[m.end():]
    # Fin = prochaine ligne non-indentée (def/class/décorateur/EOF)
    end_m = re.search(r'\n(?=\S)', after)
    end = (m.end() + end_m.start() + 1) if end_m else len(content)
    return start, end


def validate_syntax(code: str, filename: str):
    try:
        compile(code, filename, "exec")
    except SyntaxError as e:
        print(f"[ERREUR] SyntaxError : {e}")
        print("Fichier NON modifié — restaure depuis le .bak si besoin.")
        sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Lecture ──────────────────────────────────────────────────────────────
    try:
        with open(TARGET, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[ERREUR] '{TARGET}' introuvable. Lance depuis le dossier du projet.")
        sys.exit(1)

    shutil.copy(TARGET, BACKUP)
    print(f"[OK] Backup : {BACKUP}")

    # ── Étape 1 : injecter send_settings_menu() avant settings() ─────────────
    if "async def send_settings_menu" in content:
        print("[INFO] send_settings_menu() déjà présente — on passe l'injection.")
    else:
        s_start, _ = find_function_bounds(content, "settings")
        content = content[:s_start] + HELPER_FUNCTION + content[s_start:]
        print("[OK] send_settings_menu() injectée.")

    # ── Étape 2 : remplacer settings() ───────────────────────────────────────
    s_start, s_end = find_function_bounds(content, "settings")
    old_body = content[s_start:s_end]

    if "send_settings_menu" in old_body:
        print("[INFO] settings() déjà mise à jour — on passe.")
    else:
        content = content[:s_start] + NEW_SETTINGS_FUNCTION + content[s_end:]
        print("[OK] settings() remplacée.")

    # ── Étape 3 : remplacer le bloc menu_parametres ───────────────────────────
    if "send_settings_menu" in content[content.find("menu_parametres"):content.find("menu_parametres") + 500]:
        print("[INFO] menu_parametres déjà mis à jour — on passe.")
    else:
        m = OLD_MENU_PARAMETRES_PATTERN.search(content)
        if not m:
            print("[ATTENTION] Bloc menu_parametres introuvable via regex.")
            print("            Cherche manuellement 'elif data == \"menu_parametres\"' et remplace son corps.")
        else:
            full_match = m.group(0)
            # Reconstruit : garde le elif + remplace le corps
            content = content.replace(full_match, NEW_MENU_PARAMETRES_BLOCK)
            print("[OK] Bloc menu_parametres remplacé.")

    # ── Validation syntaxique ─────────────────────────────────────────────────
    validate_syntax(content, TARGET)

    # ── Écriture ──────────────────────────────────────────────────────────────
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)

    print()
    print("════════════════════════════════════════")
    print(" bot_handlers.py patché avec succès ✓")
    print(" Lance : python3 -m py_compile bot_handlers.py")
    print("════════════════════════════════════════")


if __name__ == "__main__":
    main()

