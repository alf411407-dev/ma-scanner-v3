import os, io, yfinance as yf, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TOP = ["AKRA","BBCA","BBRI","BMRI","TLKM","ASII","GOTO","ADRO","ANTM","BRPT","BBNI","UNTR","ICBP"]

def calc_ema(s,p): return s.ewm(span=p, adjust=False).mean()
def get_data(sym):
    for s in [sym, sym+".JK", sym.upper()+".JK"]:
        try:
            df=yf.download(s, period="6mo", interval="1d", auto_adjust=True, progress=False)
            if df is not None and not df.empty and len(df)>30: return df,s
        except: continue
    return None,sym

def quick(ticker):
    try:
        df,_=get_data(ticker)
        df['MA20']=df['Close'].rolling(20).mean(); df['MA50']=df['Close'].rolling(50).mean()
        l=df.iloc[-1]; sig="BUY" if l['Close']>l['MA20']>l['MA50'] else "HOLD"
        return f"{ticker}: {l['Close']:.0f} | MA20 {l['MA20']:.0f} | MA50 {l['MA50']:.0f} -> {sig}"
    except: return None

async def ma(update, ctx):
    if not ctx.args:
        await update.message.reply_text("Pakai: /ma AKRA (AKRA doang) /ma BBCA /scan all")
        return
    s=ctx.args[0].upper()
    if s=="ALL":
        await update.message.reply_text("Pakai /scan all"); return
    load=await update.message.reply_text(f"Scanning {s}...")
    df,final=get_data(s)
    if df is None:
        await load.edit_text(f"No data {s}"); return
    try:
        df['EMA5']=calc_ema(df['Close'],5); df['EMA10']=calc_ema(df['Close'],10); df['EMA20']=calc_ema(df['Close'],20)
        plot=df.tail(90).copy()
        fig,(a1,a2)=plt.subplots(2,1,figsize=(12,8),gridspec_kw={'height_ratios':[4,1]},sharex=True)
        for idx,row in enumerate(plot.iterrows()):
            r=row[1]; o=r['Open']; c=r['Close']; h=r['High']; lo=r['Low']; col='#089981' if c>=o else '#F23645'
            a1.plot([idx,idx],[lo,h],color=col,linewidth=1)
            bh=abs(c-o); bb=min(o,c)
            rect=Rectangle((idx-0.3,bb),0.6,max(bh,0.1),facecolor=col,edgecolor=col); a1.add_patch(rect)
            a2.bar(idx,r['Volume'],color=col,alpha=0.5,width=0.6)
        x=range(len(plot)); a1.plot(x,plot['EMA5'],color='#2962FF',label='EMA5'); a1.plot(x,plot['EMA10'],color='#FF9800',label='EMA10'); a1.plot(x,plot['EMA20'],color='#9C27B0',label='EMA20')
        a1.legend(); a1.set_title(f"{final} Close {plot['Close'].iloc[-1]:.2f}")
        buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=200,bbox_inches='tight'); plt.close(fig); buf.seek(0)
        await update.message.reply_photo(photo=buf,caption=f"{final} - Ketik /scan all buat all saham")
        await load.delete()
    except Exception as e: await load.edit_text(f"Error {e}")

async def scan(update, ctx):
    if not ctx.args: await update.message.reply_text("Pakai /scan AKRA atau /scan all"); return
    k=ctx.args[0].upper()
    if k=="ALL":
        await update.message.reply_text(f"Scanning {len(TOP)} saham...")
        hasil=[quick(s) for s in TOP]; hasil=[h for h in hasil if h]
        await update.message.reply_text("📊 ALL SAHAM:\n\n"+"\n".join(hasil))
    else:
        r=quick(k); await update.message.reply_text(r or f"Gagal {k}")

async def start(update, ctx): await update.message.reply_text("AKRA V3 Aktif! /ma AKRA (AKRA doang) /ma BBCA /scan all (all saham)")
def main():
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("ma", ma)); app.add_handler(CommandHandler("scan", scan)); app.add_handler(CommandHandler("start", start))
    app.run_polling()
if __name__=="__main__": main()
