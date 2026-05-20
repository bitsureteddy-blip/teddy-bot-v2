import os

# =========================================================
# IDENTIFIANTS
# =========================================================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN manquant dans l'environnement")

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
if ADMIN_ID == 0:
    raise ValueError("❌ ADMIN_ID manquant ou invalide dans l'environnement")

# =========================================================
# CLÉS API
# =========================================================

TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY")

# =========================================================
# ACCÈS & UTILISATEURS
# =========================================================

ACCESS_MODE = "approved_only"
ALLOW_AUTO_REGISTER = True
TRIAL_DAYS = 30

USER_ROLES = ["tester", "pro", "admin"]
PREMIUM_ROLES = ["pro", "admin"]

# =========================================================
# LIMITES UTILISATEURS
# =========================================================

FREE_DAILY_REQUESTS = 5
MAX_WATCHLIST_SYMBOLS_FREE = 5
MAX_WATCHLIST_SYMBOLS_TESTER = 25
MAX_WATCHLIST_SYMBOLS_PRO = 100
MAX_ALERTS_FREE = 3
MAX_ALERTS_TESTER = 20
MAX_ALERTS_PRO = 100

# =========================================================
# CACHE
# =========================================================

PRICE_CACHE_TTL = 15
HISTORY_CACHE_TTL = 300

# =========================================================
# ANALYSE TECHNIQUE
# =========================================================

DEFAULT_TIMEFRAME = "1h"
HISTORY_PERIOD = "6mo"
ATR_PERIOD = 14
ATR_MULTIPLIER_SL = 1.5
RR_RATIO_TARGET = 2.0

# =========================================================
# CONFIGURATION DES SYMBOLS
# =========================================================

SYMBOL_CONFIGS = {
    "BTCUSD": {
        "adx_min": 25, "rsi_buy_low": 45, "rsi_buy_high": 70,
        "rsi_sell_low": 30, "rsi_sell_high": 55, "atr_max_pct": 3.5, "min_cond": 4,
        "weights": {"trend": 45, "rsi": 20, "macd": 0, "adx": 20, "atr": 15}
    },
    "ETHUSD": {
        "adx_min": 25, "rsi_buy_low": 45, "rsi_buy_high": 70,
        "rsi_sell_low": 30, "rsi_sell_high": 55, "atr_max_pct": 4.0, "min_cond": 4,
        "weights": {"trend": 45, "rsi": 20, "macd": 0, "adx": 20, "atr": 15}
    },
    "EURUSD": {
        "adx_min": 20, "rsi_buy_low": 40, "rsi_buy_high": 65,
        "rsi_sell_low": 35, "rsi_sell_high": 60, "atr_max_pct": 0.8, "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },
    "GBPUSD": {
        "adx_min": 20, "rsi_buy_low": 40, "rsi_buy_high": 65,
        "rsi_sell_low": 35, "rsi_sell_high": 60, "atr_max_pct": 1.2, "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },
    "USDJPY": {
        "adx_min": 22, "rsi_buy_low": 42, "rsi_buy_high": 68,
        "rsi_sell_low": 32, "rsi_sell_high": 58, "atr_max_pct": 1.0, "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },
    "AUDUSD": {
        "adx_min": 20, "rsi_buy_low": 38, "rsi_buy_high": 62,
        "rsi_sell_low": 38, "rsi_sell_high": 62, "atr_max_pct": 0.9, "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },
    "XAUUSD": {
        "adx_min": 25, "rsi_buy_low": 48, "rsi_buy_high": 72,
        "rsi_sell_low": 28, "rsi_sell_high": 52, "atr_max_pct": 2.0, "min_cond": 4,
        "weights": {"trend": 45, "rsi": 20, "macd": 0, "adx": 20, "atr": 15}
    },
    "AAPL": {
        "adx_min": 20, "rsi_buy_low": 40, "rsi_buy_high": 60,
        "rsi_sell_low": 40, "rsi_sell_high": 60, "atr_max_pct": 2.5, "min_cond": 3,
        "weights": {"trend": 35, "rsi": 25, "macd": 0, "adx": 20, "atr": 20}
    },
    "TSLA": {
        "adx_min": 22, "rsi_buy_low": 35, "rsi_buy_high": 65,
        "rsi_sell_low": 35, "rsi_sell_high": 65, "atr_max_pct": 4.5, "min_cond": 4,
        "weights": {"trend": 35, "rsi": 20, "macd": 0, "adx": 20, "atr": 25}
    },
    "NVDA": {
        "adx_min": 22, "rsi_buy_low": 42, "rsi_buy_high": 68,
        "rsi_sell_low": 32, "rsi_sell_high": 58, "atr_max_pct": 5.0, "min_cond": 4,
        "weights": {"trend": 35, "rsi": 25, "macd": 0, "adx": 20, "atr": 20}
    },
}

# =========================================================
# DOSSIERS & FICHIERS
# =========================================================

DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.json"
ALERTS_FILE = f"{DATA_DIR}/alerts.json"
WATCHLISTS_FILE = f"{DATA_DIR}/watchlists.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"
USAGE_FILE = f"{DATA_DIR}/usage.json"

# =========================================================
# WEBSOCKETS
# =========================================================

TWELVEDATA_WS_URL = "wss://ws.twelvedata.com/v1/quotes/price"

# =========================================================
# AUTRES
# =========================================================

BINANCE_ID = os.environ.get("BINANCE_ID", "")
