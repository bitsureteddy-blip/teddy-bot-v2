import os

# --- Identifiants (strictement via environnement) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN manquant dans l'environnement")

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
if ADMIN_ID == 0:
    raise ValueError("❌ ADMIN_ID manquant ou invalide dans l'environnement")

# --- Clés API (aucune valeur par défaut sensible) ---
FCS_API_KEY = os.environ.get("FCS_API_KEY")
REALMARKET_API_KEY = os.environ.get("REALMARKET_API_KEY")
TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# --- Limites utilisateur ---
FREE_DAILY_REQUESTS = 5
TRIAL_DAYS = 3

# --- Cache ---
PRICE_CACHE_TTL = 15        # secondes
HISTORY_CACHE_TTL = 300     # secondes (5 minutes)

# --- Analyse technique ---
DEFAULT_TIMEFRAME = "1d"
HISTORY_PERIOD = "1y"
RSI_PERIOD = 14
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3
STOCH_SMOOTH = 3
ADX_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
SMA_SHORT = 20
SMA_LONG = 50
SUPPORT_RESISTANCE_LOOKBACK = 50
DIVERGENCE_LOOKBACK = 5
ATR_PERIOD = 14
ATR_MULTIPLIER_SL = 1.5
RR_RATIO_TARGET = 2.0

# Seuils dynamiques par type d'actif
ADX_THRESHOLDS = {"forex": 25, "crypto": 30, "metal": 22, "stock": 25}
ATR_PRICE_MAX = {"forex": 0.04, "crypto": 0.06, "metal": 0.05, "stock": 0.05}
RSI_BUY_LOW = {"forex": 55, "crypto": 50, "metal": 52, "stock": 55}
RSI_BUY_HIGH = {"forex": 68, "crypto": 72, "metal": 70, "stock": 68}
RSI_SELL_LOW = {"forex": 32, "crypto": 28, "metal": 30, "stock": 32}
RSI_SELL_HIGH = {"forex": 45, "crypto": 50, "metal": 48, "stock": 45}

# Seuils BTCUSD (trend + breakout)
BTC_ADX_MIN = 30
BTC_RSI_BUY_LOW = 55
BTC_RSI_BUY_HIGH = 70
BTC_RSI_SELL_LOW = 30
BTC_RSI_SELL_HIGH = 45
BTC_ATR_MIN_RATIO = 0.005
BTC_ATR_MAX_RATIO = 0.08
BTC_TIMEFRAME = "4h"

# Seuils XAUUSD (range + mean reversion)
XAU_ADX_MAX = 25
XAU_RSI_BUY_MAX = 35
XAU_RSI_SELL_MIN = 65
XAU_ATR_MAX_RATIO = 0.03
XAU_TIMEFRAME = "1h"
# --- Fichiers de données ---
DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.json"
ALERTS_FILE = f"{DATA_DIR}/alerts.json"
WATCHLISTS_FILE = f"{DATA_DIR}/watchlists.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"
USAGE_FILE = f"{DATA_DIR}/usage.json"
SIGNALS_HISTORY_FILE = f"{DATA_DIR}/signals_history.json"
CHALLENGE_SESSIONS_FILE = f"{DATA_DIR}/challenge_sessions.json"

# --- WebSocket RealMarket (optionnel) ---
WS_URL = "wss://api.realmarketapi.com/v1/ws"

# --- Rôles Premium (simplifié) ---
PREMIUM_ROLES = ["pro"]
BINANCE_ID = "1240718832"
