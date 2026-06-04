"""
patch_i18n.py
Ajoute proprement les clés settings_* dans i18n.py.
Usage : python3 patch_i18n.py
"""

import re
import shutil
import sys

TARGET = "i18n.py"
BACKUP = "i18n.py.bak"

# ── Nouvelles clés à injecter ──────────────────────────────────────────────
NEW_KEYS_EN = {
    "settings_title":    "⚙️ Your current settings",
    "settings_timeframe":"⏱️ Timeframe",
    "settings_style":    "🎯 Trading Style",
    "settings_lang":     "🌐 Language",
    "settings_edit":     "What do you want to change?",
}
NEW_KEYS_FR = {
    "settings_title":    "⚙️ Vos paramètres actuels",
    "settings_timeframe":"⏱️ Timeframe",
    "settings_style":    "🎯 Style de trading",
    "settings_lang":     "🌐 Langue",
    "settings_edit":     "Que voulez-vous modifier ?",
}

ANCHOR = "settings_info"  # clé existante — on insère AVANT elle


def build_block(keys: dict) -> str:
    """Génère le bloc de lignes Python proprement formaté."""
    lines = []
    for k, v in keys.items():
        # échapper les guillemets simples dans la valeur
        v_safe = v.replace("'", "\\'")
        lines.append(f"        '{k}': '{v_safe}',")
    return "\n".join(lines) + "\n"


def patch_section(content: str, lang: str, keys: dict) -> str:
    """
    Trouve le bloc de la langue `lang` et insère les clés
    juste avant la ligne contenant ANCHOR.
    """
    # Pattern : repère "lang": { ... "settings_info":
    # On cherche la ligne ANCHOR dans le bon contexte de langue.
    # Stratégie : on split par sections de langue, on patch la bonne.

    # Marqueur de début de section langue (robuste aux espaces)
    lang_marker = re.compile(
        r'(["\'])' + re.escape(lang) + r'\1\s*:\s*\{', re.IGNORECASE
    )

    match = lang_marker.search(content)
    if not match:
        print(f"[ERREUR] Section langue '{lang}' introuvable dans {TARGET}")
        sys.exit(1)

    section_start = match.end()

    # Cherche la clé ANCHOR uniquement après section_start
    anchor_pattern = re.compile(
        r'(\s*)(["\'])' + re.escape(ANCHOR) + r'\2\s*:'
    )
    anchor_match = anchor_pattern.search(content, section_start)
    if not anchor_match:
        print(f"[ERREUR] Clé '{ANCHOR}' introuvable dans la section '{lang}'")
        sys.exit(1)

    # Vérifie que les clés ne sont pas déjà présentes
    first_key = list(keys.keys())[0]
    check_zone = content[section_start:anchor_match.start()]
    if first_key in check_zone:
        print(f"[INFO] Clés déjà présentes dans la section '{lang}', on passe.")
        return content

    insert_pos = anchor_match.start()
    block = build_block(keys)
    return content[:insert_pos] + block + content[insert_pos:]


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

    # Patch EN puis FR
    patched = original
    patched = patch_section(patched, "en", NEW_KEYS_EN)
    patched = patch_section(patched, "fr", NEW_KEYS_FR)

    # Validation syntaxique avant d'écrire
    try:
        compile(patched, TARGET, "exec")
    except SyntaxError as e:
        print(f"[ERREUR] SyntaxError après patch : {e}")
        print("Fichier NON modifié. Corrige manuellement.")
        sys.exit(1)

    # Écriture
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(patched)

    print("[OK] i18n.py patché avec succès — syntaxe validée.")
    print("     Clés ajoutées : settings_title, settings_timeframe, settings_style, settings_lang, settings_edit")


if __name__ == "__main__":
    main()

