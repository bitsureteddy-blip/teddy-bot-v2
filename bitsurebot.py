import logging
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from io import BytesIO

# ================= CONFIGURATION =================
TOKEN = os.environ.get('TELEGRAM_TOKEN', "TON_TOKEN_ICI")

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

# ================= GRAPHIQUE =================

def create_chart(symbol, data):
    """Crée un graphique avec prix, RSI, MACD"""
    
    # Préparer les données pour mplfinance
    df = data.copy()
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Calculer les indicateurs
    rsi = calculate_rsi(df['Close'])
    macd_line, signal_line, histogram = calculate_macd(df['Close'])
    bb_upper, bb_middle, bb_lower = calculate_bollinger(df['Close'])
    
    # Ajouter les bandes de Bollinger
    df['BB_upper'] = bb_upper
    df['BB_middle'] = bb_middle
    df['BB_lower'] = bb_lower
    
    # Créer les panels supplémentaires
    apds = [
        mpf.make_addplot(rsi, panel=1, color='purple', ylabel='RSI'),
        mpf.make_addplot(macd_line, panel=2, color='blue', ylabel='MACD'),
        mpf.make_addplot(signal_line, panel=2, color='red'),
        mpf.make_addplot(histogram, panel=2, type='bar', color='green', alpha=0.5),
        mpf.make_addplot(bb_upper, panel=0, color='gray', linestyle='--'),
        mpf.make_addplot(bb_lower, panel=0, color='gray', linestyle='--')
    ]
    
    # Créer le graphique
    fig, axes = mpf.plot(df, 
                          type='candle',
                          volume=False,
                          addplot=apds,
                          style='charles',
                          title=f'{symbol} - Dernières 100 périodes',
                          ylabel='Prix ($)',
                          returnfig=True)
    
    # Sauvegarder dans un buffer mémoire
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    plt.close()
    
    return buffer

# ================= ANALYSE =================

def get_market_data(symbol="BTC-USD"):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1mo", interval="1h")
    return data

def get_analysis(symbol):
    data = get_market_data(symbol)
    if data.empty:
        return None
    
    close = data['Close']
    current_price = close.iloc[-1]
    
    # RSI
    rsi = calculate_rsi(close)
    current_rsi = rsi.iloc[-1]
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(close)
    current_macd = macd_line.iloc[-1]
    current_signal = signal_line.iloc[-1]
    current_hist = histogram.iloc[-1]
    
    # Bandes de Bollinger
    bb_upper, bb_middle, bb_lower = calculate_bollinger(close)
    current_bb_upper = bb_upper.iloc[-1]
    current_bb_lower = bb_lower.iloc[-1]
    bb_position = (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower)
    
    # Moyennes mobiles
    sma20 = close.rolling(window=20).mean().iloc[-1]
    sma50 = close.rolling(window=50).mean().iloc[-1]
    
    # SIGNAL
    buy_score = 0
    sell_score = 0
    reasons = []
    
    # RSI
    if current_rsi < 30:
        buy_score += 2
        reasons.append(f"✅ RSI survendu ({current_rsi:.1f})")
    elif current_rsi > 70:
        sell_score += 2
        reasons.append(f"❌ RSI suracheté ({current_rsi:.1f})")
    
    # MACD
    if current_macd > current_signal and current_hist > 0:
        buy_score += 2
        reasons.append("✅ MACD haussier")
    elif current_macd < current_signal and current_hist < 0:
        sell_score += 2
        reasons.append("❌ MACD baissier")
    
    # Bollinger
    if bb_position < 0.1:
        buy_score += 1
        reasons.append("✅ Prix sous bande basse")
    elif bb_position > 0.9:
        sell_score += 1
        reasons.append("❌ Prix sur bande haute")
    
    # Décision
    if buy_score >= 2:
        signal = "🟢 ACHETER"
    elif sell_score >= 2:
        signal = "🔴 VENDRE"
    else:
        signal = "🟡 ATTENDRE"
    
    return {
        'symbol': symbol,
        'price': current_price,
        'rsi': current_rsi,
        'macd': current_macd,
        'macd_signal': current_signal,
        'bb_upper': current_bb_upper,
        'bb_lower': current_bb_lower,
        'sma20': sma20,
        'sma50': sma50,
        'signal': signal,
        'reasons': reasons,
        'data': data
    }

# ================= COMMANDES TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bitsure Teddy Bot - Version Premium*\n\n"
        "Commandes :\n"
        "/analyse SYMBOLE - Analyse + graphique\n"
        "/prix SYMBOLE - Prix uniquement\n\n"
        "Exemples :\n"
        "/analyse BTC-USD\n"
        "/analyse GC=F (or)\n"
        "/analyse AAPL",
        parse_mode='Markdown'
    )

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilisation: /analyse SYMBOLE\nExemple: /analyse BTC-USD")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"📊 Analyse de *{symbol}*...", parse_mode='Markdown')
    
    result = get_analysis(symbol)
    if not result:
        await update.message.reply_text(f"❌ Symbole '{symbol}' introuvable.")
        return
    
    # Message texte
    message = f"""
📈 *{result['symbol']}*
💰 Prix: ${result['price']:.2f}
📊 RSI: {result['rsi']:.1f}
📊 MACD: {result['macd']:.4f}
📈 SMA20: ${result['sma20']:.2f}
📉 SMA50: ${result['sma50']:.2f}

🎯 *{result['signal']}*
📝 {', '.join(result['reasons']) if result['reasons'] else 'Aucun signal fort'}
    """
    await update.message.reply_text(message, parse_mode='Markdown')
    
    # Envoi du graphique
    await update.message.reply_text("📊 *Génération du graphique...*", parse_mode='Markdown')
    chart = create_chart(symbol, result['data'])
    await update.message.reply_photo(photo=chart, caption=f"Graphique {symbol} - 30 jours")

async def prix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilisation: /prix SYMBOLE")
        return
    
    symbol = context.args[0].upper()
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    if data.empty:
        await update.message.reply_text(f"❌ Symbole '{symbol}' introuvable.")
        return
    
    price = data['Close'].iloc[-1]
    await update.message.reply_text(f"💰 *{symbol}* : ${price:.2f}", parse_mode='Markdown')

# ================= LANCEMENT =================

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyse", analyse))
    app.add_handler(CommandHandler("prix", prix))
    
    print("✅ Bitsure Teddy Bot - Version Premium démarrée !")
    print("👉 Commandes: /analyse SYMBOLE, /prix SYMBOLE")
    app.run_polling()