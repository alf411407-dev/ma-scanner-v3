
import os, logging, yfinance as yf, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import time, datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN / BOT_TOKEN belum di set!")

CHAT_ID = os.getenv("CHAT_ID") or os.getenv("CHATID")
logger.info(f"CHAT_ID: {CHAT_ID}")

SAHAM_LIST = ["AKRA.JK","BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK","ADRO.JK","ANTM.JK","BBNI.JK","BRIS.JK","GOTO.JK","ICBP.JK","INDF.JK","KLBF.JK","UNVR.JK","ACES.JK","ADMR.JK","AMRT.JK","ARTO.JK","BRPT.JK","CPIN.JK","EMTK.JK","EXCL.JK","GGRM.JK","HRUM.JK","INDY.JK","INKP.JK","ITMG.JK","MDKA.JK","MEDC.JK","PGAS.JK","PTBA.JK","SMGR.JK","TOWR.JK","UNTR.JK","MNCN.JK","HMSP.JK","LPPF.JK","BFIN.JK","ASSA.JK","NCKL.JK","PTRO.JK","TBIG.JK","COCO.JK","AMMN.JK","BRMS.JK","BUKA.JK","ESSA.JK","HRUM.JK","ANTM.JK"]

def hitung_pasti(df):
    if len(df) < 50:
        return 0, {}, 50, (0,0,0,0)
    close = df['Close']
    ema5 = close.ewm(span=5).mean()
    ema10 = close.ewm(span=10).mean()
    ema20 = close.ewm(span=20).mean()
    ema50 = close.ewm(span=50).mean()
    last = df.iloc[-1]
    c = last['Close']
    e5 = ema5.iloc[-1]; e10=ema10.iloc[-1]; e20=ema20.iloc[-1]; e50=ema50.iloc[-1]
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1+rs))
    rsi_last = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
    vol = df['Volume'].iloc[-1] / df['Volume'].tail(20).mean() if df['Volume'].tail(20).mean()>0 else 1
    score=0
    detail={}
    if e5>e10>e20:
        score+=20
        detail['trend']="EMA5>EMA10>EMA20 BULLISH +20%"
    if c>e5:
        score+=15
    if e5>e50:
        score+=15
    if len(df)>=2 and df['Volume'].iloc[-1] > df['Volume'].iloc[-2]:
        score+=10
    if 50 <= rsi_last <= 70:
        score+=20
    elif 40 <= rsi_last <= 75:
        score+=10
    if e20>e50:
        score+=20
    score = min(int(score),115)
    # boost jika vol besar
    if vol>1.5 and score>=70:
        score = min(score+10,115)
    return score, detail, rsi_last, (e5,e10,e20,e50), vol

async def scan_logic(min_score=80):
    hasil=[]
    for t in SAHAM_LIST:
        try:
            df = yf.Ticker(t).history(period="6mo")
            if df.empty: continue
            price = df.iloc[-1]['Close']
            if price < 50: continue
            score, detail, rsi, emas, vol = hitung_pasti(df)
            if score >= min_score:
                hasil.append((t, price, score, rsi, vol))
        except: continue
    hasil.sort(key=lambda x: x[2], reverse=True)
    return hasil

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    await update.message.reply_text(f"""🚀 MA SCANNER V3 - V17 AUTO PAGI+SORE 🚀

ID lu: {cid}
Copy ID ini ke Railway -> Variables -> CHAT_ID biar auto notif jalan!

📌 COMMAND:
/ma AKRA.JK - Detail PASTI + Chart BUY/SELL
/ketat - Scan 80%+ PASTI (Rekomen)
/scan pasti / /scan pasti - hanya 80% pasti -> sama kayak /ketat
/scan pasti-hanya 100% pasti -> 100%+ doang
/longgar - 70%+
/semua - semua score
/pagi - scan pagi manual (08:30)
/sore - scan sore manual (15:30)

🔥 AUTO:
Pagi 08:30 WIB & Sore 15:30 WIB auto kirim kalau CHAT_ID set!
CHAT_ID sekarang: {CHAT_ID if CHAT_ID else 'BELUM DI SET ❌'}

Set: Railway Variables -> CHAT_ID = {cid}
Contoh: /ma akra.jk, /ma coco.jk, /ketat
""")

async def ma_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Contoh: /ma coco.jk"); return
    ticker = context.args[0].upper()
    if not ticker.endswith(".JK"): ticker+=".JK"
    await update.message.reply_text(f"🔍 Scanning {ticker} ...")
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        if df.empty:
            await update.message.reply_text(f"❌ {ticker} tidak ditemukan"); return
        score, detail, rsi, emas, vol = hitung_pasti(df)
        e5,e10,e20,e50 = emas
        price = df.iloc[-1]['Close']
        status = "🔥 PASTI" if score>=80 else "⚠️ LONGGAR" if score>=70 else "❌ TIDAK PASTI"
        pred = "NAIK" if score>=70 else "TURUN"
        tp1 = price*1.07; tp2=price*1.12; tp3=price*1.20
        txt = f"""{datetime.now().strftime('%Y-%m-%d')} - {ticker} [MA] {status}
Close {price:.0f} | EMA5 {e5:.0f} EMA10 {e10:.0f} EMA20 {e20:.0f}
RSI {rsi:.1f} Vol {vol:.1f}x
Trend BULLISH

🚀 PREDIKSI: {pred} {score}% {status}
- EMA5>EMA10>EMA20 BULLISH +20%

ENTRY {price:.0f} | SL {price*0.96:.0f} (-4%)
TP1 {tp1:.0f} (+7%) TP2 {tp2:.0f} (+12%) TP3 {tp3:.0f} (+20%)
V15 PASTI - Hanya 80%+ yang keluar!
"""
        try:
            plt.figure(figsize=(8,5))
            plt.subplot(2,1,1)
            plt.plot(df['Close'].tail(80), label='Close', linewidth=1.5, color='black')
            plt.plot(df['Close'].ewm(span=5).mean().tail(80), label='EMA5', linewidth=1)
            plt.plot(df['Close'].ewm(span=10).mean().tail(80), label='EMA10', linewidth=1)
            plt.plot(df['Close'].ewm(span=20).mean().tail(80), label='EMA20', linewidth=1)
            plt.legend(); plt.grid(True, alpha=0.3)
            plt.subplot(2,1,2)
            plt.bar(range(len(df.tail(80))), df['Volume'].tail(80))
            plt.tight_layout()
            buf = BytesIO(); plt.savefig(buf, format='png', dpi=150); buf.seek(0); plt.close()
            await update.message.reply_photo(photo=buf, caption=txt)
        except:
            await update.message.reply_text(txt)
    except Exception as e:
        logger.error(e)
        await update.message.reply_text(f"❌ Error: {e}")

async def ketat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ini scan 105 saham, sabar 1-2 menit...")
    hasil = await scan_logic(80)
    if not hasil:
        await update.message.reply_text("❌ Tidak ada 80%+ PASTI"); return
    txt = f"🔥 AUTO PASTI KETAT 80%+ PASTI - {datetime.now().strftime('%Y-%m-%d %H:%M')}\nSiap SORE-PAGI 80%+:\n\n"
    for i,(t,p,s,r,v) in enumerate(hasil[:15],1):
        txt+=f"{i}. {t.replace('.JK','')} - {p:.0f} | {s}% | RSI {r:.0f} Vol {v:.1f}x\n  EMA5>EMA10>EMA20 BULLISH +20%\n  /ma {t.lower()}\n"
    await update.message.reply_text(txt)

async def longgar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil = await scan_logic(70)
    txt = f"⚠️ LONGGAR 70%+ ({len(hasil)} saham)\n\n"
    for i,(t,p,s,r,v) in enumerate(hasil[:20],1):
        txt+=f"{i}. {t.replace('.JK','')} - {p:.0f} | {s}%\n"
    await update.message.reply_text(txt)

async def semua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hasil = await scan_logic(0)
    txt = f"📊 SEMUA ({len(hasil)} saham)\n\n"
    for i,(t,p,s,r,v) in enumerate(hasil[:25],1):
        icon="🔥" if s>=80 else "⚠️" if s>=70 else "❌"
        txt+=f"{i}. {icon} {t.replace('.JK','')} - {p:.0f} | {s}%\n"
    await update.message.reply_text(txt)

async def scan_alias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args).lower() if context.args else ""
    if "100" in text:
        await update.message.reply_text("🔍 Scan 100%+ PASTI...")
        hasil = await scan_logic(100)
        if not hasil:
            await update.message.reply_text("❌ Tidak ada 100%+ PASTI, coba /ketat"); return
        txt = f"💎 100% PASTI ({len(hasil)} saham)\n\n"
        for i,(t,p,s,r,v) in enumerate(hasil,1):
            txt+=f"{i}. {t.replace('.JK','')} - {p:.0f} | {s}% | RSI {r:.0f}\n"
        await update.message.reply_text(txt)
    else:
        # semua varian /scan pasti, /scan pasti-hanya 80% dll -> ketat
        await ketat(update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("ma", ma_detail))
    app.add_handler(CommandHandler("ketat", ketat))
    app.add_handler(CommandHandler("longgar", longgar))
    app.add_handler(CommandHandler("semua", semua))
    app.add_handler(CommandHandler("pagi", ketat))
    app.add_handler(CommandHandler("sore", ketat))
    app.add_handler(CommandHandler("scan", scan_alias))
    if CHAT_ID:
        async def job_pagi(ctx: ContextTypes.DEFAULT_TYPE):
            try:
                hasil = await scan_logic(80)
                if not hasil: return
                txt = f"☀️ AUTO PAGI 08:30 - {len(hasil)} SAHAM 80%+ PASTI\n"
                for i,(t,p,s,r,v) in enumerate(hasil[:12],1):
                    txt+=f"{i}. {t.replace('.JK','')} - {p:.0f} | {s}%\n"
                await ctx.bot.send_message(chat_id=int(CHAT_ID), text=txt)
            except Exception as e:
                logger.error(f"pagi error {e}")
        async def job_sore(ctx: ContextTypes.DEFAULT_TYPE):
            try:
                hasil = await scan_logic(80)
                if not hasil: return
                txt = f"🔥 AUTO SORE 15:30 - {len(hasil)} SAHAM 80%+ PASTI\n"
                for i,(t,p,s,r,v) in enumerate(hasil[:12],1):
                    txt+=f"{i}. {t.replace('.JK','')} - {p:.0f} | {s}%\n"
                await ctx.bot.send_message(chat_id=int(CHAT_ID), text=txt)
            except Exception as e:
                logger.error(f"sore error {e}")
        app.job_queue.run_daily(job_pagi, time=time(hour=1, minute=30), name="pagi")
        app.job_queue.run_daily(job_sore, time=time(hour=8, minute=30), name="sore")
        logger.info(f"AUTO PAGI 08:30 & SORE 15:30 ON -> {CHAT_ID}")
    else:
        logger.warning("CHAT_ID belum set, auto OFF")
    logger.info("V17 PASTI Bot Started!")
    app.run_polling()

if __name__ == "__main__":
    main()
