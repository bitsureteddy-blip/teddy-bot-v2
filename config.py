import os

# --- Identifiants ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")  # Optionnel pour la Web App
ADMIN_ID = 8376348929

# --- Clés API ---
FCS_API_KEY = os.environ.get("FCS_API_KEY", "")
REALMARKET_API_KEY = os.environ.get("REALMARKET_API_KEY", "")
TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY", "c7b582eed7b24bff942030a3623c6429")  # Ta clé

# --- Limites utilisateur ---
FREE_DAILY_REQUESTS = 5          # Réduit à 5 requêtes/jour
TRIAL_DAYS = 3                   # Essai gratuit de 3 jours

# --- Cache ---
PRICE_CACHE_TTL = 15        # secondes
HISTORY_CACHE_TTL = 300     # secondes (5 minutes)

# --- Analyse technique ---
DEFAULT_TIMEFRAME = "1d"    # daily pour les signaux
HISTORY_PERIOD = "2mo"      # 2 mois de données
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
SMA_SHORT = 20
SMA_LONG = 50
SUPPORT_RESISTANCE_LOOKBACK = 50
DIVERGENCE_LOOKBACK = 5

# --- Fichiers de données ---
DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.json"
ALERTS_FILE = f"{DATA_DIR}/alerts.json"
WATCHLISTS_FILE = f"{DATA_DIR}/watchlists.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"
USAGE_FILE = f"{DATA_DIR}/usage.json"

# --- WebSocket RealMarket ---
WS_URL = "wss://api.realmarketapi.com/v1/ws"  # URL à adapter selon doc

# --- Rôles Premium ---
PREMIUM_ROLES = {
    "PRO": "pro",
    "ELITE": "elite"
}
# --- IA Gemini ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")