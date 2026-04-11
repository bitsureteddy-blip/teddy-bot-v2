import logging
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os
from io import BytesIO

# ================= CONFIGURATION =================
TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Dictionnaire pour stocker la langue de chaque utilisateur
user_language = {}

# ================= TRADUCTIONS =================
texts = {
    "fr": {
        "analyzing": "📊 *Analyse de {} en cours...*",
        "not_found": "❌ Symbole '{}' introuvable.",
        "price": "💰 *{}* : {}{:.4f}",
        "chart": "📊 *Génération du graphique...*",
        "chart_caption": "Graphique {} - 50 dernières périodes",
        "start": "🤖 *Bitsure Teddy – Assistant Trading*\n\nJ'analyse crypto, actions, forex et or en temps réel.\nIndicateurs: RSI, MACD, Bandes de Bollinger, Moyennes mobiles.\n\n*Commandes:*\n/analyse SYMBOLE – Analyse complète + graphique\n/price SYMBOLE – Prix uniquement\n/langue – Changer la langue\n\n*Exemples:*\n/analyse BTC-USD\n/analyse GC=F (or)\n/analyse AAPL (Apple)\n/analyse USDBIF=X (USD → BIF)\n\n📊 *Pas un conseil financier – juste des données.*",
        "lang_prompt": "🌐 *Choisis ta langue / Choose your language:*",
        "lang_changed": "✅ Langue changée pour le français !",
        "usage_analyse": "Utilisation: /analyse SYMBOLE\nExemple: /analyse BTC-USD",
        "usage_price": "Utilisation: /price SYMBOLE\nExemple: /price BTC-USD",
        "bullish": "📈 Tendance haussière",
        "bearish": "📉 Tendance baissière",
        "neutral_trend": "📊 Tendance latérale",
        "macd_bullish": "✅ MACD haussier",
        "macd_bearish": "❌ MACD baissier",
        "rsi_oversold": "🟢 RSI survendu (bon point entrée)",
        "rsi_high": "🔴 RSI élevé - risque de correction",
        "bollinger_low": "📌 Prix sous bande basse (rebond possible)",
        "bollinger_high": "⚠️ Prix sur bande haute - zone risquée",
        "buy": "🟢 ACHETER",
        "sell": "🔴 VENDRE",
        "wait": "🟡 ATTENDRE",
        "wait_high": "🟡 ATTENDRE (prix haut, risque correction)",
        "wait_pullback": "🟡 ATTENDRE - Entrée risquée, surveiller pullback",
        "no_signal": "Aucun signal fort"
    },
    "en": {
        "analyzing": "📊 *Analyzing {}...*",
        "not_found": "❌ Symbol '{}' not found.",
        "price": "💰 *{}* : {}{:.4f}",
        "chart": "📊 *Generating chart...*",
        "chart_caption": "Chart {} - Last 50 periods",
        "start": "🤖 *Bitsure Teddy – Trading Assistant*\n\nI analyze crypto, stocks, forex, and gold in real time.\nIndicators: RSI, MACD, Bollinger Bands, Moving Averages.\n\n*Commands:*\n/analyse SYMBOL – Full analysis + chart\n/price SYMBOL – Current price only\n/language – Change language\n\n*Examples:*\n/analyse BTC-USD\n/analyse GC=F (gold)\n/analyse AAPL (Apple)\n/analyse USDBIF=X (USD to BIF)\n\n📊 *Not financial advice – just data.*",
        "lang_prompt": "🌐 *Choose your language:*",
        "lang_changed": "✅ Language changed to English!",
        "usage_analyse": "Usage: /analyse SYMBOL\nExample: /analyse BTC-USD",
        "usage_price": "Usage: /price SYMBOL\nExample: /price BTC-USD",
        "bullish": "📈 Bullish trend",
        "bearish": "📉 Bearish trend",
        "neutral_trend": "📊 Neutral trend",
        "macd_bullish": "✅ MACD bullish",
        "macd_bearish": "❌ MACD bearish",
        "rsi_oversold": "🟢 RSI oversold (good entry)",
        "rsi_high": "🔴 RSI high - correction risk",
        "bollinger_low": "📌 Price below lower band (bounce possible)",
        "bollinger_high": "⚠️ Price on upper band - risky zone",
        "buy": "🟢 BUY",
        "sell": "🔴 SELL",
        "wait": "🟡 WAIT",
        "wait_high": "🟡 WAIT (price high, correction risk)",
        "wait_pullback": "🟡 WAIT - Risky entry, watch for pullback",
        "no_signal": "No strong signal"
    }
}

def get_text(user_id, key):
    """Retourne le texte dans la langue de l'utilisateur"""
    lang = user_language.get(user_id, "en")
    return texts[lang].get(key, texts["en"][key])

# ================= INDICATEURS TECHNIQUES =================

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    exp_fast = data.ewm(span=fast, adjust=False).mean()
    exp_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = exp_fast - exp_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger(data, period=20, std=2):
    sma = data.rolling(window=period).mean()
    upper = sma + (data.rolling(window=period).std() * std)
    lower = sma - (data.rolling(window=period).std() * std)
    return upper, sma, lower

# ================= DEVISES =================

def get_currency_symbol(symbol):
    """Retourne le symbole de devise approprié pour TOUTES les devises"""
    symbol_upper = symbol.upper()
    
    # Cryptos
    if symbol_upper.endswith("-USD"):
        return "$"
    
    # Forex : format XXXYYY=X
    if symbol_upper.endswith("=X") and len(symbol_upper) >= 6:
        # Extraire les 3 premières lettres (devise de base)
        base_currency = symbol_upper[:3]
        
        # Symboles des devises
        currency_symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
            "CHF": "CHF", "CAD": "C$", "AUD": "A$", "NZD": "NZ$",
            "CNY": "¥", "BIF": "BIF", "RWF": "RWF", "TZS": "TZS",
            "UGX": "UGX", "KES": "KES", "ZAR": "R", "INR": "₹",
            "BRL": "R$", "RUB": "₽", "KRW": "₩", "SGD": "S$",
            "HKD": "HK$", "SEK": "kr", "NOK": "kr", "DKK": "kr",
            "TRY": "₺", "MXN": "MX$"
        }
        
        # Si la devise de base est dans le dictionnaire, retourne son symbole
        if base_currency in currency_symbols:
            return currency_symbols[base_currency]
        else:
            # Sinon, retourne le code (ex: "BIF", "RWF")
            return base_currency
    
    # Or, argent, pétrole
    if symbol_upper in ["GC=F", "SI=F", "CL=F"]:
        return "$"
    
    # Actions et autres
    return "$"

# ================= GRAPHIQUE =================

def create_chart(symbol, data):
    df = data.tail(50).copy()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df.index, df['Close'], label='Price', color='blue', linewidth=2)
    sma = df['Close'].rolling(20).mean()
    std = df['Close'].rolling(20).std()
    ax.fill_between(df.index, sma + 2*std, sma - 2*std, alpha=0.2, color='gray', label='Bollinger Bands')
    ax.set_title(f'{symbol} - Last 50 periods')
    ax.set_ylabel(f'Price ({get_currency_symbol(symbol)})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    plt.close()
    return buffer

# ================= DONNÉES MARCHÉ =================

def get_market_data(symbol="BTC-USD"):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1mo", interval="1h")
    return data

# ================= ANALYSE =================

def get_analysis(symbol):
    data = get_market_data(symbol)
    if data.empty:
        return None
    
    close = data['Close']
    current_price = close.iloc[-1]
    
    rsi = calculate_rsi(close)
    current_rsi = rsi.iloc[-1]
    
    macd_line, signal_line, histogram = calculate_macd(close)
    current_macd = macd_line.iloc[-1]
    current_signal = signal_line.iloc[-1]
    current_hist = histogram.iloc[-1]
    
    bb_upper, bb_middle, bb_lower = calculate_bollinger(close)
    current_bb_upper = bb_upper.iloc[-1]
    current_bb_lower = bb_lower.iloc[-1]
    bb_position = (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower)
    
    sma20 = close.rolling(window=20).mean().iloc[-1]
    sma50 = close.rolling(window=50).mean().iloc[-1]
    
    trend_haussier = current_price > sma20 and sma20 > sma50
    trend_baissier = current_price < sma20 and sma20 < sma50
    
    if current_rsi < 30:
        rsi_zone = "survendu"
    elif current_rsi < 50:
        rsi_zone = "bas"
    elif current_rsi < 65:
        rsi_zone = "neutre"
    else:
        rsi_zone = "haut"
    
    if bb_position < 0.2:
        bollinger_zone = "basse"
    elif bb_position > 0.8:
        bollinger_zone = "haute"
    else:
        bollinger_zone = "neutre"
    
    macd_haussier = current_macd > current_signal and current_hist > 0
    macd_baissier = current_macd < current_signal and current_hist < 0
    
    reasons_keys = []
    
    if trend_haussier:
        reasons_keys.append("bullish")
    elif trend_baissier:
        reasons_keys.append("bearish")
    else:
        reasons_keys.append("neutral_trend")
    
    if macd_haussier:
        reasons_keys.append("macd_bullish")
    elif macd_baissier:
        reasons_keys.append("macd_bearish")
    
    if rsi_zone == "survendu":
        reasons_keys.append("rsi_oversold")
    elif rsi_zone == "haut":
        reasons_keys.append("rsi_high")
    
    if bollinger_zone == "basse":
        reasons_keys.append("bollinger_low")
    elif bollinger_zone == "haute":
        reasons_keys.append("bollinger_high")
    
    # Signal intelligent
    if trend_haussier and rsi_zone == "survendu":
        signal_key = "buy"
    elif trend_haussier and rsi_zone == "bas" and bollinger_zone != "haute":
        signal_key = "buy"
    elif trend_baissier and rsi_zone == "haut":
        signal_key = "sell"
    elif rsi_zone == "haut" or bollinger_zone == "haute":
        signal_key = "wait_high"
    elif trend_haussier and rsi_zone == "haut":
        signal_key = "wait_pullback"
    else:
        signal_key = "wait"
    
    return {
        'symbol': symbol,
        'price': current_price,
        'rsi': current_rsi,
        'macd': current_macd,
        'sma20': sma20,
        'sma50': sma50,
        'signal_key': signal_key,
        'reasons_keys': reasons_keys,
        'data': data
    }

# ================= COMMANDES TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(get_text(user_id, "start"), parse_mode='Markdown')

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌐 *Choose your language / Choisis ta langue :*", parse_mode='Markdown', reply_markup=reply_markup)

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "lang_fr":
        user_language[user_id] = "fr"
        await query.edit_message_text("✅ Langue changée pour le français !")
    elif query.data == "lang_en":
        user_language[user_id] = "en"
        await query.edit_message_text("✅ Language changed to English!")

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(get_text(user_id, "usage_analyse"))
        return
    
    symbol = context.args[0].upper()
    status_msg = await update.message.reply_text(get_text(user_id, "analyzing").format(symbol), parse_mode='Markdown')
    
    result = get_analysis(symbol)
    if not result:
        await status_msg.edit_text(get_text(user_id, "not_found").format(symbol))
        return
    
    currency = get_currency_symbol(symbol)
    reasons = [get_text(user_id, k) for k in result['reasons_keys']]
    signal = get_text(user_id, result['signal_key'])
    
    message = f"""
📈 *{result['symbol']}*
💰 Price: {currency}{result['price']:.2f}
📊 RSI: {result['rsi']:.1f}
📊 MACD: {result['macd']:.4f}
📈 SMA20: {currency}{result['sma20']:.2f}
📉 SMA50: {currency}{result['sma50']:.2f}

🎯 *{signal}*
📝 {', '.join(reasons) if reasons else get_text(user_id, 'no_signal')}
    """
    
    await status_msg.edit_text(message, parse_mode='Markdown')
    
    await update.message.reply_text(get_text(user_id, "chart"), parse_mode='Markdown')
    chart = create_chart(symbol, result['data'])
    await update.message.reply_photo(photo=chart, caption=get_text(user_id, "chart_caption").format(symbol))

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(get_text(user_id, "usage_price"))
        return
    
    symbol = context.args[0].upper()
    status_msg = await update.message.reply_text(f"💰 *Fetching price for {symbol}...*", parse_mode='Markdown')
    
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    if data.empty:
        await status_msg.edit_text(get_text(user_id, "not_found").format(symbol))
        return
    
    price = data['Close'].iloc[-1]
    currency = get_currency_symbol(symbol)
    
    await status_msg.edit_text(get_text(user_id, "price").format(symbol, currency, price), parse_mode='Markdown')

# ================= LANCEMENT =================

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyse", analyse))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("langue", language))
    app.add_handler(CommandHandler("language", language))
    app.add_handler(CallbackQueryHandler(language_callback))
    
    print("✅ Bitsure Teddy Bot - Version Bilingue démarrée !")
    print("👉 Commandes: /analyse SYMBOLE, /price SYMBOLE, /langue")
    app.run_polling()
