"""
patch_handlers.py
Remplace proprement la fonction settings() dans bot_handlers.py.
Usage : python3 patch_handlers.py
"""

import re
import shutil
import sys

TARGET = "bot_handlers.py"
BACKUP = "bot_handlers.py.bak"

# ── Nouvelle fonction settings ─────────────────────────────────────────────
NEW_FUNCTION = '''async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = user_mgr.get_setting(uid, "lang", "en")
    tf = user_mgr.get_setting(uid, "timeframe", DEFAULT_TIMEFRAME)
    style = user_mgr.get_setting(uid, "trading_style", "day")
    role = user_mgr.get_role(uid)

    style_names = {
        "day":      "Day Trader",
        "swing":    "Swing Trader",
        "position": "Position Trader",
    }
    style_display = style_names.get(style, style)

    lines = [
        get_text(lang, "settings_title"),
        get_text(lang, "settings_timeframe") + " : " + tf,
        get_text(lang, "settings_style") + " : " + style_display,
        get_text(lang, "settings_lang") + " : " + lang.upper(),
        "",
        get_text(lang, "settings_edit"),
    ]
    recap = "\\n".join(lines)

    await update.message.reply_text(recap)
'''


def find_function_bounds(content: str, func_name: str):
    """
    Trouve le début et la fin d'une fonction async/def dans `content`.
    Retourne (start, end) ou lève SystemExit si introuvable.
    """
    # Repère la ligne de définition
    pattern = re.compile(
        r'^(async\s+)?def\s+' + re.escape(func_name) + r'\s*\(',
        re.MULTILINE
    )
    m = pattern.search(content)
    if not m:
        print(f"[ERREUR] Fonction '{func_name}' introuvable dans {TARGET}")
        sys.exit(1)

    start = m.start()
    # Indentation de base = 0 (fonction de module)
    # La fonction se termine quand on trouve une ligne non-indentée
    # qui est aussi une def/class/décorateur, OU fin de fichier.
    after = content[m.end():]
    end_pattern = re.compile(r'\n(?=\S)', re.MULTILINE)  # newline suivi de non-espace
    end_match = end_pattern.search(after)

    if end_match:
        end = m.end() + end_match.start() + 1  # +1 pour inclure le \n
    else:
        end = len(content)

    return start, end


def main():
    # Lecture
    try:
        with open(TARGET, "r", encoding="utf-8") as f:
            original = f.read()
    except FileNotFoundError:
        print(f"[ERREUR] Fichier '{TARGET}' introuvable. Lance ce script depuis le dossier du projet.")
        sys.exit(1)

    # Backup
    shutil.copy(TARGET, BACKUP)
    print(f"[OK] Backup créé : {BACKUP}")

    # Localise la fonction
    start, end = find_function_bounds(original, "settings")
    old_func = original[start:end]
    print(f"[INFO] Fonction 'settings' trouvée (lignes {original[:start].count(chr(10))+1}–{original[:end].count(chr(10))+1})")
    print(f"[INFO] Ancienne version :\n---\n{old_func.strip()}\n---")

    # Vérifie qu'il ne s'agit pas déjà de la nouvelle version
    if "settings_title" in old_func:
        print("[INFO] La fonction contient déjà 'settings_title' — déjà à jour, rien à faire.")
        sys.exit(0)

    # Remplacement
    patched = original[:start] + NEW_FUNCTION + original[end:]

    # Validation syntaxique
    try:
        compile(patched, TARGET, "exec")
    except SyntaxError as e:
        print(f"[ERREUR] SyntaxError après patch : {e}")
        print("Fichier NON modifié.")
        sys.exit(1)

    # Écriture
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(patched)

    print("[OK] bot_handlers.py patché avec succès — syntaxe validée.")
    print("     Fonction 'settings' remplacée par la version avec récapitulatif.")


if __name__ == "__main__":
    main()

