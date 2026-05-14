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
FCS_WS_KEY = os.environ.get("FCS_WS_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# --- Limites utilisateur ---
FREE_DAILY_REQUESTS = 5
TRIAL_DAYS = 3

# --- Cache ---
PRICE_CACHE_TTL = 15        # secondes
HISTORY_CACHE_TTL = 300     # secondes (5 minutes)

# --- Analyse technique ---
DEFAULT_TIMEFRAME = "1h"
HISTORY_PERIOD = "6mo"
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

SYMBOL_CONFIGS = {
    # ========== CRYPTOS ==========
    "BTCUSD": {
        "adx_min": 25,
        "rsi_buy_low": 45, "rsi_buy_high": 70,
        "rsi_sell_low": 30, "rsi_sell_high": 55,
        "atr_max_pct": 3.5,
        "min_cond": 4,
        "weights": {"trend": 45, "rsi": 20, "macd": 0, "adx": 20, "atr": 15}
    },
    "ETHUSD": {
        "adx_min": 25,
        "rsi_buy_low": 45, "rsi_buy_high": 70,
        "rsi_sell_low": 30, "rsi_sell_high": 55,
        "atr_max_pct": 4.0,
        "min_cond": 4,
        "weights": {"trend": 45, "rsi": 20, "macd": 0, "adx": 20, "atr": 15}
    },

    # ========== FOREX ==========
    "EURUSD": {
        "adx_min": 20,
        "rsi_buy_low": 40, "rsi_buy_high": 65,
        "rsi_sell_low": 35, "rsi_sell_high": 60,
        "atr_max_pct": 0.8,
        "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },
    "GBPUSD": {
        "adx_min": 20,
        "rsi_buy_low": 40, "rsi_buy_high": 65,
        "rsi_sell_low": 35, "rsi_sell_high": 60,
        "atr_max_pct": 1.2,
        "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },
    "USDJPY": {
        "adx_min": 22,
        "rsi_buy_low": 42, "rsi_buy_high": 68,
        "rsi_sell_low": 32, "rsi_sell_high": 58,
        "atr_max_pct": 1.0,
        "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },
    "AUDUSD": {
        "adx_min": 20,
        "rsi_buy_low": 38, "rsi_buy_high": 62,
        "rsi_sell_low": 38, "rsi_sell_high": 62,
        "atr_max_pct": 0.9,
        "min_cond": 4,
        "weights": {"trend": 40, "rsi": 20, "macd": 0, "adx": 25, "atr": 15}
    },

    # ========== OR ==========
    "XAUUSD": {
        "adx_min": 25,
        "rsi_buy_low": 48, "rsi_buy_high": 72,
        "rsi_sell_low": 28, "rsi_sell_high": 52,
        "atr_max_pct": 2.0,
        "min_cond": 4,
        "weights": {"trend": 45, "rsi": 20, "macd": 0, "adx": 20, "atr": 15}
    },

    # ========== ACTIONS TECH ==========
    "AAPL": {
        "adx_min": 20,
        "rsi_buy_low": 40, "rsi_buy_high": 60,
        "rsi_sell_low": 40, "rsi_sell_high": 60,
        "atr_max_pct": 2.5,
        "min_cond": 3,
        "weights": {"trend": 35, "rsi": 25, "macd": 0, "adx": 20, "atr": 20}
    },
    "TSLA": {
        "adx_min": 22,
        "rsi_buy_low": 35, "rsi_buy_high": 65,
        "rsi_sell_low": 35, "rsi_sell_high": 65,
        "atr_max_pct": 4.5,
        "min_cond": 4,
        "weights": {"trend": 35, "rsi": 20, "macd": 0, "adx": 20, "atr": 25}
    },
    "NVDA": {
        "adx_min": 22,
        "rsi_buy_low": 42, "rsi_buy_high": 68,
        "rsi_sell_low": 32, "rsi_sell_high": 58,
        "atr_max_pct": 5.0,
        "min_cond": 4,
        "weights": {"trend": 35, "rsi": 25, "macd": 0, "adx": 20, "atr": 20}
    },
}
# --- Fichiers de données ---
DATA_DIR = "data"
USERS_FILE = f"{DATA_DIR}/users.json"
ALERTS_FILE = f"{DATA_DIR}/alerts.json"
WATCHLISTS_FILE = f"{DATA_DIR}/watchlists.json"
SETTINGS_FILE = f"{DATA_DIR}/settings.json"
USAGE_FILE = f"{DATA_DIR}/usage.json"
SIGNALS_HISTORY_FILE = f"{DATA_DIR}/signals_history.json"
CHALLENGE_SESSIONS_FILE = f"{DATA_DIR}/challenge_sessions.json"

# WebSocket URLs
TWELVEDATA_WS_URL = "wss://ws.twelvedata.com/v1/quotes/price"
FCS_WS_URL = "wss://ws-v4.fcsapi.com/ws"
REALMARKET_WS_URL = "wss://api.realmarketapi.com/price"

# --- WebSocket RealMarket (optionnel) ---
WS_URL = "wss://api.realmarketapi.com/v1/ws"

# --- Rôles Premium (simplifié) ---
PREMIUM_ROLES = ["pro"]
BINANCE_ID = "1240718832"
