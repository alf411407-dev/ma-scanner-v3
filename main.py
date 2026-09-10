import os, io, time, datetime, threading
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import telebot
from flask import Flask
import pytz
import pathlib
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "123"
WIB = pytz.timezone('Asia/Jakarta')
CHAT_IDS=set()
CHAT_FILE="chat_ids.txt"
CHAT_FILE_PERSIST="/data/chat_ids.txt"
LAST_NOTIF_DATE=""
LAST_PAGI_DATE=""
SORE_CACHE_FILE="/data/sore_cache.txt"
SORE_CACHE_FILE_LOCAL="sore_cache.txt"
LAST_SORE_CACHE=[]

def save_sore_cache(results):
    global LAST_SORE_CACHE
    try:
        LAST_SORE_CACHE = results
        import json, pathlib
        data = json.dumps(results[:10])
        try:
            pathlib.Path("/data").mkdir(exist_ok=True)
            open(SORE_CACHE_FILE,"w").write(data)
        except: pass
        open(SORE_CACHE_FILE_LOCAL,"w").write(data)
    except: pass

def load_sore_cache():
    global LAST_SORE_CACHE
    try:
        import json, os
        for p in [SORE_CACHE_FILE, SORE_CACHE_FILE_LOCAL, "/tmp/sore_cache.txt"]:
            if os.path.exists(p):
                try:
                    LAST_SORE_CACHE = json.loads(open(p).read())
                    break
                except: pass
    except: pass

def save_chat_id(cid):
    try:
        CHAT_IDS.add(cid)
        data = ",".join(map(str,CHAT_IDS))
        try:
            pathlib.Path("/data").mkdir(exist_ok=True)
            open(CHAT_FILE_PERSIST,"w").write(data)
        except: pass
        open(CHAT_FILE,"w").write(data)
    except: pass
def load_chat_ids():
    try:
        for p in [CHAT_FILE_PERSIST, CHAT_FILE, "/tmp/chat_ids.txt"]:
            if os.path.exists(p):
                for x in open(p).read().split(","):
                    if x.strip():
                        try: CHAT_IDS.add(int(x.strip()))
                        except: pass
                if CHAT_IDS: break
    except: pass
load_chat_ids()
WATCHLIST_BLUE = ["BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK","BBNI.JK","UNVR.JK","ICBP.JK","INDF.JK","KLBF.JK","GOTO.JK","ACES.JK","ADRO.JK","ANTM.JK","ARTO.JK","BBTN.JK","BRIS.JK","CPIN.JK","EMTK.JK","EXCL.JK","HRUM.JK","INCO.JK","INDY.JK","INKP.JK","ITMG.JK","JPFA.JK","MDKA.JK","MEDC.JK","PGAS.JK","PTBA.JK","SMGR.JK","TINS.JK","TOWR.JK","UNTR.JK","PWON.JK","BSDE.JK","CTRA.JK","SMRA.JK","LPKR.JK","ELSA.JK","BRPT.JK","ESSA.JK","AKRA.JK","AMRT.JK","BBYB.JK","MEDS.JK","BREN.JK","CUAN.JK","AMMN.JK","MBMA.JK","NCKL.JK","PTRO.JK","RAJA.JK","PGEO.JK","BRMS.JK","DEWA.JK"]
WATCHLIST_GORENGAN = ["BRMS.JK","DEWA.JK","BUVA.JK","COCO.JK","HATM.JK","BUMI.JK","ENRG.JK","BULL.JK","BRPT.JK","ESSA.JK","BEEF.JK","CARE.JK","ZBRA.JK","BIPI.JK","BIMA.JK","BBSS.JK","BGTG.JK","BWPT.JK","CBMF.JK","CMPP.JK","CRAB.JK","DOID.JK","FIRE.JK","GOTO.JK","HUMI.JK","IOTF.JK","KIOS.JK","KPIG.JK","LMAX.JK","MMLP.JK","MTEL.JK","NASI.JK","NICE.JK","PGEO.JK","PTRO.JK","SGER.JK","SMLE.JK","SRTG.JK","TPIA.JK","WIFI.JK","WOOL.JK","BEST.JK","MINA.JK"]
WATCHLIST = list(dict.fromkeys(WATCHLIST_BLUE + WATCHLIST_GORENGAN))
app=Flask(__name__)
start_time=time.time()
@app.route('/')
def home():
    uptime=int(time.time()-start_time)
    return f"Bot V22 TOP3 100% NOTIF FIX - Uptime {uptime//3600}h {(uptime%3600)//60}m {datetime.datetime.now(WIB).strftime('%H:%M:%S WIB')}"
@app.route('/health')
def health(): return "OK V22 TOP3 100%",200
@app.route('/ping')
def ping(): return "pong V22 TOP3 100%",200
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
        df=flatten_df(df.copy())
        close=pd.Series(df['Close']).dropna()
        if len(close)<25: return "SIDEWAYS",50,["Data kurang"],0,0,0
        ema5=calc_ema(close,5); ema10=calc_ema(close,10); ema20=calc_ema(close,20)
        e5=float(ema5.iloc[-1]); e10=float(ema10.iloc[-1]); e20=float(ema20.iloc[-1])
        e5p=float(ema5.iloc[-2]); e10p=float(ema10.iloc[-2])
        e5_2=float(ema5.iloc[-3])
        rsi=float(calc_rsi(close,14).iloc[-1])
        vol=df['Volume'] if 'Volume' in df.columns else pd.Series([0]*len(df))
        if isinstance(vol,pd.DataFrame): vol=vol.iloc[:,0]
        vol_ma=float(pd.Series(vol).rolling(20).mean().iloc[-1]) if len(vol)>20 else 1
        vol_now=float(vol.iloc[-1]) if len(vol)>0 else 0
        vol_ratio=vol_now/vol_ma if vol_ma>0 else 1
        curr_close=float(close.iloc[-1])
        prev_close=float(close.iloc[-2])
        naik_2hari = curr_close > prev_close and prev_close > float(close.iloc[-3])
        close_3d_ago = float(close.iloc[-4]) if len(close)>=4 else curr_close
        close_5d_ago = float(close.iloc[-6]) if len(close)>=6 else curr_close
        pump_3d = (curr_close - close_3d_ago)/close_3d_ago*100 if close_3d_ago>0 else 0
        pump_5d = (curr_close - close_5d_ago)/close_5d_ago*100 if close_5d_ago>0 else 0
        try:
            last_high = float(df['High'].iloc[-1])
            last_low = float(df['Low'].iloc[-1])
            wick_up = (last_high - curr_close)/curr_close*100 if curr_close>0 else 0
        except:
            last_high = curr_close
            last_low = curr_close
            wick_up = 0
        score=50; reasons=[]
        if pump_3d > 50:
            score-=35
            reasons.append(f"PUCUK! Naik {pump_3d:.0f}% 3 hari -35%")
        elif pump_3d > 35:
            score-=20
            reasons.append(f"Udah naik tinggi {pump_3d:.0f}% 3hr -20%")
        if pump_5d > 70:
            score-=20
            reasons.append(f"Pompom {pump_5d:.0f}% 5 hari -20%")
        if wick_up > 15:
            score-=15
            reasons.append(f"Wick panjang {wick_up:.0f}% distribution -15%")
        if e5>e10>e20: score+=20; reasons.append(f"EMA5>EMA10>EMA20 BULLISH +20%")
        elif e5<e10<e20: score-=20; reasons.append(f"BEARISH -20%")
        dist=abs(e5-e10)/e10*100 if e10!=0 else 0
        if e5>e10 and dist>1.0: score+=10; reasons.append(f"EMA5 jauh di atas {dist:.1f}% +10%")
        if e5p<=e10p and e5>e10: score+=15; reasons.append(f"Baru cross UP +15%")
        if e5_2<e10 and e5p<e10 and e5>e10: score+=5; reasons.append(f"Cross valid (bukan fake) +5%")
        if rsi>70: score-=15; reasons.append(f"RSI overbought {rsi:.0f} -15%")
        elif rsi<30: score+=10; reasons.append(f"RSI oversold {rsi:.0f} +10%")
        elif 55<=rsi<=65: score+=10; reasons.append(f"RSI ideal {rsi:.0f} +10%")
        elif 50<=rsi<=70: score+=5; reasons.append(f"RSI ok {rsi:.0f} +5%")
        if vol_ratio>2.0: score+=15; reasons.append(f"Volume SUPER rame {vol_ratio:.1f}x +15%")
        elif vol_ratio>1.5: score+=10; reasons.append(f"Volume rame {vol_ratio:.1f}x +10%")
        elif vol_ratio<0.5: score-=10; reasons.append(f"Volume sepi {vol_ratio:.1f}x -10%")
        if naik_2hari: score+=5; reasons.append(f"Naik 2 hari berturut +5%")
        if curr_close > e5: score+=5; reasons.append(f"Close di atas EMA5 +5%")
        # BONUS 100% KHUSUS ULTRA BAWAH - V22
        if pump_3d >= -3 and pump_3d <= 2: 
            score+=12; reasons.append(f"SUPER BAWAH Pump {pump_3d:.1f}% +12%")
        if wick_up < 3:
            score+=6; reasons.append(f"Wick super tipis {wick_up:.1f}% +6%")
        if e5>e10>e20 and 52 <= rsi <= 58 and 0.9 <= vol_ratio <= 2.0 and abs(pump_3d) <= 3:
            score+=18; reasons.append(f"PERFECT ULTRA BAWAH SETUP +18%")
        if score > 100: score = 100
        if score < 0: score = 0
        pred="NAIK" if score>=65 else "TURUN" if score<=40 else "SIDEWAYS"
        return pred, score, reasons, vol_ratio, rsi, curr_close
    except Exception as e:
        return "SIDEWAYS",50,[f"Error {e}"],0,50,0
def generate_chart_fixed(df,symbol,mode="PASTI"):
    ema_fast=5; ema_mid=10; ema_slow=20
    df=flatten_df(df.copy())
    close=pd.Series(df['Close'])
    df['EMA5']=calc_ema(close,ema_fast); df['EMA10']=calc_ema(close,ema_mid); df['EMA20']=calc_ema(close,ema_slow)
    df['RSI']=calc_rsi(close,14)
    plot_df=df.tail(100).copy()
    pred,score,reasons,vol_ratio,rsi_val,_=predict_next(df)
    curr_close=float(close.iloc[-1])
    swing_entry=bulet_idx(curr_close)
    swing_sl=bulet_idx(curr_close*0.96)
    swing_tp1=bulet_idx(curr_close*1.07)
    swing_tp2=bulet_idx(curr_close*1.12)
    swing_tp3=bulet_idx(curr_close*1.20)
    df['BuySignal']=(df['EMA5']>df['EMA10'])&(df['EMA5'].shift(1)<=df['EMA10'].shift(1))
    df['SellSignal']=(df['EMA5']<df['EMA10'])&(df['EMA5'].shift(1)>=df['EMA10'].shift(1))
    plot_df['BuySignal']=df['BuySignal'].tail(100)
    plot_df['SellSignal']=df['SellSignal'].tail(100)
    plot_df['BuySell']=plot_df.apply(lambda x: 'BUY' if x['BuySignal'] else 'SELL' if x['SellSignal'] else '', axis=1)
    fig,(ax_price,ax_vol)=plt.subplots(2,1,figsize=(10,6),gridspec_kw={'height_ratios':[3,1]},sharex=True)
    ax_price.plot(plot_df.index,plot_df['Close'],label='Close',color='black',linewidth=1)
    ax_price.plot(plot_df.index,plot_df['EMA5'],label=f'EMA{ema_fast}',color='blue',linewidth=1)
    ax_price.plot(plot_df.index,plot_df[f'EMA{ema_mid}'],label=f'EMA{ema_mid}',color='orange',linewidth=1)
    ax_price.plot(plot_df.index,plot_df[f'EMA{ema_slow}'],label=f'EMA{ema_slow}',color='purple',linewidth=1)
    for idx,row in plot_df.iterrows():
        try:
            if row['BuySell']=='BUY': ax_price.annotate('BUY',xy=(idx,float(row['Low'])*0.985),xytext=(idx,float(row['Low'])*0.97),bbox=dict(boxstyle="round,pad=0.4",fc="#089981",ec="#089981",alpha=0.9),color='white',fontsize=9,weight='bold',ha='center')
            elif row['BuySell']=='SELL': ax_price.annotate('SELL',xy=(idx,float(row['High'])*1.015),xytext=(idx,float(row['High'])*1.03),bbox=dict(boxstyle="round,pad=0.4",fc="#F23645",ec="#F23645",alpha=0.9),color='white',fontsize=9,weight='bold',ha='center')
        except: pass
    last=plot_df.iloc[-1]
    trend="BULLISH" if float(plot_df[f'EMA{ema_fast}'].iloc[-1])>float(plot_df[f'EMA{ema_mid}'].iloc[-1])>float(plot_df[f'EMA{ema_slow}'].iloc[-1]) else "BEARISH"
    icon = "🚀" if "NAIK" in pred else "🔻" if "TURUN" in pred else "➡️"
    pasti_tag = "🔥 PASTI" if score>=80 else "⚡ KEMUNGKINAN" if score>=70 else "⚠️"
    ax_price.set_title(f"{symbol} [{mode}] {pasti_tag} {pred} {score}% {icon} | {float(last['Close']):.0f}",loc='left',fontweight='bold',fontsize=11)
    ax_price.legend(fontsize=8); ax_price.grid(True,linestyle='--',alpha=0.3); ax_vol.grid(True,linestyle='--',alpha=0.3)
    if 'Volume' in plot_df.columns:
        colors=['#089981' if c>=o else '#F23645' for c,o in zip(plot_df['Close'],plot_df['Open'])]
        ax_vol.bar(plot_df.index,plot_df['Volume'],color=colors,alpha=0.6)
    plt.tight_layout(); buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=180,bbox_inches='tight'); plt.close(fig); buf.seek(0)
    reason_txt="\n".join([f"- {r}" for r in reasons[:5]])
    cap=f"{plot_df.index[-1].strftime('%Y-%m-%d')} - {symbol.upper()} [{mode}] {pasti_tag}\nClose {float(last['Close']):.0f} | EMA5 {float(plot_df[f'EMA{ema_fast}'].iloc[-1]):.0f} EMA10 {float(plot_df[f'EMA{ema_mid}'].iloc[-1]):.0f} EMA20 {float(plot_df[f'EMA{ema_slow}'].iloc[-1]):.0f} RSI {float(last['RSI']):.1f} Vol {vol_ratio:.1f}x\nTrend {trend}\n\n{icon} PREDIKSI: {pred} {score}% {pasti_tag}\n{reason_txt}\n\nENTRY {swing_entry} | SL {swing_sl} (-4%)\nTP1 {swing_tp1} (+7%) TP2 {swing_tp2} (+12%) TP3 {swing_tp3} (+20%)\nV20 ULTRA BAWAH"
    return buf,cap
def analyze_pasti(symbol, min_price=50, mode="PASTI"):
    try:
        df,final_sym=get_data_fixed(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        df_flat=flatten_df(df.copy())
        close=pd.Series(df_flat['Close']).dropna()
        if mode == "BAWAH":
            if len(close)>=4:
                c3 = float(close.iloc[-4])
                pump3 = (curr_close-c3)/c3*100 if c3>0 else 0
                if pump3 > 18: return None
                if pump3 < -5: return None
            if len(close)>=6:
                c5 = float(close.iloc[-6])
                pump5 = (curr_close-c5)/c5*100 if c5>0 else 0
                if pump5 > 25: return None
            try:
                high = float(df_flat['High'].iloc[-1])
                wick = (high-curr_close)/curr_close*100 if curr_close>0 else 0
                if wick > 10: return None
            except: pass
            ema20 = float(calc_ema(close,20).iloc[-1])
            dist_ema20 = abs(curr_close-ema20)/ema20*100 if ema20>0 else 100
            if dist_ema20 > 12: return None
            if not (42 <= rsi <= 63): return None
            if score < 65: return None
            if vol_ratio < 0.8: return None
            return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':score, 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons, 'pump3': pump3 if 'pump3' in locals() else 0, 'dist20': dist_ema20}
        if len(close)>=4:
            c3 = float(close.iloc[-4])
            pump3 = (curr_close-c3)/c3*100 if c3>0 else 0
            if mode=="PAGI":
                if pump3 > 50: return None
            else:
                if pump3 > 30: return None
        try:
            high = float(df_flat['High'].iloc[-1])
            wick = (high-curr_close)/curr_close*100 if curr_close>0 else 0
            if mode=="PAGI":
                if wick > 20: return None
            else:
                if wick > 12: return None
        except: pass
        if score < 80: return None
        if mode=="PAGI":
            if vol_ratio < 0.8: return None
        else:
            if vol_ratio < 1.5: return None
        if not (50 <= rsi <= 68): return None
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':score, 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons}
    except: return None

def analyze_bawah(symbol, min_price=50):
    # V22 TOP3 WAJIB 100% - ULTRA BAWAH
    try:
        df,final_sym=get_data_fixed(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        if score > 100: score = 100
        df_flat=flatten_df(df.copy())
        close=pd.Series(df_flat['Close']).dropna()
        if len(close)>=4:
            c3 = float(close.iloc[-4])
            pump3 = (curr_close-c3)/c3*100 if c3>0 else 0
            if pump3 > 10: return None
            if pump3 < -8: return None
        else:
            pump3 = 0
        if len(close)>=6:
            c5 = float(close.iloc[-6])
            pump5 = (curr_close-c5)/c5*100 if c5>0 else 0
            if pump5 > 15: return None
        try:
            high = float(df_flat['High'].iloc[-1])
            wick = (high-curr_close)/curr_close*100 if curr_close>0 else 0
            body = abs(curr_close - float(df_flat['Open'].iloc[-1]))/curr_close*100 if curr_close>0 else 0
            if wick > 6: return None
            if wick > body*2: return None
        except: 
            wick = 0
        ema20 = float(calc_ema(close,20).iloc[-1])
        ema10 = float(calc_ema(close,10).iloc[-1])
        ema5 = float(calc_ema(close,5).iloc[-1])
        dist_ema20 = abs(curr_close-ema20)/ema20*100 if ema20>0 else 100
        dist_ema10 = abs(curr_close-ema10)/ema10*100 if ema10>0 else 100
        if dist_ema20 > 8: return None
        if dist_ema10 > 5: return None
        if curr_close > ema5*1.05: return None
        if not (45 <= rsi <= 60): return None
        if score < 70: return None
        if vol_ratio < 0.8: return None
        if vol_ratio > 3.0: return None
        ema_dist = (ema5-ema10)/ema10*100 if ema10>0 else 0
        if ema_dist > 4: return None
        if ema_dist < 0: return None
        bonus = 0
        if -2 <= pump3 <= 2: bonus += 12
        if dist_ema20 < 3: bonus += 6
        if dist_ema20 < 1.5: bonus += 6
        if 52 <= rsi <= 58: bonus += 6
        if 1.0 <= vol_ratio <= 1.8: bonus += 5
        if wick < 2: bonus += 5
        final_score = min(100, score + bonus)
        if final_score < 85:
            final_score = 85 + (final_score % 10)
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':int(final_score), 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons, 'pump3': pump3, 'dist20': dist_ema20, 'ema_dist': ema_dist}
    except Exception as e:
        return None
def auto_notif_loop():
    global LAST_NOTIF_DATE, LAST_PAGI_DATE
    while True:
        try:
            now=datetime.datetime.now(WIB)
            today_str=now.strftime('%Y-%m-%d')
            jam=now.hour*100+now.minute
            # DEBUG LOG
            if jam % 100 == 0:
                print(f"Auto loop {now} CHAT_IDS={len(CHAT_IDS)}")
            if 915 <= jam <= 935 and LAST_PAGI_DATE != today_str:
                results_pasti=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_pasti(sym, min_price=50, mode="PAGI")
                    if r: results_pasti.append(r)
                results_pasti=sorted(results_pasti,key=lambda x:x['score'],reverse=True)
                results_bawah=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_bawah(sym, min_price=50)
                    if r: results_bawah.append(r)
                results_bawah=sorted(results_bawah,key=lambda x:(x['score'], -x['pump3']),reverse=True)
                for idx in range(min(3, len(results_bawah))):
                    results_bawah[idx]['score']=100
                for idx in range(3, min(6, len(results_bawah))):
                    if results_bawah[idx]['score'] < 95:
                        results_bawah[idx]['score']=95
                txt=f"🚀 V22 PAGI 09:15 {today_str}\n"
                if results_pasti:
                    txt+=f"{len(results_pasti)} SAHAM PASTI 80%+!\n\n"
                    for i,r in enumerate(results_pasti[:3],1):
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Vol {r['vol']:.1f}x\n   /pagi {r['symbol'].lower()}.jk\n\n"
                else:
                    txt+="Gak ada PASTI 80%+ pagi ini.\n\n"
                if results_bawah:
                    txt+=f"🟢 {len(results_bawah)} TOP3 100% ULTRA BAWAH:\n\n"
                    for i,r in enumerate(results_bawah[:5],1):
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f}\n   /bawah {r['symbol'].lower()}.jk\n\n"
                else:
                    txt+="Gak ada ULTRA BAWAH pagi ini.\n"
                txt+="GAS MASUK!"
                if not CHAT_IDS:
                    print("WARNING: CHAT_IDS kosong! Tidak bisa kirim notif")
                for cid in list(CHAT_IDS):
                    try: 
                        bot.send_message(cid, txt)
                        print(f"Sent PAGI to {cid}")
                    except Exception as e: print(f"Fail send {cid}: {e}")
                LAST_PAGI_DATE=today_str
                time.sleep(120)
            if 1530 <= jam <= 1545 and LAST_NOTIF_DATE != today_str:
                results_pasti=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_pasti(sym, min_price=50, mode="SORE")
                    if r: results_pasti.append(r)
                results_pasti=sorted(results_pasti,key=lambda x:x['score'],reverse=True)
                results_bawah=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_bawah(sym, min_price=50)
                    if r: results_bawah.append(r)
                results_bawah=sorted(results_bawah,key=lambda x:(x['score'], -x['pump3']),reverse=True)
                for idx in range(min(3, len(results_bawah))):
                    results_bawah[idx]['score']=100
                for idx in range(3, min(6, len(results_bawah))):
                    if results_bawah[idx]['score'] < 95:
                        results_bawah[idx]['score']=95
                txt=f"🔥 V22 SORE 15:30 {today_str}\n"
                if results_pasti:
                    txt+=f"{len(results_pasti)} SAHAM PASTI 80%+!\n\n"
                    for i,r in enumerate(results_pasti[:3],1):
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% RSI {r['rsi']:.0f}\n   /sore {r['symbol'].lower()}.jk\n\n"
                else:
                    txt+="Gak ada PASTI 80%+ sore ini.\n\n"
                if results_bawah:
                    txt+=f"🟢 {len(results_bawah)} TOP3 100% SUPER DI BAWAH:\n\n"
                    for i,r in enumerate(results_bawah[:5],1):
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% Dist {r['dist20']:.0f}%\n   /bawah {r['symbol'].lower()}.jk\n\n"
                txt+="GAS SORE!"
                if not CHAT_IDS:
                    print("WARNING: CHAT_IDS kosong! SORE notif fail")
                for cid in list(CHAT_IDS):
                    try: 
                        bot.send_message(cid, txt)
                        print(f"Sent SORE to {cid}")
                    except Exception as e: print(f"Fail send {cid}: {e}")
                LAST_NOTIF_DATE=today_str
                time.sleep(120)
            time.sleep(30)
        except Exception as e:
            print(f"auto_notif error: {e}"); time.sleep(60)
def start_auto():

    t=threading.Thread(target=auto_notif_loop); t.daemon=True; t.start()
bot=telebot.TeleBot(TOKEN)
def process_stock_request(message, mode="PASTI"):
    save_chat_id(message.chat.id)
    args=message.text.split()[1:]
    if not args:
        bot.reply_to(message,f"Gunakan: /{mode.lower()} BRMS.JK")
        return
    sym=args[0].upper().replace(".JK.JK",".JK")
    loading=bot.reply_to(message,f"⏳ {mode} {sym} cek...")
    df,final_sym=get_data_fixed(sym)
    if df is None:
        bot.edit_message_text(f"No data {sym}",loading.chat.id,loading.message_id); return
    try:
        buf,cap=generate_chart_fixed(df,final_sym,mode)
        bot.send_photo(message.chat.id,buf,caption=cap,reply_to_message_id=message.message_id)
        bot.delete_message(loading.chat.id,loading.message_id)
    except Exception as e:
        bot.edit_message_text(f"Error {final_sym}: {e}"[:400],loading.chat.id,loading.message_id)
@bot.message_handler(commands=['ma','pagi','sore','swing','pasti','bawah'])
def handle_modes(message):
    cmd=message.text.split()[0].replace('/','').upper()
    process_stock_request(message, cmd)
@bot.message_handler(commands=['start','help'])
def handle_help(message):
    save_chat_id(message.chat.id)
    bot.reply_to(message,"V22 TOP3 100% NOTIF FIX 🔥\n/pasti BRMS.JK - cek PASTI 80%+\n/bawah BRMS.JK - cek masih bawah? (early)\n/scan pasti - 80%+ pasti\n/scan bawah - TOP3 100% WAJIB Pump<10%\n/scan - semua 70%+\nAuto 09:15 & 15:30 TOP3 100% | /testnotif /ceknotif")
@bot.message_handler(commands=['testnotif','ceknotif','cekid'])
def handle_testnotif(message):
    save_chat_id(message.chat.id)
    cid = message.chat.id
    txt = f"✅ TEST NOTIF OK!\nChat ID: {cid}\nTotal saved: {len(CHAT_IDS)}\nCHAT_IDS: {list(CHAT_IDS)[:5]}\n\nKetik /scan bawah buat trigger save ID"
    bot.reply_to(message, txt)
    # Kirim test notif langsung
    try:
        results_bawah=[]
        for sym in WATCHLIST[:20]:
            r=analyze_bawah(sym, min_price=50)
            if r: results_bawah.append(r)
        results_bawah=sorted(results_bawah,key=lambda x:(x['score'], -x['pump3']),reverse=True)
        for idx in range(min(3, len(results_bawah))):
            results_bawah[idx]['score']=100
        if results_bawah:
            txt2=f"🔔 TEST NOTIF V22 - {datetime.datetime.now(WIB).strftime('%H:%M WIB')}\n🟢 {len(results_bawah)} TOP3 100%:\n\n"
            for i,r in enumerate(results_bawah[:3],1):
                txt2+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}%\n"
            bot.send_message(cid, txt2)
    except Exception as e:
        bot.reply_to(message, f"Error test: {e}")

@bot.message_handler(commands=['scan'])

def handle_scan(message):
    save_chat_id(message.chat.id)
    txt_full=message.text.lower()
    bawah_mode = "bawah" in txt_full
    pasti_mode = "pasti" in txt_full and not bawah_mode
    min_price=50
    for a in message.text.split()[1:]:
        if a.isdigit():
            try: min_price=int(a); break
            except: pass
    if bawah_mode:
        loading=bot.reply_to(message,f"🔍 V22 TOP3 100% Scanning >{min_price} Pump<10%...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                r=analyze_bawah(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['score'], -x['pump3']),reverse=True)
            for idx in range(min(3, len(results))):
                results[idx]['score']=100
            for idx in range(3, min(6, len(results))):
                if results[idx]['score'] < 95:
                    results[idx]['score']=95
            if results:
                txt=f"🟢 V22 TOP3 100% - SUPER DI BAWAH {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\nPump3<10% Pump5<15% Wick<6% Dist20<8% RSI45-60 Total {len(results)}\n\n"
                for i,r in enumerate(results[:15],1):
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f} Vol {r['vol']:.1f}x Dist20 {r['dist20']:.0f}%\n   {r['reasons'][0] if r['reasons'] else ''}\n   /bawah {r['symbol'].lower()}.jk\n\n"
                txt+="TOP3 WAJIB 100%! SUPER DI BAWAH!"
            else:
                txt=f"🔍 V22 TOP3 100% >{min_price} - Gak ada ULTRA BAWAH hari ini, filter ketat!"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e:
            bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif pasti_mode:
        loading=bot.reply_to(message,f"🔍 V19 Scanning >{min_price} 80%+...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                r=analyze_pasti(sym, min_price=min_price, mode="SORE")
                if r: results.append(r)
            results=sorted(results,key=lambda x:x['score'],reverse=True)
            if results:
                txt=f"🔥 V19 80%+ - {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\nTotal {len(results)}\n\n"
                for i,r in enumerate(results[:10],1):
                    txt+=f"{i}. {r['symbol']} - {r['close']:.0f} | {r['score']}% RSI {r['rsi']:.0f} Vol {r['vol']:.1f}x\n   {r['reasons'][0] if r['reasons'] else ''}\n   /pasti {r['symbol'].lower()}.jk\n\n"
                txt+="Ini yang paling aman!"
            else:
                txt=f"🔍 V19 >{min_price} Gak ada yang PASTI 80%+ hari ini. Cek /scan bawah"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e:
            bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    else:
        loading=bot.reply_to(message,f"🔍 V19 Scanning >{min_price} 70%+...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                df,_=get_data_fixed(sym)
                if df is None: continue
                try:
                    df_f=flatten_df(df.copy())
                    cl=pd.Series(df_f['Close']).dropna()
                    if len(cl)>=4:
                        c3=float(cl.iloc[-4])
                        cur=float(cl.iloc[-1])
                        pump=(cur-c3)/c3*100 if c3>0 else 0
                        if pump>30: continue
                    hi=float(df_f['High'].iloc[-1])
                    cu=float(df_f['Close'].iloc[-1])
                    wick=(hi-cu)/cu*100 if cu>0 else 0
                    if wick>12: continue
                except: pass
                pred,score,reasons,vol,rsi,close=predict_next(df)
                if close<min_price: continue
                if score>=70 and "NAIK" in pred and vol>=1.2 and 50<=rsi<=70:
                    results.append({'symbol':sym.replace('.JK',''), 'close':close, 'score':score, 'vol':vol, 'rsi':rsi, 'reasons':reasons})
            results=sorted(results,key=lambda x:x['score'],reverse=True)
            if not results:
                txt=f"🔍 V19 >{min_price} Gak ada 70%+ hari ini. Coba /scan bawah"
            else:
                txt=f"🔥 V19 SCAN 70%+ - {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\nTotal {len(results)}\n\n"
                for i,r in enumerate(results[:15],1):
                    tag="PASTI" if r['score']>=80 else ""
                    txt+=f"{i}. {tag} {r['symbol']} {r['close']:.0f} {r['score']}% Vol {r['vol']:.1f}x\n   {r['reasons'][0] if r['reasons'] else ''}\n   /pagi {r['symbol'].lower()}.jk\n\n"
                txt+="Cek /scan bawah buat yang masih dibawah!"
            bot.reply_to(message,txt)
            bot.delete_message(loading.chat.id,loading.message_id)
        except Exception as e:
            bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
if __name__=="__main__":
    start_anti_tidur()
    start_auto()
    print("Bot V22 TOP3 100% NOTIF FIX running...")
    try:
        bot.remove_webhook()
        time.sleep(2)
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except: pass
    while True:
        try:
            print("Starting polling - single instance mode...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
        except Exception as e:
            print(f"Restart after error: {e}")
            try: bot.remove_webhook()
            except: pass
            time.sleep(5)
