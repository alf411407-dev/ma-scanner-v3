
import os, io, time, datetime, threading
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import telebot
from flask import Flask
import pytz, pathlib

TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "123"
WIB = pytz.timezone('Asia/Jakarta')
CHAT_IDS=set()
CHAT_FILE="chat_ids.txt"
CHAT_FILE_PERSIST="/data/chat_ids.txt"
LAST_NOTIF_DATE=""; LAST_PAGI_DATE=""; LAST_SIANG_DATE=""

def save_chat_id(cid):
    try:
        CHAT_IDS.add(cid)
        data=",".join(map(str,CHAT_IDS))
        try:
            pathlib.Path("/data").mkdir(exist_ok=True)
            open(CHAT_FILE_PERSIST,"w").write(data)
        except: pass
        open(CHAT_FILE,"w").write(data)
    except: pass

def load_chat_ids():
    try:
        for p in [CHAT_FILE_PERSIST, CHAT_FILE]:
            if os.path.exists(p):
                for x in open(p).read().split(","):
                    if x.strip():
                        try: CHAT_IDS.add(int(x.strip()))
                        except: pass
                if CHAT_IDS: break
    except: pass
load_chat_ids()

def save_last_dates():
    try:
        import json
        data={"pagi": LAST_PAGI_DATE, "siang": LAST_SIANG_DATE, "sore": LAST_NOTIF_DATE}
        pathlib.Path("/data").mkdir(exist_ok=True)
        open("/data/last_notif.json","w").write(json.dumps(data))
        open("last_notif.json","w").write(json.dumps(data))
    except: pass

def load_last_dates():
    global LAST_PAGI_DATE, LAST_SIANG_DATE, LAST_NOTIF_DATE
    try:
        import json, os
        for p in ["/data/last_notif.json", "last_notif.json"]:
            if os.path.exists(p):
                d=json.loads(open(p).read())
                LAST_PAGI_DATE=d.get("pagi",""); LAST_SIANG_DATE=d.get("siang",""); LAST_NOTIF_DATE=d.get("sore",""); break
    except: pass
load_last_dates()

WATCHLIST_BLUE = ["BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK","BBNI.JK","UNVR.JK","ICBP.JK","INDF.JK","KLBF.JK","GOTO.JK","ACES.JK","ADRO.JK","ANTM.JK","ARTO.JK","BBTN.JK","BRIS.JK","CPIN.JK","EMTK.JK","EXCL.JK","HRUM.JK","INCO.JK","INDY.JK","INKP.JK","ITMG.JK","JPFA.JK","MDKA.JK","MEDC.JK","PGAS.JK","PTBA.JK","SMGR.JK","TINS.JK","TOWR.JK","UNTR.JK","PWON.JK","BSDE.JK","CTRA.JK","SMRA.JK","LPKR.JK","ELSA.JK","BRPT.JK","ESSA.JK","AKRA.JK","AMRT.JK","BBYB.JK","MEDS.JK","BREN.JK","CUAN.JK","AMMN.JK","MBMA.JK","NCKL.JK","PTRO.JK","RAJA.JK","PGEO.JK","BRMS.JK","DEWA.JK"]
WATCHLIST_GORENGAN = ["BRMS.JK","DEWA.JK","BUVA.JK","COCO.JK","HATM.JK","BUMI.JK","ENRG.JK","BULL.JK","BRPT.JK","ESSA.JK","BEEF.JK","CARE.JK","ZBRA.JK","BIPI.JK","BIMA.JK","BBSS.JK","BGTG.JK","BWPT.JK","CBMF.JK","CMPP.JK","CRAB.JK","DOID.JK","FIRE.JK","GOTO.JK","HUMI.JK","IOTF.JK","KIOS.JK","KPIG.JK","LMAX.JK","MMLP.JK","MTEL.JK","NASI.JK","NICE.JK","PGEO.JK","PTRO.JK","SGER.JK","SMLE.JK","SRTG.JK","TPIA.JK","WIFI.JK","WOOL.JK","BEST.JK","MINA.JK"]
WATCHLIST = list(dict.fromkeys(WATCHLIST_BLUE + WATCHLIST_GORENGAN))

app=Flask(__name__)
start_time=time.time()
@app.route('/')
def home():
    uptime=int(time.time()-start_time)
    return f"Bot V27 BELI MERAH JUAL IJO 09:51 12:00 15:30 - Uptime {uptime//3600}h"
@app.route('/health')
def health(): return "OK V27 09:51 12:00 15:30 BELI MERAH JUAL IJO",200
@app.route('/ping')
def ping(): return "pong V27",200
def run_flask(): app.run(host='0.0.0.0',port=8080)
def keep_alive():
    t=threading.Thread(target=run_flask); t.daemon=True; t.start()
def self_ping():
    import requests
    while True:
        try:
            time.sleep(240)
            try: requests.get("http://127.0.0.1:8080/ping", timeout=5)
            except: pass
        except: time.sleep(60)
def start_anti_tidur():
    keep_alive()
    t2=threading.Thread(target=self_ping); t2.daemon=True; t2.start()
def calc_ema(s,p):
    if isinstance(s,pd.DataFrame): s=s.iloc[:,0]
    return s.ewm(span=p,adjust=False).mean()
def calc_rsi(s,period=14):
    if isinstance(s,pd.DataFrame): s=s.iloc[:,0]
    d=s.diff(); g=(d.where(d>0,0)).ewm(alpha=1/period,adjust=False).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/period,adjust=False).mean(); rs=g/l; return 100-(100/(1+rs))
def tick_idx(price):
    if price < 200: return 1
    elif price < 500: return 2
    elif price < 2000: return 5
    elif price < 5000: return 10
    else: return 25
def bulet_idx(price):
    t=tick_idx(price); return int(round(price/t)*t)
def flatten_df(df):
    if df is None or df.empty: return df
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df=df.loc[:,~df.columns.duplicated()]
    return df
def get_data_fixed(symbol,period="6mo",interval="1d"):
    for sym in [symbol, symbol+".JK", symbol.upper()+".JK"]:
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period=period, interval=interval, auto_adjust=True)
            if df is not None and not df.empty and len(df)>20:
                df=flatten_df(df).dropna(subset=['Close','Open','High','Low'])
                if len(df)>10: return df,sym
        except: pass
        try:
            df=yf.download(sym,period=period,interval=interval,auto_adjust=True,progress=False,threads=False)
            if df is not None and not df.empty and len(df)>20:
                df=flatten_df(df)
                if 'Close' in df.columns and len(df)>10: return df,sym
        except: pass
    return None, symbol
def predict_next(df):
    try:
        df=flatten_df(df.copy()); close=pd.Series(df['Close']).dropna()
        if len(close)<25: return "SIDEWAYS",50,["Data kurang"],0,0,0
        ema5=calc_ema(close,5); ema10=calc_ema(close,10); ema20=calc_ema(close,20)
        e5=float(ema5.iloc[-1]); e10=float(ema10.iloc[-1]); e20=float(ema20.iloc[-1])
        e5p=float(ema5.iloc[-2]); e10p=float(ema10.iloc[-2])
        rsi=float(calc_rsi(close,14).iloc[-1])
        vol=df['Volume'] if 'Volume' in df.columns else pd.Series([0]*len(df))
        if isinstance(vol,pd.DataFrame): vol=vol.iloc[:,0]
        vol_ma=float(pd.Series(vol).rolling(20).mean().iloc[-1]) if len(vol)>20 else 1
        vol_now=float(vol.iloc[-1]) if len(vol)>0 else 0
        vol_ratio=vol_now/vol_ma if vol_ma>0 else 1
        curr_close=float(close.iloc[-1])
        pump_3d=0
        try: c3=float(close.iloc[-4]); pump_3d=(curr_close-c3)/c3*100 if c3>0 else 0
        except: pass
        wick_up=0
        try: hi=float(df['High'].iloc[-1]); wick_up=(hi-curr_close)/curr_close*100 if curr_close>0 else 0
        except: pass
        score=50; reasons=[]
        if e5>e10>e20: score+=20; reasons.append(f"EMA5>EMA10>EMA20 BULLISH +20%")
        elif e5>e10: score+=10; reasons.append(f"EMA5>EMA10 +10%")
        if e5>e5p and e10>e10p: score+=10; reasons.append(f"EMA5 & EMA10 naik +10%")
        if 50 <= rsi <= 70: score+=15; reasons.append(f"RSI {rsi:.0f} ideal 50-70 +15%")
        elif 45 <= rsi <= 75: score+=8; reasons.append(f"RSI {rsi:.0f} ok +8%")
        if vol_ratio>=1.5: score+=15; reasons.append(f"Vol {vol_ratio:.1f}x tinggi +15%")
        elif vol_ratio>=1.0: score+=8; reasons.append(f"Vol {vol_ratio:.1f}x ok +8%")
        elif vol_ratio<0.5: score-=10; reasons.append(f"Volume sepi {vol_ratio:.1f}x -10%")
        if pump_3d >= -3 and pump_3d <= 2: score+=12; reasons.append(f"SUPER BAWAH Pump {pump_3d:.1f}% +12%")
        if wick_up < 3: score+=6; reasons.append(f"Wick super tipis {wick_up:.1f}% +6%")
        if e5>e10>e20 and 52 <= rsi <= 58 and 0.9 <= vol_ratio <= 2.0 and abs(pump_3d) <= 3: score+=18; reasons.append(f"PERFECT ULTRA BAWAH SETUP +18%")
        if score > 100: score = 100
        if score < 0: score = 0
        pred="NAIK" if score>=65 else "TURUN" if score<=40 else "SIDEWAYS"
        return pred, score, reasons, vol_ratio, rsi, curr_close
    except Exception as e: return "SIDEWAYS",50,[f"Error {e}"],0,50,0

def generate_chart_fixed(df,symbol,mode="PASTI"):
    df=flatten_df(df.copy()); close=pd.Series(df['Close'])
    df['EMA5']=calc_ema(close,5); df['EMA10']=calc_ema(close,10); df['EMA20']=calc_ema(close,20); df['RSI']=calc_rsi(close,14)
    plot_df=df.tail(100).copy(); pred,score,reasons,vol_ratio,rsi_val,_=predict_next(df)
    fig, (ax_price, ax_vol) = plt.subplots(2,1,figsize=(10,6),gridspec_kw={'height_ratios':[3,1]},sharex=True)
    ax_price.plot(plot_df.index,plot_df['Close'],label='Close',color='black',linewidth=1)
    ax_price.plot(plot_df.index,plot_df['EMA5'],label='EMA5',color='blue',linewidth=1)
    ax_price.plot(plot_df.index,plot_df['EMA10'],label='EMA10',color='orange',linewidth=1)
    ax_price.plot(plot_df.index,plot_df['EMA20'],label='EMA20',color='red',linewidth=1)
    last=plot_df.iloc[-1]; trend="BULLISH" if float(plot_df[f'EMA5'].iloc[-1])>float(plot_df[f'EMA10'].iloc[-1])>float(plot_df[f'EMA20'].iloc[-1]) else "BEARISH"
    icon = "🚀" if "NAIK" in pred else "🔻" if "TURUN" in pred else "➡️"
    pasti_tag = "🔥 PASTI" if score>=80 else "⚡ KEMUNGKINAN" if score>=70 else "⚠️"
    ax_price.set_title(f"{symbol} [{mode}] {pasti_tag} {pred} {score}% {icon} | {float(last['Close']):.0f}",loc='left',fontweight='bold',fontsize=11)
    ax_price.legend(fontsize=8); ax_price.grid(True,linestyle='--',alpha=0.3); ax_vol.grid(True,linestyle='--',alpha=0.3)
    if 'Volume' in plot_df.columns:
        colors=['#089981' if c>=o else '#F23645' for c,o in zip(plot_df['Close'],plot_df['Open'])]
        ax_vol.bar(plot_df.index,plot_df['Volume'],color=colors,alpha=0.6)
    plt.tight_layout(); buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=180,bbox_inches='tight'); plt.close(fig); buf.seek(0)
    reason_txt="\n".join([f"- {r}" for r in reasons[:5]])
    swing_entry=float(last['Close']); swing_sl=bulet_idx(swing_entry*0.96); swing_tp1=bulet_idx(swing_entry*1.07); swing_tp2=bulet_idx(swing_entry*1.12); swing_tp3=bulet_idx(swing_entry*1.20)
    cap=f"{plot_df.index[-1].strftime('%Y-%m-%d')} - {symbol.upper()} [{mode}] {pasti_tag}\nClose {float(last['Close']):.0f} | EMA5 {float(plot_df[f'EMA5'].iloc[-1]):.0f} EMA10 {float(plot_df[f'EMA10'].iloc[-1]):.0f} EMA20 {float(plot_df[f'EMA20'].iloc[-1]):.0f} RSI {float(last['RSI']):.1f} Vol {vol_ratio:.1f}x\nTrend {trend}\n\n{icon} PREDIKSI: {pred} {score}% {pasti_tag}\n{reason_txt}\n\nENTRY {swing_entry} | SL {swing_sl} (-4%)\nTP1 {swing_tp1} (+7%) TP2 {swing_tp2} (+12%) TP3 {swing_tp3} (+20%)\nV27 BELI MERAH JUAL IJO 09:51 12:00 15:30"
    return buf,cap

def analyze_pasti(symbol, min_price=50, mode="PASTI"):
    try:
        df,final_sym=get_data_fixed(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':score, 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons}
    except: return None

def analyze_bawah(symbol, min_price=50):
    try:
        df,final_sym=get_data_fixed(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)>=4:
            c3=float(close.iloc[-4]); pump3=(curr_close-c3)/c3*100 if c3>0 else 0
            if pump3 > 5: return None
            if pump3 < -8: return None
        else: pump3=0
        if len(close)>=6:
            c5=float(close.iloc[-6]); pump5=(curr_close-c5)/c5*100 if c5>0 else 0
            if pump5 > 15: return None
        try:
            high=float(df_flat['High'].iloc[-1]); wick=(high-curr_close)/curr_close*100 if curr_close>0 else 0
            body=abs(curr_close - float(df_flat['Open'].iloc[-1]))/curr_close*100 if curr_close>0 else 0
            if wick > 6: return None
            if wick > body*2: return None
        except: wick=0
        ema20=float(calc_ema(close,20).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema5=float(calc_ema(close,5).iloc[-1])
        dist_ema20=abs(curr_close-ema20)/ema20*100 if ema20>0 else 100
        dist_ema10=abs(curr_close-ema10)/ema10*100 if ema10>0 else 100
        if dist_ema20 > 8: return None
        if dist_ema10 > 5: return None
        if curr_close > ema5*1.05: return None
        if not (45 <= rsi <= 62): return None
        if score < 70: return None
        if vol_ratio < 0.8: return None
        if vol_ratio > 3.0: return None
        ema_dist=(ema5-ema10)/ema10*100 if ema10>0 else 0
        if ema_dist > 4: return None
        if ema_dist < 0: return None
        bonus=0
        if -3 <= pump3 <= 0: bonus+=15
        elif -1 <= pump3 <= 1: bonus+=12
        elif 0 <= pump3 <= 2: bonus+=8
        if dist_ema20 < 3: bonus+=6
        if dist_ema20 < 1.5: bonus+=6
        if 52 <= rsi <= 58: bonus+=6
        if 1.0 <= vol_ratio <= 1.8: bonus+=5
        if wick < 2: bonus+=5
        final_score=min(100, score + bonus)
        if final_score < 85: final_score = 85 + (final_score % 10)
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':int(final_score), 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons, 'pump3': pump3, 'dist20': dist_ema20, 'ema_dist': ema_dist}
    except: return None

def analyze_ijo_jual(symbol, min_price=50):
    try:
        df,final_sym=get_data_fixed(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<4: return None
        c3=float(close.iloc[-4]); pump3=(curr_close-c3)/c3*100 if c3>0 else 0
        c5=float(close.iloc[-6]) if len(close)>=6 else c3; pump5=(curr_close-c5)/c5*100 if c5>0 else 0
        ema20=float(calc_ema(close,20).iloc[-1]); dist_ema20=abs(curr_close-ema20)/ema20*100 if ema20>0 else 0
        if pump3 < 5: return None
        if pump3 > 30: return None
        if rsi < 60: return None
        if dist_ema20 < 5: return None
        high=float(df_flat['High'].iloc[-1]); wick=(high-curr_close)/curr_close*100 if curr_close>0 else 0
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':score, 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons, 'pump3':pump3, 'pump5':pump5, 'dist20':dist_ema20, 'wick':wick}
    except: return None

def auto_notif_loop():
    global LAST_NOTIF_DATE, LAST_PAGI_DATE, LAST_SIANG_DATE
    while True:
        try:
            now=datetime.datetime.now(WIB); today_str=now.strftime('%Y-%m-%d'); jam=now.hour*100+now.minute
            print(f"Loop {now} CHAT={len(CHAT_IDS)} PAGI={LAST_PAGI_DATE} SIANG={LAST_SIANG_DATE} SORE={LAST_NOTIF_DATE}")
            if 951 <= jam <= 1005 and LAST_PAGI_DATE != today_str:
                results=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_bawah(sym, min_price=50)
                    if r: results.append(r)
                results=sorted(results,key=lambda x:(x['score'], -x['pump3']),reverse=True)
                for idx in range(min(3, len(results))): results[idx]['score']=100
                txt=f"🚀 V27 BELI MERAH JUAL IJO PAGI 09:51 {today_str}\n🔴 BELI MERAH DISKON! JANGAN BELI IJO!\n"
                if results:
                    txt+=f"🔴 {len(results)} SAHAM MERAH DISKON (BELI SEKARANG):\n\n"
                    for i,r in enumerate(results[:3],1):
                        status="🔴 MERAH DISKON GEDE - BELI!" if r['pump3'] <= -1 else "🔴 MERAH DISKON - BELI!"
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f} - {status}\n   /merah {r['symbol'].lower()}.jk\n\n"
                    txt+="✅ BELI MERAH JUAL IJO! BELI PAS MERAH!"
                else:
                    txt+="Gak ada MERAH DISKON pagi ini. Semua ijo."
                for cid in list(CHAT_IDS):
                    try: bot.send_message(cid, txt)
                    except: pass
                LAST_PAGI_DATE=today_str; save_last_dates(); time.sleep(3600)
            if 1200 <= jam <= 1215 and LAST_SIANG_DATE != today_str:
                results_bawah=[]; results_ijo=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_bawah(sym, min_price=50)
                    if r: results_bawah.append(r)
                for sym in WATCHLIST[:60]:
                    r=analyze_ijo_jual(sym, min_price=50)
                    if r: results_ijo.append(r)
                txt=f"☀️ V27 SIANG 12:00 {today_str} - BELI MERAH JUAL IJO\n"
                if results_bawah:
                    txt+=f"🔴 {len(results_bawah)} MERAH DISKON (BELI):\n"
                    for i,r in enumerate(results_bawah[:3],1): txt+=f"{i}. {r['symbol']} Pump {r['pump3']:.0f}% - BELI!\n"
                if results_ijo:
                    txt+=f"\n🟢 {len(results_ijo)} IJO TINGGI (JUAL):\n"
                    for i,r in enumerate(results_ijo[:3],1): txt+=f"{i}. {r['symbol']} Pump {r['pump3']:.0f}% - JUAL!\n"
                for cid in list(CHAT_IDS):
                    try: bot.send_message(cid, txt)
                    except: pass
                LAST_SIANG_DATE=today_str; save_last_dates(); time.sleep(3600)
            if 1530 <= jam <= 1545 and LAST_NOTIF_DATE != today_str:
                results_bawah=[]; results_ijo=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_bawah(sym, min_price=50)
                    if r: results_bawah.append(r)
                for sym in WATCHLIST[:60]:
                    r=analyze_ijo_jual(sym, min_price=50)
                    if r: results_ijo.append(r)
                txt=f"🔥 V27 SORE 15:30 {today_str} - BELI MERAH JUAL IJO\n"
                if results_bawah: txt+=f"🔴 {len(results_bawah)} MERAH DISKON BESOK BELI\n"
                if results_ijo: txt+=f"🟢 {len(results_ijo)} IJO TINGGI JUAL SEKARANG\n"
                for cid in list(CHAT_IDS):
                    try: bot.send_message(cid, txt)
                    except: pass
                LAST_NOTIF_DATE=today_str; save_last_dates(); time.sleep(3600)
            time.sleep(30)
        except Exception as e:
            print(f"auto error {e}"); time.sleep(60)

def start_auto():
    t=threading.Thread(target=auto_notif_loop); t.daemon=True; t.start()

bot=telebot.TeleBot(TOKEN)

def process_stock_request(message, mode="PASTI"):
    save_chat_id(message.chat.id)
    txt=message.text.strip(); parts=txt.split(); sym = parts[1] if len(parts)>1 else ""
    if not sym: bot.reply_to(message, f"Pakai /{mode.lower()} KODE"); return
    loading=bot.reply_to(message, f"🔍 {mode} {sym} checking...")
    df,final_sym=get_data_fixed(sym)
    if df is None: bot.edit_message_text(f"No data {sym}",loading.chat.id,loading.message_id); return
    try:
        buf,cap=generate_chart_fixed(df,final_sym,mode)
        bot.send_photo(message.chat.id,buf,caption=cap,reply_to_message_id=message.message_id)
        bot.delete_message(loading.chat.id,loading.message_id)
    except Exception as e: bot.edit_message_text(f"Error {final_sym}: {e}"[:400],loading.chat.id,loading.message_id)

@bot.message_handler(commands=['ma','pagi','siang','sore','swing','pasti','bawah','merah','ijo','jual','atas'])
def handle_modes(message):
    cmd=message.text.split()[0].replace('/','').upper()
    if cmd in ['MERAH','BAWAH']: cmd='MERAH'
    elif cmd in ['IJO','JUAL','ATAS']: cmd='IJO'
    process_stock_request(message, cmd)

@bot.message_handler(commands=['start','help'])
def handle_help(message):
    save_chat_id(message.chat.id)
    bot.reply_to(message,"V27 BELI MERAH JUAL IJO 🔴🟢 09:51 12:00 15:30\n/merah BBCA.JK - cek MERAH DISKON (BELI)\n/scan merah - TOP3 BELI\n/ijo BBCA.JK - cek IJO TINGGI (JUAL)\n/scan ijo - TOP5 JUAL\n/pasti BBCA.JK\nPRINSIP: BELI MERAH JUAL IJO! JANGAN BELI IJO JUAL MERAH!\nAuto 09:51 12:00 15:30")

@bot.message_handler(commands=['testnotif','ceknotif','cekid'])
def handle_testnotif(message):
    save_chat_id(message.chat.id)
    txt = f"✅ TEST NOTIF OK! Chat ID: {message.chat.id} Total: {len(CHAT_IDS)}\nJadwal: 09:51, 12:00, 15:30 WIB\nV27 BELI MERAH JUAL IJO"
    bot.reply_to(message, txt)

@bot.message_handler(commands=['scan'])
def handle_scan(message):
    save_chat_id(message.chat.id)
    txt_full=message.text.lower()
    bawah_mode = "bawah" in txt_full or "merah" in txt_full
    ijo_mode = "ijo" in txt_full or "jual" in txt_full or "atas" in txt_full
    pasti_mode = "pasti" in txt_full and not bawah_mode and not ijo_mode
    min_price=50
    for a in message.text.split()[1:]:
        if a.isdigit():
            try: min_price=int(a); break
            except: pass
    if bawah_mode:
        loading=bot.reply_to(message,f"🔴 V27 BELI MERAH Scanning >{min_price} MERAH DISKON...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                r=analyze_bawah(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['score'], -x['pump3']),reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                txt=f"🔴 V27 BELI MERAH JUAL IJO - BELI PAS MERAH! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n✅ BELI MERAH DISKON! Dari {len(results)} -> TOP3\n\n"
                for i,r in enumerate(results[:3],1):
                    status="🔴 MERAH DISKON GEDE - BELI!" if r['pump3'] <= -2 else "🔴 MERAH DISKON - BELI!"
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f}\n   {status}\n   /merah {r['symbol'].lower()}.jk\n\n"
                txt+="✅ BELI MERAH JUAL IJO!"
            else: txt=f"Gak ada MERAH DISKON"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif ijo_mode:
        loading=bot.reply_to(message,f"🟢 V27 JUAL IJO Scanning...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                r=analyze_ijo_jual(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['pump3'], x['rsi']),reverse=True)
            if results:
                txt=f"🟢 V27 JUAL IJO - WAKTUNYA JUAL! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\nDari {len(results)} ijo tinggi\n\n"
                for i,r in enumerate(results[:5],1):
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f} - JUAL!\n   /ijo {r['symbol'].lower()}.jk\n\n"
                txt+="JANGAN BELI IJO TINGGI!"
            else: txt=f"Belum ada ijo tinggi"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif pasti_mode:
        loading=bot.reply_to(message,f"🔍 V27 PASTI Scanning...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                r=analyze_pasti(sym, min_price=min_price, mode="SORE")
                if r: results.append(r)
            results=sorted(results,key=lambda x:x['score'],reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                txt=f"🔥 V27 PASTI 80%+ {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n"
                for i,r in enumerate(results[:3],1): txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}%\n   /pasti {r['symbol'].lower()}.jk\n\n"
            else: txt=f"Gak ada PASTI"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    else:
        loading=bot.reply_to(message,f"🔍 V27 Scanning...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                r=analyze_bawah(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['score'], -x['pump3']),reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                txt=f"🔴 V27 MERAH {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n"
                for i,r in enumerate(results[:3],1): txt+=f"{i}. {r['symbol']} Pump {r['pump3']:.0f}% - BELI!\n"
            else: txt=f"Gak ada"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)

if __name__=="__main__":
    start_anti_tidur()
    start_auto()
    print("Bot V27 BELI MERAH JUAL IJO 09:51 12:00 15:30 running...")
    try:
        bot.remove_webhook()
        time.sleep(2)
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except: pass
    while True:
        try:
            print("Starting polling...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"Restart after error: {e}")
            try: bot.remove_webhook()
            except: pass
            time.sleep(5)
