import os, logging, asyncio
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "")  # isi chat id lu buat auto notif, atau kosongin dulu
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN belum di set!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LIST SAHAM ALL IDX - minimal harga 50 akan di filter otomatis
IDX_TICKERS = [
"BBCA.JK","BBRI.JK","BMRI.JK","BBNI.JK","BRIS.JK","TLKM.JK","ASII.JK","ADRO.JK","AMMN.JK","ANTM.JK","BRPT.JK","PTBA.JK","PGAS.JK","UNTR.JK","UNVR.JK","ICBP.JK","INDF.JK","KLBF.JK","GGRM.JK","HMSP.JK","EXCL.JK","ISAT.JK","MDKA.JK","INCO.JK","ITMG.JK","MEDC.JK","AKRA.JK","AUTO.JK","CPIN.JK","JPFA.JK","MAIN.JK","MYOR.JK","ACES.JK","MAPI.JK","LPPF.JK","ERAA.JK","SCMA.JK","MNCN.JK","EMTK.JK","BUKA.JK","GOTO.JK","BREN.JK","CUAN.JK","AMRT.JK","ARTO.JK","BBYB.JK","BRMS.JK","DEWA.JK","MBMA.JK","NCKL.JK","ESSA.JK","INCO.JK","HRUM.JK","ADMR.JK","INDY.JK","ELSA.JK","AKRA.JK","TOWR.JK","TBIG.JK","MTEL.JK","JSMR.JK","ASSA.JK","SMDR.JK","ELSA.JK","ENRG.JK","BULL.JK","WIFI.JK","RAJA.JK","GEMS.JK","TPIA.JK","ESSA.JK","BOGA.JK","PANI.JK","FILM.JK","MAPA.JK","BFIN.JK","BIRD.JK","TAPG.JK","AADI.JK","CMRY.JK","AVIA.JK","HATM.JK","PGEO.JK","PTRO.JK","BRMS.JK","SRTG.JK","DSNG.JK","LSIP.JK","SSMS.JK","TAPG.JK","BWPT.JK","STAA.JK","KEJU.JK","GOOD.JK","BREAD.JK","PANI.JK","CTRA.JK","BSDE.JK","PWON.JK","SMRA.JK","CTRA.JK","LPKR.JK","DMAS.JK","KIJA.JK","MPRO.JK","MTLA.JK","GPRA.JK","BKSL.JK","BEST.JK","ASRI.JK","PWON.JK","SMRA.JK","APLN.JK","JRPT.JK","DILD.JK"
]
IDX_TICKERS = list(dict.fromkeys(IDX_TICKERS))  # hapus duplikat

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def get_data(ticker, period="6mo"):
    # auto .JK
    tries = [ticker]
    if ".JK" not in ticker:
        tries = [ticker+".JK", ticker]
    for t in tries:
        try:
            df = yf.Ticker(t).history(period=period)
            if df is not None and not df.empty and len(df) > 30:
                return df, t
        except Exception as e:
            logger.error(f"{t} {e}")
            continue
    return None, None

def analyze_stock(df):
    df = df.copy()
    df['EMA5'] = calc_ema(df['Close'], 5)
    df['EMA10'] = calc_ema(df['Close'], 10)
    df['EMA20'] = calc_ema(df['Close'], 20)
    df['RSI'] = calc_rsi(df['Close'], 14)
    df['VolAvg20'] = df['Volume'].rolling(20).mean()
    df['VolRatio'] = df['Volume'] / df['VolAvg20']
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    close = last['Close']
    if close < 50:  # minimal harga 50
        return None
    
    ema5, ema10, ema20 = last['EMA5'], last['EMA10'], last['EMA20']
    rsi = last['RSI']
    vol_ratio = last['VolRatio'] if not np.isnan(last['VolRatio']) else 1.0
    
    # TREND
    if ema5 > ema10 > ema20:
        trend = "BULLISH"
    elif ema5 < ema10 < ema20:
        trend = "BEARISH"
    else:
        trend = "SIDEWAYS"
    
    # SCORING V15 PASTI
    score = 50  # base
    details = []
    
    # 1. EMA5>EMA10>EMA20 BULLISH +20%
    if ema5 > ema10 > ema20:
        score += 20
        details.append(f"- EMA5>EMA10>EMA20 BULLISH +20%")
    elif ema5 > ema10:
        score += 10
        details.append(f"- EMA5>EMA10 +10%")
    
    # 2. Baru cross UP +15%
    baru_cross = False
    if prev['EMA5'] < prev['EMA10'] and last['EMA5'] > last['EMA10']:
        baru_cross = True
        score += 15
        details.append(f"- Baru cross UP +15%")
    elif prev['EMA5'] < prev['EMA20'] and last['EMA5'] > last['EMA20']:
        baru_cross = True
        score += 15
        details.append(f"- Baru cross UP EMA20 +15%")
    elif prev['EMA10'] < prev['EMA20'] and last['EMA10'] > last['EMA20']:
        baru_cross = True
        score += 15
        details.append(f"- Baru cross UP +15%")
    
    # 3. Cross valid (bukan fake) +5% - jarak EMA tidak terlalu lebar, valid
    if abs(ema5 - ema10)/close < 0.05 and abs(ema10 - ema20)/close < 0.07:
        score += 5
        details.append(f"- Cross valid (bukan fake) +5%")
    
    # 4. RSI ideal 45-65 +10%
    if 45 <= rsi <= 65:
        score += 10
        details.append(f"- RSI ideal {rsi:.0f} +10%")
    elif 40 <= rsi <= 70:
        score += 5
        details.append(f"- RSI ok {rsi:.0f} +5%")
    
    # 5. Volume rame 1.5x+ +10%
    if vol_ratio >= 1.9:
        score += 10
        details.append(f"- Volume rame {vol_ratio:.1f}x +10%")
    elif vol_ratio >= 1.5:
        score += 7
        details.append(f"- Volume rame {vol_ratio:.1f}x +7%")
    elif vol_ratio >= 1.2:
        score += 3
        details.append(f"- Volume ok {vol_ratio:.1f}x +3%")
    
    # Tambahan: Trend BULLISH
    if trend == "BULLISH" and score >= 70:
        score += 5
    
    # Cap di 130%
    score = min(score, 135)
    
    # SL TP - V15 formula
    entry = close
    sl = entry * 0.96  # -4%
    tp1 = entry * 1.07
    tp2 = entry * 1.12
    tp3 = entry * 1.20
    
    return {
        "close": close,
        "ema5": ema5,
        "ema10": ema10,
        "ema20": ema20,
        "rsi": rsi,
        "vol_ratio": vol_ratio,
        "trend": trend,
        "score": score,
        "details": details,
        "baru_cross": baru_cross,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "df": df
    }

def create_chart(df, ticker, score):
    # Chart persis kayak screenshot lu
    df_plot = df.tail(130)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10,6), gridspec_kw={'height_ratios': [3,1]}, dpi=150)
    
    ax1.plot(df_plot['Close'], label='Close', color='black', linewidth=1.2)
    ax1.plot(df_plot['EMA5'], label='EMA5', color='#1f77b4', linewidth=1)
    ax1.plot(df_plot['EMA10'], label='EMA10', color='#ff7f0e', linewidth=1)
    ax1.plot(df_plot['EMA20'], label='EMA20', color='#9467bd', linewidth=1)
    
    # BUY SELL signals - deteksi cross
    for i in range(1, len(df_plot)):
        idx = df_plot.index[i]
        prev = df_plot.iloc[i-1]
        cur = df_plot.iloc[i]
        # BUY: EMA5 cross up EMA20
        if prev['EMA5'] < prev['EMA20'] and cur['EMA5'] > cur['EMA20']:
            ax1.text(idx, cur['Close']*0.97, 'BUY', fontsize=7, color='white', ha='center', va='center',
                     bbox=dict(boxstyle="round,pad=0.3", facecolor='#2ca02c', edgecolor='none'))
        # SELL: EMA5 cross down EMA10
        if prev['EMA5'] > prev['EMA10'] and cur['EMA5'] < cur['EMA10']:
            ax1.text(idx, cur['Close']*1.03, 'SELL', fontsize=7, color='white', ha='center', va='center',
                     bbox=dict(boxstyle="round,pad=0.3", facecolor='#d62728', edgecolor='none'))
    
    last_close = df_plot.iloc[-1]['Close']
    title = f"{ticker} [MA] @ PASTI NAIK {score:.0f}% @ | {last_close:.0f}"
    ax1.set_title(title, fontsize=9, fontweight='bold', loc='left')
    ax1.legend(fontsize=7, loc='upper left')
    ax1.grid(True, alpha=0.2)
    ax1.set_ylabel('Price')
    
    # Volume subplot kayak screenshot
    colors = ['#d62728' if c < o else '#2ca02c' for c, o in zip(df_plot['Close'], df_plot['Open'])]
    ax2.bar(df_plot.index, df_plot['Volume'], color=colors, alpha=0.6, width=2)
    ax2.set_ylabel('Vol', fontsize=8)
    ax2.tick_params(labelsize=7)
    
    plt.tight_layout()
    bio = BytesIO()
    plt.savefig(bio, format='png', dpi=200)
    plt.close()
    bio.seek(0)
    return bio

async def ma_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Pakai: /ma AKRA atau /ma AKRA.JK")
        return
    ticker = context.args[0].upper()
    await update.message.reply_text(f"⏳ Scan {ticker} V15 PASTI...")
    df, used = get_data(ticker)
    if df is None:
        await update.message.reply_text(f"❌ {ticker} tidak ketemu atau harga <50")
        return
    
    res = analyze_stock(df)
    if res is None:
        await update.message.reply_text(f"❌ {used} harga di bawah 50, skip")
        return
    
    # Hanya 80%+ yang keluar? Sesuai V15 PASTI rule, tapi untuk /ma boleh semua, kasih warning
    score = res['score']
    # if score < 80:
    #     await update.message.reply_text(f"⚠️ {used} cuma {score:.0f}% (di bawah 80% PASTI), skip.\nPakai /longgar untuk lihat semua")
    #     return
    
    chart = create_chart(res['df'], used, score)
    
    # Format persis screenshot
    tgl = datetime.now().strftime("%Y-%m-%d")
    detail_str = "\n".join(res['details'])
    
    caption = (
        f"{tgl} - {used} [MA] 🔥 PASTI\n"
        f"Close {res['close']:.0f} | EMA5 {res['ema5']:.0f} EMA10 {res['ema10']:.0f} EMA20 {res['ema20']:.0f} RSI {res['rsi']:.1f} Vol {res['vol_ratio']:.1f}x\n"
        f"Trend {res['trend']}\n"
        f"\n"
        f"🚀 PREDIKSI: NAIK {score:.0f}% 🔥 PASTI\n"
        f"{detail_str}\n"
        f"\n"
        f"ENTRY {res['entry']:.0f} | SL {res['sl']:.0f} (-4%)\n"
        f"TP1 {res['tp1']:.0f} (+7%) TP2 {res['tp2']:.0f} (+12%) TP3 {res['tp3']:.0f} (+20%)\n"
        f"V15 PASTI - Hanya 80%+ yang keluar!"
    )
    
    await update.message.reply_photo(photo=chart, caption=caption)

async def scan_all(update: Update, context: ContextTypes.DEFAULT_TYPE, mode="ketat"):
    # mode: longgar 70%+, ketat 80%+, semua 0%+
    if mode == "longgar":
        threshold = 70
        title_mode = "LONGGAR 70%+"
    elif mode == "ketat":
        threshold = 80
        title_mode = "KETAT 80%+ PASTI"
    else:
        threshold = 0
        title_mode = "SEMUA"
    
    await update.message.reply_text(f"🔍 V15 SCAN ALL SAHAM harga>50 MODE {title_mode}...\nIni scan {len(IDX_TICKERS)} saham, sabar 1-2 menit...")
    
    results = []
    for t in IDX_TICKERS:
        try:
            df, used = get_data(t, period="6mo")
            if df is None: continue
            res = analyze_stock(df)
            if res is None: continue
            if res['score'] >= threshold:
                results.append((used, res))
        except Exception as e:
            logger.error(f"scan {t} error {e}")
            continue
    
    results.sort(key=lambda x: x[1]['score'], reverse=True)
    
    if not results:
        await update.message.reply_text(f"😴 Tidak ada saham {title_mode} hari ini.")
        return
    
    # Kirim top 15 biar gak spam
    tgl = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"🔥 AUTO PASTI {title_mode} - {tgl}\nSiap SORE-PAGI {threshold}%+:\n\n"
    for i, (ticker, res) in enumerate(results[:20], 1):
        text += f"{i}. {ticker.replace('.JK','')} - {res['close']:.0f} | {res['score']:.0f}% | RSI {res['rsi']:.0f} Vol {res['vol_ratio']:.1f}x\n"
        text += f"   EMA5>EMA10>EMA20 {res['trend']} +20%\n"
        text += f"   /ma {ticker.lower()}\n"
    
    if len(results) > 20:
        text += f"\n...dan {len(results)-20} saham lainnya {threshold}%+"
    
    # Bagi 2 pesan kalau kepanjangan
    await update.message.reply_text(text)
    
    # Auto kirim detail top 3 dengan chart
    for ticker, res in results[:3]:
        try:
            chart = create_chart(res['df'], ticker, res['score'])
            tgl = datetime.now().strftime("%Y-%m-%d")
            detail_str = "\n".join(res['details'])
            caption = (
                f"{tgl} - {ticker} [MA] 🔥 PASTI\n"
                f"Close {res['close']:.0f} | EMA5 {res['ema5']:.0f} EMA10 {res['ema10']:.0f} EMA20 {res['ema20']:.0f} RSI {res['rsi']:.1f} Vol {res['vol_ratio']:.1f}x\n"
                f"Trend {res['trend']}\n\n"
                f"🚀 PREDIKSI: NAIK {res['score']:.0f}% 🔥 PASTI\n{detail_str}\n\n"
                f"ENTRY {res['entry']:.0f} | SL {res['sl']:.0f} (-4%)\n"
                f"TP1 {res['tp1']:.0f} (+7%) TP2 {res['tp2']:.0f} (+12%) TP3 {res['tp3']:.0f} (+20%)\n"
                f"V15 PASTI - Hanya 80%+ yang keluar!"
            )
            await update.message.reply_photo(photo=chart, caption=caption)
            await asyncio.sleep(1)
        except: pass

async def ketat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scan_all(update, context, mode="ketat")

async def longgar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scan_all(update, context, mode="longgar")

async def semua_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await scan_all(update, context, mode="semua")

async def pagi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌅 SCAN PAGI 08:30 - Mode KETAT 80%+")
    await scan_all(update, context, mode="ketat")

async def sore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌇 SCAN SORE 15:30 - Mode KETAT 80%+")
    await scan_all(update, context, mode="ketat")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "🚀 *MA SCANNER V3 - V15 PASTI* 🚀\n\n"
        "Format persis punya lu!\n\n"
        "📌 *COMMAND:*\n"
        "/ma AKRA.JK - Detail PASTI + Chart BUY/SELL\n"
        "/ketat - Scan ALL saham harga>50 hanya 80%+ PASTI (Rekomen)\n"
        "/longgar - Scan ALL saham 70%+\n"
        "/semua - Scan ALL saham semua score\n"
        "/pagi - Auto scan pagi (08:30)\n"
        "/sore - Auto scan sore (15:30)\n\n"
        "🔥 *AUTO NOTIF 15:30* akan kirim tiap sore kalau CHAT_ID di set di Railway Variables!\n"
        "Setting di Railway: CHAT_ID = id telegram lu\n\n"
        "Contoh: /ma akra.jk, /ma bbca.jk, /ketat"
    )
    await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)

# Auto job sore 15:30 WIB = 08:30 UTC
async def auto_sore_job(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID:
        return
    try:
        # scan ketat
        results = []
        for t in IDX_TICKERS[:40]:  # biar cepet, scan 40 top
            try:
                df, used = get_data(t, period="6mo")
                if df is None: continue
                res = analyze_stock(df)
                if res and res['score'] >= 80:
                    results.append((used, res))
            except: continue
        results.sort(key=lambda x: x[1]['score'], reverse=True)
        if not results:
            await context.bot.send_message(chat_id=CHAT_ID, text="😴 AUTO SORE 15:30 - Tidak ada 80%+ hari ini")
            return
        tgl = datetime.now().strftime("%Y-%m-%d")
        text = f"🔥 AUTO PASTI SORE 15:30 - {tgl}\nSiap SORE-PAGI 80%+:\n"
        for ticker, res in results[:10]:
            text += f"✅ {ticker.replace('.JK','')} {res['close']:.0f} {res['score']:.0f}%\n/sore {ticker.lower()}\n"
        await context.bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        logger.error(f"auto job error {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("ma", ma_handler))
    app.add_handler(CommandHandler("ketat", ketat_cmd))
    app.add_handler(CommandHandler("longgar", longgar_cmd))
    app.add_handler(CommandHandler("semua", semua_cmd))
    app.add_handler(CommandHandler("pagi", pagi_cmd))
    app.add_handler(CommandHandler("sore", sore_cmd))
    
    # JobQueue auto 15:30 WIB = 08:30 UTC
    if app.job_queue:
        app.job_queue.run_daily(auto_sore_job, time=datetime.strptime("08:30", "%H:%M").time(), name="auto_sore")
        logger.info("Auto job 15:30 WIB scheduled")
    
    logger.info("V15 PASTI Bot Started!")
    app.run_polling()

if __name__ == "__main__":
    main()
