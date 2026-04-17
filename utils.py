import os
import json
import hashlib
import time
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def ensure_data_dir():
    """Crée le dossier data s'il n'existe pas"""
    from config import DATA_DIR
    os.makedirs(DATA_DIR, exist_ok=True)

def load_json(filepath: str) -> Dict:
    """Charge un fichier JSON, retourne {} si inexistant"""
    ensure_data_dir()
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return {}

def save_json(filepath: str, data: Dict):
    """Sauvegarde un fichier JSON"""
    ensure_data_dir()
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")

def is_valid_symbol(symbol: str) -> bool:
    """
    Vérifie si le symbole a un format valide.
    Accepte lettres, chiffres, slash, point, tiret.
    """
    if not symbol or len(symbol) < 2:
        return False
    return bool(re.match(r'^[A-Z0-9/.-]+$', symbol.upper()))

def normalize_symbol(symbol: str) -> str:
    """Normalise le symbole (majuscules, supprime les /)"""
    s = symbol.upper().strip()
    if '/' in s:
        s = s.replace('/', '')
    return s

def format_number(num: float, decimals: int = 2) -> str:
    """
    Formate un nombre avec séparateur de milliers.
    Adapte automatiquement le nombre de décimales pour le Forex.
    """
    if num is None:
        return "N/A"
    if abs(num) < 0.01 and num != 0:
        return f"{num:.8f}".rstrip('0').rstrip('.')
    # Pour le Forex, on veut souvent 4 ou 5 décimales
    if 0.01 <= abs(num) < 1000:
        decimals = max(decimals, 4)
    return f"{num:,.{decimals}f}"

def format_timestamp(ts: float) -> str:
    """Convertit un timestamp en date lisible"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def get_date_days_ago(days: int) -> datetime:
    """Retourne la date il y a N jours"""
    return datetime.now() - timedelta(days=days)

def cache_key(*args) -> str:
    """Génère une clé de cache unique à partir d'arguments"""
    raw = "|".join(str(a) for a in args)
    return hashlib.md5(raw.encode()).hexdigest()