
import logging
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os
from io import BytesIO

TOKEN = os.environ.get('TELEGRAM_TOKEN')

user_language = {}

# ================= TRADUCTIONS COMPLÈTES =================

texts = {
    "fr": {
        "buy": "🟢 ACHETER",
        "sell": "🔴 VENDRE",
        "wait": "🟡 ATTENDRE",
        "no_signal": "Aucun signal",
        "chart": "📊 Génération du graphique...",
        "start": "🤖 Bitsure Teddy – Assistant Trading\n\nJ'analyse crypto, actions, forex et or en temps réel.\n\nCommandes:\n/analyse BTC-USD – Analyse complète + graphique\n/price BTC-USD – Prix uniquement\n/langue – Changer la langue\n\nExemples:\n/analyse EURUSD=X\n/analyse USDBIF=X (USD → BIF)\n/analyse GC=F (or)\n\n📊 Pas un conseil financier – juste des données.",
        "price_cmd": "💰 {} : {}{:.4f}",
        "analyzing": "📊 Analyse de {}...",
        "not_found": "❌ Symbole {} introuvable",
        "lang_changed": "✅ Langue changée pour le français !",
        "lang_prompt": "🌐 Choisis ta langue :",
        "advice_wait_pullback": "⚠️ Attendre un retracement avant d'acheter",
        "advice_good_entry": "✅ Bon point d'entrée",
        "advice_sell_pressure": "🔻 Pression vendeuse, risque de baisse",
        "advice_price_high": "⚠️ Prix élevé, risque de correction",
        "advice_bounce": "📈 Zone de rebond probable",
        "advice_observation": "📊 Observation, pas de signal clair",
        "advice_strong_buy": "🔥 Signal FORT d'achat",
        "advice_strong_sell": "💀 Signal FORT de vente",
        "score_low": "📉 Score faible, éviter de trader",
        "score_medium": "📊 Score moyen, risque modéré",
        "score_high": "📈 Score élevé, bonne opportunité"
    },
    "en": {
        "buy": "🟢 BUY",
        "sell": "🔴 SELL",
        "wait": "🟡 WAIT",
        "no_signal": "No signal",
        "chart": "📊 Generating chart...",
        "start": "🤖 Bitsure Teddy – Trading Assistant\n\nI analyze crypto, stocks, forex, and gold in real time.\n\nCommands:\n/analyse BTC-USD – Full analysis + chart\n/price BTC-USD – Price only\n/language – Change language\n\nExamples:\n/analyse EURUSD=X\n/analyse USDBIF=X (USD → BIF)\n/analyse GC=F (gold)\n\n📊 Not financial advice – just data.",
        "price_cmd": "💰 {} : {}{:.4f}",
        "analyzing": "📊 Analyzing {}...",
        "not_found": "❌ Symbol {} not found",
        "lang_changed": "✅ Language changed to English!",
        "lang_prompt": "🌐 Choose your language:",
        "advice_wait_pullback": "⚠️ Wait for a pullback before buying",
        "advice_good_entry": "✅ Good entry point",
        "advice_sell_pressure": "🔻 Selling pressure, downside risk",
        "advice_price_high": "⚠️ Price high, correction risk",
        "advice_bounce": "📈 Bounce zone likely",
        "advice_observation": "📊 No clear signal",
        "advice_strong_buy": "🔥 STRONG BUY signal",
        "advice_strong_sell": "💀 STRONG SELL signal",
        "score_low": "📉 Low score, avoid trading",
        "score_medium": "📊 Medium score, moderate risk",
        "score_high": "📈 High score, good opportunity"
    }
}

def get_text(user_id, key):
    lang = user_language.get(user_id, "fr")
    return texts[lang].get(key, key)

# ================= DEVISES =================

def get_display_currency(symbol):
    sym = symbol.upper()

    if sym.endswith("-USD"):
        return "$"

    if sym.endswith("=X") and len(sym) >= 6:
        base = sym[:3]
        target = sym[3:6]

        curr = target if base == "USD" else base

        symbols = {
            "EUR": "€", "GBP": "£", "USD": "$", "JPY": "¥",
            "CHF": "CHF", "CAD": "C$", "AUD": "A$", "NZD": "NZ$",
            "CNY": "¥", "BIF": "BIF", "RWF": "RWF", "TZS": "TZS"
        }

        return symbols.get(curr, curr)

    if sym in ["GC=F", "SI=F", "CL=F"]:
        return "$"

    return "$"

# ================= INDICATEURS =================

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data):
    exp1 = data.ewm(span=12, adjust=False).mean()
    exp2 = data.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger(data):
    sma = data.rolling(20).mean()
    std = data.rolling(20).std()
    return sma + 2*std, sma, sma - 2*std

# ================= SUPPORT / RÉSISTANCE =================

def calculate_support_resistance(data, lookback=50):
    high = data['High'].tail(lookback)
    low = data['Low'].tail(lookback)
    return {"support": low.min(), "resistance": high.max()}

# ================= ADVICE =================

def generate_advice(trend_up, trend_down, rsi, bb_zone, score, user_id):
    if score >= 6:
        return get_text(user_id, "advice_strong_buy")
    if score <= -6:
        return get_text(user_id, "advice_strong_sell")
    if trend_up and rsi > 65:
        return get_text(user_id, "advice_wait_pullback")
    if trend_up and rsi < 40:
        return get_text(user_id, "advice_good_entry")
    if trend_down and rsi > 60:
        return get_text(user_id, "advice_sell_pressure")
    if bb_zone == "haute":
        return get_text(user_id, "advice_price_high")
    if bb_zone == "basse":
        return get_text(user_id, "advice_bounce")
    return get_text(user_id, "advice_observation")

def get_score_text(score, user_id):
    if score >= 5:
        return get_text(user_id, "score_high")
    if score <= -5:
        return get_text(user_id, "score_low")
    return get_text(user_id, "score_medium")

# ================= ANALYSIS =================

def get_analysis(symbol):
    data = yf.Ticker(symbol).history(period="1mo", interval="1h")
    if data.empty:
        return None

    close = data['Close']
    price = close.iloc[-1]

    rsi = calculate_rsi(close).iloc[-1]
    macd, signal = calculate_macd(close)
    macd_val = macd.iloc[-1]
    signal_val = signal.iloc[-1]

    upper, mid, lower = calculate_bollinger(close)
    bb_pos = (price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])

    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]

    trend_up = price > sma20 > sma50
    trend_down = price < sma20 < sma50

    bb_zone = "neutre"
    if bb_pos > 0.8:
        bb_zone = "haute"
    elif bb_pos < 0.2:
        bb_zone = "basse"

    macd_up = macd_val > signal_val

    score = 0
    if trend_up:
        score += 2
    elif trend_down:
        score -= 2

    if macd_up:
        score += 1
    else:
        score -= 1

    if rsi < 30:
        score += 2
    elif rsi < 60:
        score += 1
    elif rsi > 70:
        score -= 2
    elif rsi > 65:
        score -= 1

    if bb_zone == "basse":
        score += 1
    elif bb_zone == "haute":
        score -= 1

    if score >= 3:
        signal_key = "buy"
    elif score <= -3:
        signal_key = "sell"
    else:
        signal_key = "wait"

    sr = calculate_support_resistance(data)

    return {
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "macd": macd_val,
        "sma20": sma20,
        "sma50": sma50,
        "signal": signal_key,
        "score": score,
        "trend_up": trend_up,
        "trend_down": trend_down,
        "bb_zone": bb_zone,
        "support": sr["support"],
        "resistance": sr["resistance"],
        "data": data
    }

# ================= CHART =================

def create_chart(symbol, data):
    df = data.tail(50)
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(df.index, df['Close'], label='Price', linewidth=2)
    sma20 = df['Close'].rolling(20).mean()
    sma50 = df['Close'].rolling(50).mean()

    ax.plot(df.index, sma20, '--', label='SMA20', alpha=0.7)
    ax.plot(df.index, sma50, '--', label='SMA50', alpha=0.7)

    upper, mid, lower = calculate_bollinger(df['Close'])
    ax.fill_between(df.index, upper, lower, alpha=0.2, color='gray')

    ax.legend()
    ax.set_title(symbol)
    ax.grid(True, alpha=0.3)

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()

    return buf

# ================= MAIN =================

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyse", analyse))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("langue", language))
    app.add_handler(CommandHandler("language", language))
    app.add_handler(CallbackQueryHandler(language_callback))

    print("🚀 Bitsure Teddy Bot - Version corrigée démarrée !")
    app.run_polling()