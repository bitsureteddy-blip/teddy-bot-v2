import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIGURATION =================
TOKEN = "8616503037:AAFWEZB1w2ml3_OumTwEZLIHAf7zdOyXCpk"  # REMPLACE PAR TON VRAI TOKEN !

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= FONCTIONS D'ANALYSE =================

def get_market_data(symbol="BTC-USD"):
    """Récupère les données"""
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1mo", interval="1h")
    return data

def calculate_rsi(data, period=14):
    """Calcule le RSI"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_analysis(symbol):
    """Analyse complète"""
    data = get_market_data(symbol)
    if data.empty:
        return None
    
    close = data['Close']
    current_price = close.iloc[-1]
    
    # RSI
    rsi = calculate_rsi(close)
    current_rsi = rsi.iloc[-1]
    
    # Moyennes mobiles
    sma20 = close.rolling(window=20).mean().iloc[-1]
    sma50 = close.rolling(window=50).mean().iloc[-1]
    
    # Signal
    if current_rsi < 30:
        signal = "🟢 ACHETER"
        reason = f"RSI survendu ({current_rsi:.1f})"
    elif current_rsi > 70:
        signal = "🔴 VENDRE"
        reason = f"RSI suracheté ({current_rsi:.1f})"
    elif current_price > sma20 and current_price > sma50:
        signal = "🟡 TENDANCE HAUSSIÈRE"
        reason = "Prix au-dessus des moyennes mobiles"
    elif current_price < sma20 and current_price < sma50:
        signal = "🟠 TENDANCE BAISSIÈRE"
        reason = "Prix en dessous des moyennes mobiles"
    else:
        signal = "⚪ ATTENDRE"
        reason = "Pas de signal clair"
    
    return {
        'symbol': symbol,
        'price': current_price,
        'rsi': current_rsi,
        'sma20': sma20,
        'sma50': sma50,
        'signal': signal,
        'reason': reason
    }

# ================= COMMANDES TELEGRAM =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bitsure Teddy Bot*\n\n"
        "Commandes disponibles :\n"
        "/analyse BTC-USD - Bitcoin\n"
        "/analyse ETH-USD - Ethereum\n"
        "/analyse AAPL - Apple\n"
        "/analyse EURUSD=X - Euro/Dollar\n"
        "/analyse GC=F - Or\n\n"
        "Exemple: /analyse BTC-USD",
        parse_mode='Markdown'
    )

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilisation: /analyse SYMBOLE\nExemple: /analyse BTC-USD")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"📊 Analyse de *{symbol}* en cours...", parse_mode='Markdown')
    
    result = get_analysis(symbol)
    if not result:
        await update.message.reply_text(f"❌ Symbole '{symbol}' introuvable.")
        return
    
    message = f"""
📈 *{result['symbol']}*
💰 Prix: ${result['price']:.2f}
📊 RSI: {result['rsi']:.1f}
📈 SMA20: ${result['sma20']:.2f}
📉 SMA50: ${result['sma50']:.2f}

🎯 *{result['signal']}*
📝 {result['reason']}

⚠️ Simple aide à la décision
    """
    await update.message.reply_text(message, parse_mode='Markdown')

# ================= LANCEMENT =================

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyse", analyse))
    
    print("✅ Bitsure Teddy Bot démarré !")
    print("👉 Va parler à ton bot sur Telegram")
    app.run_polling()