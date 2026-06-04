"""
check_i18n.py
─────────────
Vérifie que les clés settings_* sont bien présentes ET correctement
traduites dans i18n.py. Les affiche pour diagnostic visuel.

Usage : python3 check_i18n.py

Si une clé est manquante ou retourne la clé brute, ce script
affiche le correctif exact à copier dans i18n.py.
"""

import sys
import importlib.util
import os

TARGET = "i18n.py"

EXPECTED_KEYS = [
    "settings_title",
    "settings_timeframe",
    "settings_style",
    "settings_lang",
    "settings_edit",
]

REQUIRED_VALUES = {
    "en": {
        "settings_title":     "⚙️ Your current settings",
        "settings_timeframe": "⏱️ Timeframe",
        "settings_style":     "🎯 Trading Style",
        "settings_lang":      "🌐 Language",
        "settings_edit":      "What do you want to change?",
    },
    "fr": {
        "settings_title":     "⚙️ Vos paramètres actuels",
        "settings_timeframe": "⏱️ Timeframe",
        "settings_style":     "🎯 Style de trading",
        "settings_lang":      "🌐 Langue",
        "settings_edit":      "Que voulez-vous modifier ?",
    },
}


def load_i18n():
    """Charge i18n.py dynamiquement et retourne le module."""
    if not os.path.exists(TARGET):
        print(f"[ERREUR] '{TARGET}' introuvable. Lance depuis le dossier du projet.")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("i18n", TARGET)
    mod  = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        print(f"[ERREUR] Impossible de charger {TARGET} : {e}")
        sys.exit(1)
    return mod


def find_translations(mod):
    """
    Cherche le dict de traductions dans le module.
    Supporte : TRANSLATIONS, translations, TEXTS, texts, i18n, I18N.
    """
    for name in ("TRANSLATIONS", "translations", "TEXTS", "texts", "i18n", "I18N"):
        obj = getattr(mod, name, None)
        if isinstance(obj, dict):
            return name, obj
    # Cherche n'importe quel dict qui a des sous-dicts avec "en"/"fr"
    for name, obj in vars(mod).items():
        if isinstance(obj, dict) and ("en" in obj or "fr" in obj):
            return name, obj
    return None, None


def main():
    mod = load_i18n()
    dict_name, translations = find_translations(mod)

    if translations is None:
        print("[ERREUR] Aucun dict de traductions trouvé dans i18n.py")
        print("         Vérifie que ton dict s'appelle TRANSLATIONS, translations, TEXTS ou texts.")
        sys.exit(1)

    print(f"[OK] Dict de traductions trouvé : '{dict_name}'")
    print()

    missing = {}   # {lang: [clés manquantes]}
    wrong   = {}   # {lang: {clé: (attendu, obtenu)}}

    for lang in ("en", "fr"):
        lang_dict = translations.get(lang, {})
        if not lang_dict:
            print(f"[ERREUR] Section '{lang}' absente du dict !")
            continue

        missing[lang] = []
        wrong[lang]   = {}

        for key in EXPECTED_KEYS:
            value = lang_dict.get(key)
            expected = REQUIRED_VALUES[lang][key]

            if value is None:
                missing[lang].append(key)
            elif value != expected:
                wrong[lang][key] = (expected, value)
            else:
                print(f"  [{lang}] ✅  {key!r:30s} → {value}")

    print()

    # ── Rapport ───────────────────────────────────────────────────────────────
    has_error = False

    for lang in ("en", "fr"):
        if missing.get(lang):
            has_error = True
            print(f"[MANQUANT — {lang.upper()}] Ces clés sont absentes :")
            for k in missing[lang]:
                v = REQUIRED_VALUES[lang][k]
                print(f"    '{k}': '{v}',")
            print()

        if wrong.get(lang):
            has_error = True
            print(f"[VALEUR INCORRECTE — {lang.upper()}] Ces clés ont une mauvaise valeur :")
            for k, (exp, got) in wrong[lang].items():
                print(f"    '{k}':")
                print(f"      attendu  → '{exp}'")
                print(f"      obtenu   → '{got}'")
            print()

    if not has_error:
        print("════════════════════════════════════════")
        print(" i18n.py est correct ✓ — toutes les clés settings_* sont présentes et traduites.")
        print("════════════════════════════════════════")
        print()
        print("Si get_text() retourne quand même la clé brute, le problème est dans")
        print("la fonction get_text() elle-même. Vérifie qu'elle fait bien :")
        print("    return translations.get(lang, translations['en']).get(key, key)")
    else:
        print("════════════════════════════════════════")
        print(" ACTION REQUISE : lance patch_i18n.py pour corriger i18n.py")
        print("════════════════════════════════════════")


if __name__ == "__main__":
    main()

