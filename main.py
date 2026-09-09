import os
import logging
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN belum di set di Variables!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot MA Scanner AKRA 115% ANTI TIDUR AKTIF!\n\n"
        "Perintah:\n"
        "/scan AKRA.JK - scan MA\n"
        "/help - bantuan"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Contoh: /scan AKRA.JK")
            return
        
        ticker = context.args[0].upper()
        if not ticker.endswith(".JK"):
            ticker += ".JK"
            
        await update.message.reply_text(f"🔍 Scanning {ticker} ...")
        
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if df.empty:
            await update.message.reply_text(f"❌ Data {ticker} tidak ditemukan!")
            return

        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean()
        
        last = df.iloc[-1]
        price = last['Close']
        ma20 = last['MA20']
        ma50 = last['MA50']
        ma200 = last['MA200']
        
        # Logic sinyal
        if price > ma20 and ma20 > ma50:
            signal = "🚀 BULLISH KUAT"
        elif price > ma50:
            signal = "📈 BULLISH"
        elif price < ma20 and ma20 < ma50:
            signal = "🔻 BEARISH KUAT"
        else:
            signal = "📉 BEARISH"
        
        msg = f"""
📊 {ticker} - MA Scanner

💰 Harga: {price:.0f}
MA20: {ma20:.0f}
MA50: {ma50:.0f}
MA200: {ma200:.0f}

Sinyal: {signal}

115% Anti Tidur ✅
"""
        await update.message.reply_text(msg)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {e}")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ketik /scan AKRA.JK untuk scan saham!")

def main():
    # INI YANG BENER - ADA .build() DI BELAKANG!
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("help", help_cmd))
    
    logger.info("Bot Started - ANTI TIDUR MODE ON")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
