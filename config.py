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
    "BTCUSD": {"adx_min": 20, "rsi_buy_low": 32, "rsi_buy_high": 50, "rsi_sell_low": 50, "rsi_sell_high": 68, "atr_max_pct": 5.5, "min_cond": 4, "weights": {"trend": 25, "rsi": 20, "macd": 20, "adx": 20, "atr": 15}},
    "ETHUSD": {"adx_min": 22, "rsi_buy_low": 35, "rsi_buy_high": 48, "rsi_sell_low": 52, "rsi_sell_high": 65, "atr_max_pct": 5.5, "min_cond": 4, "weights": {"trend": 20, "rsi": 20, "macd": 25, "adx": 20, "atr": 15}},
    "SOLUSD": {"adx_min": 23, "rsi_buy_low": 34, "rsi_buy_high": 47, "rsi_sell_low": 53, "rsi_sell_high": 66, "atr_max_pct": 8.0, "min_cond": 4, "weights": {"trend": 20, "rsi": 20, "macd": 25, "adx": 20, "atr": 15}},
    "XRPUSD": {"adx_min": 22, "rsi_buy_low": 30, "rsi_buy_high": 48, "rsi_sell_low": 52, "rsi_sell_high": 70, "atr_max_pct": 7.0, "min_cond": 4, "weights": {"trend": 20, "rsi": 20, "macd": 25, "adx": 20, "atr": 15}},
    "EURUSD": {"adx_min": 16, "rsi_buy_low": 30, "rsi_buy_high": 42, "rsi_sell_low": 58, "rsi_sell_high": 70, "atr_max_pct": 1.1, "min_cond": 4, "weights": {"trend": 30, "rsi": 15, "macd": 15, "adx": 20, "atr": 20}},
    "GBPUSD": {"adx_min": 16, "rsi_buy_low": 30, "rsi_buy_high": 42, "rsi_sell_low": 58, "rsi_sell_high": 70, "atr_max_pct": 1.3, "min_cond": 4, "weights": {"trend": 30, "rsi": 15, "macd": 15, "adx": 20, "atr": 20}},
    "USDJPY": {"adx_min": 18, "rsi_buy_low": 31, "rsi_buy_high": 41, "rsi_sell_low": 59, "rsi_sell_high": 69, "atr_max_pct": 1.0, "min_cond": 4, "weights": {"trend": 30, "rsi": 15, "macd": 15, "adx": 20, "atr": 20}},
    "AUDUSD": {"adx_min": 18, "rsi_buy_low": 30, "rsi_buy_high": 40, "rsi_sell_low": 60, "rsi_sell_high": 70, "atr_max_pct": 1.1, "min_cond": 4, "weights": {"trend": 30, "rsi": 15, "macd": 15, "adx": 20, "atr": 20}},
    "XAUUSD": {"adx_min": 20, "rsi_buy_low": 32, "rsi_buy_high": 44, "rsi_sell_low": 56, "rsi_sell_high": 68, "atr_max_pct": 2.0, "min_cond": 4, "weights": {"trend": 25, "rsi": 15, "macd": 20, "adx": 20, "atr": 20}},
    "WTI": {"adx_min": 21, "rsi_buy_low": 33, "rsi_buy_high": 46, "rsi_sell_low": 54, "rsi_sell_high": 67, "atr_max_pct": 4.0, "min_cond": 4},
    "XAGUSD": {"adx_min": 21, "rsi_buy_low": 33, "rsi_buy_high": 46, "rsi_sell_low": 54, "rsi_sell_high": 67, "atr_max_pct": 4.5, "min_cond": 4},
    "AAPL": {"adx_min": 20, "rsi_buy_low": 33, "rsi_buy_high": 45, "rsi_sell_low": 55, "rsi_sell_high": 67, "atr_max_pct": 3.0, "min_cond": 4, "weights": {"trend": 25, "rsi": 20, "macd": 20, "adx": 20, "atr": 15}},
    "TSLA": {"adx_min": 22, "rsi_buy_low": 34, "rsi_buy_high": 47, "rsi_sell_low": 53, "rsi_sell_high": 66, "atr_max_pct": 6.0, "min_cond": 4, "weights": {"trend": 20, "rsi": 20, "macd": 25, "adx": 20, "atr": 15}},
    "NVDA": {"adx_min": 21, "rsi_buy_low": 34, "rsi_buy_high": 46, "rsi_sell_low": 54, "rsi_sell_high": 66, "atr_max_pct": 4.5, "min_cond": 4, "weights": {"trend": 25, "rsi": 20, "macd": 20, "adx": 20, "atr": 15}},
    "SPX": {"adx_min": 18, "rsi_buy_low": 32, "rsi_buy_high": 44, "rsi_sell_low": 56, "rsi_sell_high": 68, "atr_max_pct": 1.5, "min_cond": 4},
    "NDX": {"adx_min": 19, "rsi_buy_low": 33, "rsi_buy_high": 45, "rsi_sell_low": 55, "rsi_sell_high": 67, "atr_max_pct": 2.2, "min_cond": 4},
}

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
