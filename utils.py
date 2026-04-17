import os
import json
import hashlib
import time
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
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return {}

def save_json(filepath: str, data: Dict):
    """Sauvegarde un fichier JSON"""
    ensure_data_dir()
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")

def is_valid_symbol(symbol: str) -> bool:
    """Vérifie si le symbole semble valide (lettres/chiffres/:/.)"""
    import re
    return bool(re.match(r'^[A-Za-z0-9:./]+$', symbol))

def normalize_symbol(symbol: str) -> str:
    """Normalise le symbole (majuscules, remplace / par :)"""
    s = symbol.upper().strip()
    # Pour forex: EUR/USD -> EURUSD ou selon API
    if '/' in s:
        s = s.replace('/', '')
    return s

def format_number(num: float, decimals: int = 2) -> str:
    """Formate un nombre avec séparateur de milliers."""
    if abs(num) < 0.01 and num != 0:
        return f"{num:.8f}".rstrip('0').rstrip('.')
    # Pour le Forex, on veut souvent 4 décimales
    if 0.01 <= abs(num) < 1000:
        decimals = max(decimals, 4)
    return f"{num:,.{decimals}f}"

def format_timestamp(ts: float) -> str:
    """Convertit timestamp en date lisible"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def get_date_days_ago(days: int) -> datetime:
    """Retourne la date il y a N jours"""
    return datetime.now() - timedelta(days=days)

def cache_key(*args) -> str:
    """Génère une clé de cache unique"""
    raw = "|".join(str(a) for a in args)
    return hashlib.md5(raw.encode()).hexdigest()