import logging
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests
import threading
import json
import websocket
from io import BytesIO

TOKEN = os.environ.get('TELEGRAM_TOKEN')
FCS_API_KEY = os.environ.get('FCS_API_KEY')
REALMARKET_API_KEY = os.environ.get('REALMARKET_API_KEY')

# Stockage des prix temps réel (WebSocket)
realtime_prices = {}

# ================= WEBSOCKET (RealMarketAPI) =================
def on_ws_message(ws, message):
    try:
        data = json.loads(message)
        symbol = data.get('symbolCode')
        price = data.get('price')
        if symbol and price:
            realtime_prices[symbol] = float(price)
    except:
        pass

def start_websocket():
    if not REALMARKET_API_KEY:
        return
    url = f"wss://api.realmarketapi.com/price?apiKey={REALMARKET_API_KEY}&symbolCode=GBPUSD&timeFrame=M1"
    ws = websocket.WebSocketApp(url, on_message=on_ws_message)
    ws.run_forever()

# Lancer le WebSocket dans un thread séparé
if REALMARKET_API_KEY:
    threading.Thread(target=start_websocket, daemon=True).start()

# ================= PRIX VIA FCS API =================
def get_fcs_price(symbol):
    if not FCS_API_KEY:
        return None
    # Convertir le symbole Yahoo en format FCS (ex: GBPJPY=X -> GBP/JPY)
    sym = symbol.upper().replace('=X', '')
    if '/' not in sym and len(sym) == 6:
        sym = sym[:3] + '/' + sym[3:]
    url = f"https://fcsapi.com/api-v3/forex/latest?symbol={sym}&access_key={FCS_API_KEY}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data.get('status'):
            return float(data['response'][0]['c'])
    except:
        pass
    return None

# ================= INDICATEURS (Yahoo) =================
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

def calculate_support_resistance(data, lookback=50):
    high = data['High'].tail(lookback)
    low = data['Low'].tail(lookback)
    return {"support": low.min(), "resistance": high.max()}

def get_display_currency(symbol):
    sym = symbol.upper()
    if sym.endswith("-USD") or sym in ["GC=F", "SI=F", "CL=F"]:
        return "$"
    if sym.endswith("=X") and len(sym) >= 6:
        base = sym[:3]
        symbols = {"EUR": "€", "GBP": "£", "USD": "$", "JPY": "¥"}
        return symbols.get(base, base)
    return "$"

def get_analysis(symbol):
    # 1. Récupérer les données historiques (Yahoo) pour les indicateurs
    data = yf.Ticker(symbol).history(period="2mo", interval="1h")
    if data.empty:
        return None

    close = data['Close']
    price = close.iloc[-1]  # fallback

    # 2. Essayer d'abord le prix temps réel (WebSocket)
    if symbol in realtime_prices:
        price = realtime_prices[symbol]
    else:
        # 3. Sinon, utiliser FCS API (forex uniquement)
        fcs_price = get_fcs_price(symbol)
        if fcs_price:
            price = fcs_price
        # 4. Sinon garder le dernier prix Yahoo

    rsi = calculate_rsi(close).iloc[-1]
    macd, signal = calculate_macd(close)
    macd_val = macd.iloc[-1]
    signal_val = signal.iloc[-1]
    macd_hist = macd_val - signal_val

    upper, mid, lower = calculate_bollinger(close)
    bb_pos = (price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])

    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]

    trend_up = price > sma20 > sma50
    trend_down = price < sma20 < sma50

    sr = calculate_support_resistance(data)

    # Divergences
    rsi_series = calculate_rsi(close)
    price_series = close
    divergence_bullish = (price_series.iloc[-5] < price_series.iloc[-1] and 
                          rsi_series.iloc[-5] > rsi_series.iloc[-1])
    divergence_bearish = (price_series.iloc[-5] > price_series.iloc[-1] and 
                          rsi_series.iloc[-5] < rsi_series.iloc[-1])

    # MACD cross
    macd_cross_up = (macd_hist > 0 and macd_hist.shift(1).iloc[-1] <= 0)
    macd_cross_down = (macd_hist < 0 and macd_hist.shift(1).iloc[-1] >= 0)

    # Signal decision
    signal_key = "WAIT"
    reason = ""

    if divergence_bullish:
        signal_key = "BUY"
        reason = "🔥 Bullish divergence (price down, RSI up)"
    elif divergence_bearish:
        signal_key = "SELL"
        reason = "🔥 Bearish divergence (price up, RSI down)"
    elif rsi < 30 and macd_hist > 0:
        signal_key = "BUY"
        reason = "🟢 RSI oversold + MACD turning bullish"
    elif rsi > 70 and macd_hist < 0:
        signal_key = "SELL"
        reason = "🔴 RSI overbought + MACD turning bearish"
    elif price <= sr['support'] * 1.01 and rsi < 40:
        signal_key = "BUY"
        reason = "🟢 Price at support + RSI low"
    elif price >= sr['resistance'] * 0.99 and rsi > 60:
        signal_key = "SELL"
        reason = "🔴 Price at resistance + RSI high"
    elif macd_cross_up:
        signal_key = "BUY"
        reason = "🟢 MACD bullish crossover"
    elif macd_cross_down:
        signal_key = "SELL"
        reason = "🔴 MACD bearish crossover"
    elif trend_up and rsi < 50:
        signal_key = "BUY"
        reason = "🟢 Bullish trend + pullback (RSI < 50)"
    elif trend_down and rsi > 50:
        signal_key = "SELL"
        reason = "🔴 Bearish trend + bounce (RSI > 50)"
    else:
        reason = "📊 No clear signal – wait for better setup"

    # Score (information seulement)
    score = 0
    if trend_up:
        score += 2
    if macd_hist > 0:
        score += 1
    if rsi < 30:
        score += 2
    elif rsi < 60:
        score += 1

    return {
        "symbol": symbol,
        "price": price,
        "rsi": rsi,
        "macd": macd_val,
        "sma20": sma20,
        "sma50": sma50,
        "signal": signal_key,
        "reason": reason,
        "score": score,
        "support": sr["support"],
        "resistance": sr["resistance"],
        "data": data
    }

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

# ================= COMMANDES =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bitsure Teddy – Trading Bot*\n\n"
        "I analyze crypto, stocks, forex, and gold.\n"
        "Using Yahoo Finance + FCS API + RealMarketAPI (real-time).\n\n"
        "*Commands:*\n"
        "/analyse SYMBOL – Full analysis + chart\n"
        "/price SYMBOL – Current price only\n\n"
        "*Examples:*\n"
        "/analyse BTC-USD\n"
        "/analyse EURUSD=X\n"
        "/analyse USDBIF=X (USD → BIF)\n"
        "/analyse GC=F (gold)\n\n"
        "📊 *Not financial advice – just data.*",
        parse_mode='Markdown'
    )

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /analyse BTC-USD")
        return

    symbol = context.args[0].upper()
    status_msg = await update.message.reply_text(f"📊 Analyzing {symbol}...", parse_mode='Markdown')
    
    result = get_analysis(symbol)
    if not result:
        await status_msg.edit_text(f"❌ Symbol {symbol} not found.")
        return

    currency = get_display_currency(symbol)

    sr_text = ""
    if result['support'] > 0 and result['resistance'] > 0 and result['support'] != result['resistance']:
        sr_text = f"\n📊 *Key levels:*\n🟢 Support: {currency}{result['support']:.2f}\n🔴 Resistance: {currency}{result['resistance']:.2f}"

    msg = f"""
📈 *{result['symbol']}*
💰 {currency}{result['price']:.2f}{sr_text}

📊 RSI: {result['rsi']:.1f}
📊 MACD: {result['macd']:.4f}

📈 SMA20: {currency}{result['sma20']:.2f}
📉 SMA50: {currency}{result['sma50']:.2f}

🎯 *{result['signal']}*
📊 Score: {result['score']}/10

🧠 {result['reason']}
"""
    await status_msg.edit_text(msg, parse_mode='Markdown')
    await update.message.reply_text("📊 Generating chart...")
    chart = create_chart(symbol, result['data'])
    await update.message.reply_photo(chart)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price BTC-USD")
        return

    symbol = context.args[0].upper()
    status_msg = await update.message.reply_text(f"💰 Fetching price for {symbol}...", parse_mode='Markdown')
    
    # On essaie d'abord le prix temps réel
    if symbol in realtime_prices:
        price = realtime_prices[symbol]
    else:
        fcs_price = get_fcs_price(symbol)
        if fcs_price:
            price = fcs_price
        else:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if data.empty:
                await status_msg.edit_text(f"❌ Symbol {symbol} not found.")
                return
            price = data['Close'].iloc[-1]
    
    currency = get_display_currency(symbol)
    await status_msg.edit_text(f"💰 *{symbol}* : {currency}{price:.4f}", parse_mode='Markdown')

# ================= MAIN =================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyse", analyse))
    app.add_handler(CommandHandler("price", price))

    print("🚀 Bitsure Teddy Bot - Multi-API version started (Yahoo + FCS + RealMarket)")
    print("👉 Commands: /analyse, /price")
    app.run_polling()