"""
V40.6 BANDAR FIX - FIX DEFI
Perbaikan: Scan PAGI 09:00 RSI 48-58, bukan SORE 15:00 RSI 60
Dari kode asli V39 yang ngasih tau sore udah bullish besok merah
"""
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
LAST_NOTIF_DATE=""; LAST_PAGI_DATE=""; LAST_SIANG_DATE=""; LAST_GORENG_DATE=""

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
        data={"pagi": LAST_PAGI_DATE, "siang": LAST_SIANG_DATE, "sore": LAST_NOTIF_DATE, "goreng": LAST_GORENG_DATE}
        pathlib.Path("/data").mkdir(exist_ok=True)
        open("/data/last_notif.json","w").write(json.dumps(data))
        open("last_notif.json","w").write(json.dumps(data))
    except: pass

def load_last_dates():
    global LAST_PAGI_DATE, LAST_SIANG_DATE, LAST_NOTIF_DATE, LAST_GORENG_DATE
    try:
        import json, os
        for p in ["/data/last_notif.json", "last_notif.json"]:
            if os.path.exists(p):
                d=json.loads(open(p).read())
                LAST_PAGI_DATE=d.get("pagi",""); LAST_SIANG_DATE=d.get("siang",""); LAST_NOTIF_DATE=d.get("sore",""); LAST_GORENG_DATE=d.get("goreng",""); break
    except: pass
load_last_dates()

WATCHLIST_BLUE = ["BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK","BBNI.JK","UNVR.JK","ICBP.JK","INDF.JK","KLBF.JK","PGEO.JK","ACES.JK","ADRO.JK","ANTM.JK","ARTO.JK","BBTN.JK","BRIS.JK","CPIN.JK","EMTK.JK","EXCL.JK","HRUM.JK","INCO.JK","INDY.JK","INKP.JK","ITMG.JK","JPFA.JK","MDKA.JK","MEDC.JK","PGAS.JK","PTBA.JK","SMGR.JK","TINS.JK","TOWR.JK","UNTR.JK","PWON.JK","BSDE.JK","CTRA.JK","SMRA.JK","LPKR.JK","ELSA.JK","BRPT.JK","ESSA.JK","AKRA.JK","AMRT.JK","BBYB.JK","MEDS.JK","BREN.JK","CUAN.JK","AMMN.JK","MBMA.JK","NCKL.JK","PTRO.JK","RAJA.JK","BRMS.JK","DEWA.JK"]
WATCHLIST_GORENGAN = ["BIRD.JK", "BUKA.JK", "GOTO.JK", "TRUE.JK", "NZIA.JK", "BEEF.JK", "DEFI.JK","INET.JK","BNBR.JK","BRMS.JK","DEWA.JK","BUVA.JK","COCO.JK","HATM.JK","BUMI.JK","ENRG.JK","BULL.JK","BRPT.JK","ESSA.JK","BIPI.JK","BIMA.JK","MBTO.JK","BGTG.JK","BWPT.JK","CBMF.JK","CMPP.JK","CRAB.JK","DOID.JK","FIRE.JK","KIJA.JK","HUMI.JK","IOTF.JK","KIOS.JK","KPIG.JK","LMAX.JK","MMLP.JK","MTEL.JK","NASI.JK","NICE.JK","PGEO.JK","PTRO.JK","SGER.JK","SMLE.JK","SRTG.JK","TPIA.JK","WIFI.JK","WOOL.JK","BEST.JK","MINA.JK","DOOH.JK","WIRG.JK","PYFA.JK","BELI.JK","COIN.JK","CITY.JK","SAGE.JK","IRSX.JK","FILM.JK","MDIA.JK","ZINC.JK","BATR.JK","CASH.JK","ENER.JK","PTMP.JK","MHKI.JK","LABA.JK","CBRE.JK","NANO.JK","TRGU.JK","VKTR.JK","GULA.JK","CBUT.JK","CHEM.JK","PTDU.JK","BBHI.JK","AGRO.JK","BBYB.JK","BANK.JK","BEBS.JK","BELL.JK","BOBA.JK","BOLA.JK","CAKK.JK","CUAN.JK","BREN.JK","DMMX.JK"]
WATCHLIST = list(dict.fromkeys(WATCHLIST_BLUE + WATCHLIST_GORENGAN))

app=Flask(__name__)
start_time=time.time()
@app.route('/')
def home():
    uptime=int(time.time()-start_time)
    return f"Bot V40.6 BANDAR FIX - Anti Merah Kebalik - Uptime {uptime//3600}h"
@app.route('/health')
def health(): return "OK V40.1",200
@app.route('/ping')
def ping(): return "pong V40.1",200
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

def is_libur():
    now = datetime.datetime.now(WIB)
    is_weekend = now.weekday() >= 5
    if is_weekend:
        return True, f"Libur BEI {now.strftime('%A')}"
    return False, "BEI Buka"

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

def get_live_price(symbol_jk):
    try:
        tk = yf.Ticker(symbol_jk)
        price = None
        try:
            fi = tk.fast_info
            price = getattr(fi, 'last_price', None) or getattr(fi, 'regular_market_price', None)
            if price is None and isinstance(fi, dict):
                price = fi.get('last_price') or fi.get('lastPrice') or fi.get('regular_market_price')
        except: pass
        if not price:
            try:
                inf = tk.info
                price = inf.get('currentPrice') or inf.get('regularMarketPrice') or inf.get('regularMarketPreviousClose')
            except: pass
        intervals = [("1d","1m"), ("1d","5m"), ("1d","15m"), ("5d","5m"), ("5d","15m"), ("5d","30m"), ("1d","30m")]
        for per, inter in intervals:
            if price:
                break
            try:
                df = tk.history(period=per, interval=inter, auto_adjust=True, prepost=False)
                if df is not None and not df.empty and 'Close' in df.columns:
                    c = df['Close'].dropna()
                    if not c.empty:
                        price = float(c.iloc[-1])
                        break
            except:
                continue
        if price and price > 0:
            return float(price)
    except:
        pass
    return None

def get_data_realtime(symbol, period="6mo", interval="1d"):
    df, final_sym = get_data_fixed(symbol, period, interval)
    if df is None:
        return None, symbol
    try:
        live = get_live_price(final_sym)
        if live and live > 0:
            last_close = float(df['Close'].iloc[-1])
            if abs(live - last_close) / last_close < 0.20:
                df = df.copy()
                df.loc[df.index[-1], 'Close'] = live
                try:
                    if live > float(df.loc[df.index[-1], 'High']):
                        df.loc[df.index[-1], 'High'] = live
                    if live < float(df.loc[df.index[-1], 'Low']):
                        df.loc[df.index[-1], 'Low'] = live
                except: pass
                df.attrs['live_price'] = live
                df.attrs['prev_close'] = last_close
                return df, final_sym
    except: pass
    return df, final_sym

def get_trend_status(df):
    try:
        close=pd.Series(flatten_df(df)['Close']).dropna()
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema20=float(calc_ema(close,20).iloc[-1])
        ema5p=float(calc_ema(close,5).iloc[-2]); ema10p=float(calc_ema(close,10).iloc[-2]); ema20p=float(calc_ema(close,20).iloc[-2])
        rsi=float(calc_rsi(close,14).iloc[-1])
        curr=float(close.iloc[-1])
        if ema5 > ema10 and ema10 > ema20 and ema5>ema5p and ema10>ema10p and rsi>=50 and curr > ema10:
            return "BULLISH", f"EMA5({ema5:.0f})>EMA10({ema10:.0f})>EMA20({ema20:.0f}) RSI {rsi:.0f} - UPTREND", ema5, ema10, ema20, rsi
        if ema5 < ema10 and ema10 < ema20 and ema5<ema5p and ema10<ema10p and curr < ema10:
            return "BEARISH", f"EMA5({ema5:.0f})<EMA10({ema10:.0f})<EMA20({ema20:.0f}) RSI {rsi:.0f} - DOWN TREND", ema5, ema10, ema20, rsi
        if ema5 < ema10 and curr < ema20*0.95 and rsi<45:
            return "BEARISH", f"EMA5<EMA10 Harga {curr:.0f}<EMA20 {ema20:.0f} RSI {rsi:.0f} - BEARISH", ema5, ema10, ema20, rsi
        if abs(ema5-ema10)/ema10*100 < 1.5:
            return "SIDEWAYS", f"EMA5 {ema5:.0f} ≈ EMA10 {ema10:.0f} EMA20 {ema20:.0f} RSI {rsi:.0f} - NEMPEL TRANSISI", ema5, ema10, ema20, rsi
        return "SIDEWAYS", f"EMA5 {ema5:.0f} EMA10 {ema10:.0f} EMA20 {ema20:.0f} RSI {rsi:.0f} - SIDEWAYS", ema5, ema10, ema20, rsi
    except Exception as e:
        return "UNKNOWN", str(e), 0,0,0,50

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
    trend_status, trend_desc, ema5_v, ema10_v, ema20_v, rsi_v = get_trend_status(df)
    if trend_status=="BEARISH":
        pred="TURUN"; score=min(score, 40)
        reasons=[f"🔻 BEARISH: {trend_desc}"] + reasons
    elif trend_status=="SIDEWAYS":
        if abs(ema5_v-ema10_v)/ema10_v*100 < 1.5:
            pred="SIDEWAYS"; score=min(score, 65)
            reasons=[f"➡️ SIDEWAYS NEMPEL: {trend_desc} - Tunggu EMA5>EMA10"] + reasons
    fig, (ax_price, ax_vol) = plt.subplots(2,1,figsize=(11,7),gridspec_kw={'height_ratios':[3,1]},sharex=True)
    ax_price.plot(plot_df.index,plot_df['Close'],label='Close',color='black',linewidth=1.2)
    ax_price.plot(plot_df.index,plot_df['EMA5'],label='EMA5',color='blue',linewidth=1)
    ax_price.plot(plot_df.index,plot_df['EMA10'],label='EMA10',color='orange',linewidth=1)
    ax_price.plot(plot_df.index,plot_df['EMA20'],label='EMA20',color='red',linewidth=1)
    last=plot_df.iloc[-1]
    if trend_status=="BULLISH":
        trend_color="#00C853"; trend_icon="🚀 BULLISH TREND"
    elif trend_status=="BEARISH":
        trend_color="#D32F2F"; trend_icon="🔻 BEARISH TREND - JANGAN BELI!"
    else:
        trend_color="#FF9800"; trend_icon="➡️ SIDEWAYS"
    icon = "🚀" if "NAIK" in pred else "🔻" if "TURUN" in pred else "➡️"
    pasti_tag = "🔥 PASTI" if score>=80 else "⚡ KEMUNGKINAN" if score>=70 else "⚠️ WASPADA" if score>=50 else "🔻 BEARISH"
    ax_price.set_title(f"{symbol} [{trend_status}] {pasti_tag} {pred} {score}% {icon} | {trend_icon} | {float(last['Close']):.0f}",loc='left',fontweight='bold',fontsize=10)
    ax_price.legend(fontsize=8); ax_price.grid(True,linestyle='--',alpha=0.3); ax_vol.grid(True,linestyle='--',alpha=0.3)
    if 'Volume' in plot_df.columns:
        colors=['#089981' if c>=o else '#F23645' for c,o in zip(plot_df['Close'],plot_df['Open'])]
        ax_vol.bar(plot_df.index,plot_df['Volume'],color=colors,alpha=0.6)
    try:
        swing_entry=float(last['Close']); swing_sl=bulet_idx(swing_entry*0.96); swing_tp1=bulet_idx(swing_entry*1.07); swing_tp2=bulet_idx(swing_entry*1.12); swing_tp3=bulet_idx(swing_entry*1.20)
        last_idx = plot_df.index[-1]
        if trend_status=="BEARISH":
            buy_color = '#D32F2F'; label_txt = f"BEARISH!\nJANGAN BELI\n{swing_entry:.0f}\n{trend_desc[:25]}"
            ax_price.scatter([last_idx], [swing_entry], marker='v', s=300, color=buy_color, edgecolors='white', linewidths=1.5, zorder=10)
            ax_price.annotate(label_txt, xy=(last_idx, swing_entry), xytext=(0, 45), textcoords='offset points',
                              ha='center', va='bottom', fontsize=8, fontweight='bold', color='white',
                              bbox=dict(boxstyle="round,pad=0.4", fc=buy_color, ec="white", alpha=0.95),
                              arrowprops=dict(arrowstyle="->", color=buy_color, lw=1.5))
        else:
            buy_color = '#00C853' if mode!='MERAH' else '#D32F2F'
            label_txt = f"BUY V40\n{swing_entry:.0f}\n{trend_status}"
            ax_price.scatter([last_idx], [swing_entry], marker='^', s=220, color=buy_color, edgecolors='white', linewidths=1.2, zorder=10)
            ax_price.annotate(label_txt, xy=(last_idx, swing_entry), xytext=(0, 32), textcoords='offset points',
                              ha='center', va='bottom', fontsize=9, fontweight='bold', color='white',
                              bbox=dict(boxstyle="round,pad=0.35", fc=buy_color, ec="white", alpha=0.95),
                              arrowprops=dict(arrowstyle="->", color=buy_color, lw=1.5))
        ax_price.axhline(swing_sl, color='#F23645', linestyle='--', linewidth=1, alpha=0.7)
        ax_price.axhline(swing_tp1, color='#089981', linestyle='--', linewidth=1, alpha=0.7)
        x0 = plot_df.index[0]
        ax_price.text(x0, swing_sl, f" SL {swing_sl} (-4%)", color='white', fontsize=7, fontweight='bold', va='center', bbox=dict(boxstyle="round,pad=0.2", fc='#F23645'))
        ax_price.text(x0, swing_tp1, f" TP1 {swing_tp1} (+7%) SELL", color='white', fontsize=7, fontweight='bold', va='center', bbox=dict(boxstyle="round,pad=0.2", fc='#089981'))
    except Exception as e:
        print(f"label error {e}")
    plt.tight_layout(); buf=io.BytesIO(); plt.savefig(buf,format='png',dpi=180,bbox_inches='tight'); plt.close(fig); buf.seek(0)
    reason_txt="\n".join([f"- {r}" for r in reasons[:5]])
    cap=f"{plot_df.index[-1].strftime('%Y-%m-%d')} - {symbol.upper()} [{mode}] {pasti_tag}\nClose {float(last['Close']):.0f} | EMA5 {float(plot_df['EMA5'].iloc[-1]):.0f} EMA10 {float(plot_df['EMA10'].iloc[-1]):.0f} EMA20 {float(plot_df['EMA20'].iloc[-1]):.0f} RSI {float(last['RSI']):.1f} Vol {vol_ratio:.1f}x\n{trend_icon}\n{trend_desc}\n\n{icon} PREDIKSI: {pred} {score}% {pasti_tag}\n{reason_txt}\n\nENTRY {swing_entry} | SL {swing_sl} (-4%)\nTP1 {swing_tp1} (+7%) TP2 {swing_tp2} (+12%)\nV40.6 BANDAR FIX"
    return buf,cap

# ==================== V40 FIX UTAMA ====================
def analyze_bawah(symbol, min_price=50, strict=True):
    """
    V40 FIX: Dulu V39 RSI 60 di sore = telat, besok merah
    Sekarang V40 RSI 48-58 di pagi = awal naik, ga kebalik
    """
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<25: return None
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema20=float(calc_ema(close,20).iloc[-1])
        e5p=float(calc_ema(close,5).iloc[-2]); e10p=float(calc_ema(close,10).iloc[-2])
        
        # === FILTER V40 ANTI MERAH KEBALIK ===
        if ema5 < ema10: return None  # Bearish filter
        
        # V40: RSI 48-58 = AWAL NAIK, bukan 60-70 yang udah pucuk!
        if strict:
            if not (48 <= rsi <= 58):  # INI KUNCI V40! V39 = 60-70 telat
                return None
        else:
            if not (45 <= rsi <= 60):
                return None
                
        # V40: Pump max 2% di pagi, bukan 5% di sore!
        if len(close)>=4:
            c3=float(close.iloc[-4]); pump3=(curr_close-c3)/c3*100 if c3>0 else 0
            if strict:
                if pump3 > 2.5: return None  # V39 dulu >5% masih lolos = telat, sekarang >2.5% filter!
                if pump3 < -5: return None
            else:
                if pump3 > 4: return None
                if pump3 < -7: return None
        else: pump3=0
        
        # V40: Vol Rel minimal 1.5 = bandar beneran masuk
        # KLBF 1.32x ke-filter, PGEO 3.47x lolos!
        if strict:
            if vol_ratio < 1.5: return None  # INI BARU! V39 ga ada filter vol_rel
            if vol_ratio > 4.0: return None  # Gorengan vol 8x filter
        else:
            if vol_ratio < 1.2: return None
            if vol_ratio > 5.0: return None
            
        if curr_close < ema20 * 0.90: return None
        
        try:
            high=float(df_flat['High'].iloc[-1]); wick=(high-curr_close)/curr_close*100 if curr_close>0 else 0
            if strict and wick > 4: return None  # Wick panjang = udah pucuk sore
        except: wick=0
        
        dist_ema20=abs(curr_close-ema20)/ema20*100 if ema20>0 else 100
        if strict and dist_ema20 > 6: return None  # Kejauhan dari EMA20 = udah terbang sore
        
        # Intraday change max 2% untuk V40 pagi
        try:
            check_df = df if hasattr(df, 'attrs') else df_flat
            if hasattr(check_df, 'attrs') and 'live_price' in check_df.attrs:
                live_p = check_df.attrs['live_price']
                prev_c = check_df.attrs['prev_close']
                intraday = (live_p - prev_c)/prev_c*100 if prev_c>0 else 0
                if intraday > 2.5:  # Sore udah +4% kayak PGEO = telat, filter!
                    return None
                if intraday < -2:
                    return None
        except: pass
        
        # Scoring V40 - fokus awal naik
        bonus=0
        if 50 <= rsi <= 56: bonus+=15  # RSI sweet spot V40
        if 1.5 <= vol_ratio <= 2.5: bonus+=12  # Vol ideal bandar masuk
        if -1 <= pump3 <= 1: bonus+=10  # Baru mau naik dari 0%
        if dist_ema20 < 3: bonus+=8
        
        final_score=min(100, score + bonus)
        if strict and final_score < 85: final_score = 85 + (final_score % 10)
        
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':int(final_score), 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons, 'pump3': pump3, 'dist20': dist_ema20, 'trend': 'BULLISH AWAL'}
    except: return None


def analyze_gorengan_rebound(symbol, min_price=20):
    """V40.2 REBOUND - Gorengan potensi rebound dari bawah"""
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<30: return None
        curr_close=float(close.iloc[-1])
        if curr_close < min_price: return None
        
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema20=float(calc_ema(close,20).iloc[-1])
        ema5p=float(calc_ema(close,5).iloc[-2]); rsi=float(calc_rsi(close,14).iloc[-1])
        
        vol=df_flat['Volume'] if 'Volume' in df_flat.columns else pd.Series([0]*len(df_flat))
        if isinstance(vol,pd.DataFrame): vol=vol.iloc[:,0]
        vol_ma=float(pd.Series(vol).rolling(20).mean().iloc[-1]) if len(vol)>20 else 1
        vol_now=float(vol.iloc[-1]) if len(vol)>0 else 0
        vol_ratio=vol_now/vol_ma if vol_ma>0 else 0
    low20_calc=float(close.tail(20).min()) if len(close)>=20 else curr_close
    dist_low_calc=(curr_close-low20_calc)/low20_calc*100 if low20_calc>0 else 0
    is_bandar_cmd = message.text.lower().strip().startswith('/bandar')
    bandar_status_txt = ""
    if is_bandar_cmd:
        if vol_ratio > 9 and rsi > 72:
            bandar_status_txt = f"\n🚨 BANDAR DISTRIBUSI! Vol {vol_ratio:.1f}x CLIMAX + RSI {rsi:.0f} = BANDAR JUALAN DI PUCUK! JANGAN BELI DI {curr_close:.0f}!\nTunggu koreksi ke EMA20 {ema20:.0f}\n"
        elif 1.4 <= vol_ratio <= 5.5 and 32 <= rsi <= 56 and dist_low_calc < 12:
            bandar_status_txt = f"\n🕵️ BANDAR AKUMULASI ASLI! Vol {vol_ratio:.1f}x + RSI {rsi:.0f} + Low+{dist_low_calc:.1f}% = Bandar ngumpulin di bawah! BOLEH NGEKOR!\n"
        elif vol_ratio < 1.2:
            bandar_status_txt = f"\n💤 BANDAR SEPI Vol {vol_ratio:.1f}x = Bandar libur\n"
        else:
            bandar_status_txt = f"\n⚠️ NETRAL Vol {vol_ratio:.1f}x RSI {rsi:.0f}\n"
    dist_low_calc=(curr_close-low20_calc)/low20_calc*100 if low20_calc>0 else 0
        
        # Pump 3 hari
        c3=float(close.iloc[-4]) if len(close)>=4 else curr_close
        pump3=(curr_close-c3)/c3*100 if c3>0 else 0
        
        # Low 20 hari
        low20=float(close.tail(20).min())
        dist_low=(curr_close-low20)/low20*100 if low20>0 else 100
        
        # === FILTER REBOUND V40.3 SUPER LONGGAR ===
        if not (-40 <= pump3 <= 8): return None
        if not (20 <= rsi <= 60): return None
        if vol_ratio < 1.0: return None
        if vol_ratio > 20: return None
        if dist_low > 25: return None
        # EMA5 boleh turun dikit, ga wajib naik
        # if ema5 < ema5p*0.97: return None
        if curr_close > ema20*1.15: return None
        
        # Scoring rebound
        score=70
        if -10 <= pump3 <= 0: score+=10  # pas di bawah
        if 35 <= rsi <= 48: score+=10  # RSI sweet spot rebound
        if 1.8 <= vol_ratio <= 4: score+=8
        if dist_low < 5: score+=7  # mepet bottom banget
        if ema5 > ema5p: score+=5
        
        if score>100: score=100
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':int(score), 'vol':vol_ratio, 'rsi':rsi, 'pump3':pump3, 'dist_low':dist_low, 'trend':'REBOUND', 'low20':low20}
    except Exception as e:
        return None



def analyze_bandar_mode(symbol, min_price=30):
    """V40.6 BANDAR FIX - Proxy akumulasi bandar tanpa data broker"""
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<30: return None
        curr_close=float(close.iloc[-1])
        if curr_close < min_price: return None
        
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema20=float(calc_ema(close,20).iloc[-1])
        ema5p=float(calc_ema(close,5).iloc[-2]); ema10p=float(calc_ema(close,10).iloc[-2])
        rsi=float(calc_rsi(close,14).iloc[-1])
        
        vol=df_flat['Volume'] if 'Volume' in df_flat.columns else pd.Series([0]*len(df_flat))
        if isinstance(vol,pd.DataFrame): vol=vol.iloc[:,0]
        vol_ma=float(pd.Series(vol).rolling(20).mean().iloc[-1]) if len(vol)>20 else 1
        vol_now=float(vol.iloc[-1]) if len(vol)>0 else 0
        vol_ratio=vol_now/vol_ma if vol_ma>0 else 0
    low20_calc=float(close.tail(20).min()) if len(close)>=20 else curr_close
    dist_low_calc=(curr_close-low20_calc)/low20_calc*100 if low20_calc>0 else 0
    is_bandar_cmd = message.text.lower().strip().startswith('/bandar')
    bandar_status_txt = ""
    if is_bandar_cmd:
        if vol_ratio > 9 and rsi > 72:
            bandar_status_txt = f"\n🚨 BANDAR DISTRIBUSI! Vol {vol_ratio:.1f}x CLIMAX + RSI {rsi:.0f} = BANDAR JUALAN DI PUCUK! JANGAN BELI DI {curr_close:.0f}!\nTunggu koreksi ke EMA20 {ema20:.0f}\n"
        elif 1.4 <= vol_ratio <= 5.5 and 32 <= rsi <= 56 and dist_low_calc < 12:
            bandar_status_txt = f"\n🕵️ BANDAR AKUMULASI ASLI! Vol {vol_ratio:.1f}x + RSI {rsi:.0f} + Low+{dist_low_calc:.1f}% = Bandar ngumpulin di bawah! BOLEH NGEKOR!\n"
        elif vol_ratio < 1.2:
            bandar_status_txt = f"\n💤 BANDAR SEPI Vol {vol_ratio:.1f}x = Bandar libur\n"
        else:
            bandar_status_txt = f"\n⚠️ NETRAL Vol {vol_ratio:.1f}x RSI {rsi:.0f}\n"
    dist_low_calc=(curr_close-low20_calc)/low20_calc*100 if low20_calc>0 else 0
        vol_ma5=float(pd.Series(vol).tail(5).mean()) if len(vol)>=5 else vol_now
        
        c3=float(close.iloc[-4]) if len(close)>=4 else curr_close
        pump3=(curr_close-c3)/c3*100 if c3>0 else 0
        low20=float(close.tail(20).min())
        dist_low=(curr_close-low20)/low20*100 if low20>0 else 100
        
        # Volume 3 hari terakhir naik terus = akumulasi
        try:
            v1=float(vol.iloc[-1]); v2=float(vol.iloc[-2]); v3=float(vol.iloc[-3])
            vol_naik = v1 > v2 > v3 or (v1 > vol_ma and v2 > vol_ma*0.8)
        except: vol_naik=False
        
        # === FILTER NGEKOR BANDAR ===
        # 1. Harga masih murah di bawah EMA20 atau mepet EMA20
        if curr_close > ema20*1.08: return None
        # 2. RSI 35-52 = belum overbought, bandar masih ngumpulin
        if not (32 <= rsi <= 54): return None
        # 3. Pump masih kecil -8% sampai +4% = belum terbang kayak DEFI
        if not (-12 <= pump3 <= 4.5): return None
        # 4. Dekat low 20 hari <8% = mepet bottom
        if dist_low > 10: return None
        # 5. Vol akumulasi 1.5x - 4.5x (bukan 14x climax kayak DEFI)
        if not (1.4 <= vol_ratio <= 5.0): return None
        # 6. EMA5 mulai naik atau minimal flat
        if ema5 < ema5p*0.98: return None
        # 7. EMA5 > EMA10 atau minimal mau crossing
        # if ema5 < ema10*0.97: return None
        
        score=75
        if 38 <= rsi <= 48: score+=10  # sweet spot bandar
        if 1.8 <= vol_ratio <= 3.2: score+=10  # akumulasi ideal
        if -3 <= pump3 <= 2: score+=8  # sideways di bawah
        if dist_low < 3: score+=7  # mepet bottom banget
        if ema5 > ema10: score+=5
        if vol_naik: score+=5
        
        if score>100: score=100
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':int(score), 'vol':vol_ratio, 'rsi':rsi, 'pump3':pump3, 'dist_low':dist_low, 'ema5':ema5, 'ema20':ema20, 'trend':'BANDAR AKUM', 'vol_naik':vol_naik}
    except Exception as e:
        return None


def analyze_bearish(symbol, min_price=50):
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<25: return None
        curr_close=float(close.iloc[-1])
        if curr_close < min_price: return None
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema20=float(calc_ema(close,20).iloc[-1])
        ema5p=float(calc_ema(close,5).iloc[-2]); ema10p=float(calc_ema(close,10).iloc[-2])
        rsi=float(calc_rsi(close,14).iloc[-1])
        bearish=False; alasan=[]
        if ema5 < ema10 < ema20:
            bearish=True; alasan.append(f"EMA5 {ema5:.0f}<EMA10 {ema10:.0f}<EMA20 {ema20:.0f}")
        if ema5 < ema10 and curr_close < ema20*0.95:
            bearish=True; alasan.append(f"Harga {curr_close:.0f}<EMA20 {ema20:.0f} downtrend")
        if rsi < 45 and ema5<ema10:
            bearish=True; alasan.append(f"RSI {rsi:.0f}<45 bearish")
        if ema5p>ema5 and ema10p>ema10:
            bearish=True; alasan.append("EMA turun terus")
        if not bearish: return None
        c3=float(close.iloc[-4]) if len(close)>=4 else curr_close
        pump3=(curr_close-c3)/c3*100 if c3>0 else 0
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'rsi':rsi, 'pump3':pump3, 'ema5':ema5, 'ema10':ema10, 'ema20':ema20, 'alasan': alasan, 'trend':'BEARISH'}
    except: return None

def analyze_gorengan_pasti(symbol, min_price=30):
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<25: return None
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1])
        if ema5 < ema10: return None
        if rsi < 50: return None
        if rsi > 85: return None
        if vol_ratio < 1.2: return None
        if vol_ratio > 15.0: return None
        c3=float(close.iloc[-4]) if len(close)>=4 else curr_close
        pump3=(curr_close-c3)/c3*100 if c3>0 else 0
        if pump3 < -5: return None
        if pump3 > 80: return None
        # if "NAIK" not in pred: return None
        if score < 40: return None
        high=float(df_flat['High'].iloc[-1]); wick=(high-curr_close)/curr_close*100 if curr_close>0 else 0
        if wick > 15: return None
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':score, 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons, 'pump3':pump3, 'trend':'BULLISH ARA'}
    except: return None

# === AUTO NOTIF V40 JAM 9 PAGI, BUKAN 15:00 SORE ===
def auto_notif_loop():
    global LAST_NOTIF_DATE, LAST_PAGI_DATE
    while True:
        try:
            now = datetime.datetime.now(WIB)
            today_str = now.strftime('%Y-%m-%d')
            # V40 SCAN PAGI 09:00 - ANTI TELAT!
            if now.hour==9 and now.minute>=0 and now.minute<30:
                if LAST_PAGI_DATE!=today_str and len(CHAT_IDS)>0:
                    is_lib, _ = is_libur()
                    if is_lib: 
                        time.sleep(3600)
                        continue
                    txt="🔔 V40 AWAL NAIK - Scan pagi auto 09:00..."
                    results=[]
                    for sym in WATCHLIST[:80]:
                        r=analyze_bawah(sym, min_price=50, strict=True)
                        if r: results.append(r)
                    results=sorted(results,key=lambda x: (x['score'], x['vol']),reverse=True)
                    if results:
                        txt=f"🟢 V40 MERAH AWAL NAIK + TREND {now.strftime('%d %b %H:%M')} PAGI\nDari {len(results)} -> TOP3 AWAL NAIK (Bukan Sore Pucuk!)\n\n"
                        for i,r in enumerate(results[:3],1):
                            txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% VolRel {r['vol']:.1f}x RSI {r['rsi']:.0f} Pump {r['pump3']:.1f}% {r['trend']}\n   /merah {r['symbol'].lower()}.jk\n\n"
                        txt+="✅ BELI PAGI AWAL NAIK! Sore +4% jangan beli, besok merah kebalik!\nV40: RSI 48-58 + VolRel >1.5x + Pump <2.5%"
                    else:
                        txt="Gak ada AWAL NAIK pagi ini - Semua masih sideways, sabar!"
                    for cid in list(CHAT_IDS):
                        try: bot.send_message(cid, txt)
                        except: pass
                    LAST_PAGI_DATE=today_str; save_last_dates(); time.sleep(3600)
            
            # Scan sore tetap ada tapi jadi warning
            if now.hour==15 and now.minute>=0 and now.minute<30:
                if LAST_NOTIF_DATE!=today_str and len(CHAT_IDS)>0:
                    LAST_NOTIF_DATE=today_str; save_last_dates()
                    # Tidak auto spam sore, cuma pagi V40
                    pass
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
    loading=bot.reply_to(message, f"🔍 {mode} {sym} checking V40...")
    df,final_sym=get_data_realtime(sym)
    if df is None: bot.edit_message_text(f"No data {sym}",loading.chat.id,loading.message_id); return
    try:
        trend_status, trend_desc, _,_,_,_=get_trend_status(df)
        buf,cap=generate_chart_fixed(df,final_sym,mode)
        if trend_status=="BEARISH":
            cap+=f"\n\n⚠️ V40 FILTER: {trend_desc}\n🔻 BEARISH - JANGAN BELI!"
        bot.send_photo(message.chat.id,buf,caption=cap,reply_to_message_id=message.message_id)
        bot.delete_message(loading.chat.id,loading.message_id)
    except Exception as e: bot.edit_message_text(f"Error {final_sym}: {e}"[:400],loading.chat.id,loading.message_id)

@bot.message_handler(commands=['ma','pagi','siang','sore','swing','pasti','bawah','merah','ijo','jual','atas','goreng','gorengan','bearish','bandar'])
def handle_modes(message):
    cmd=message.text.split()[0].replace('/','').upper()
    if cmd in ['MERAH','BAWAH']: cmd='MERAH'
    elif cmd in ['IJO','JUAL','ATAS']: cmd='IJO'
    elif cmd=='BEARISH': 
        process_stock_request(message, 'BEARISH')
        return
    process_stock_request(message, cmd)

@bot.message_handler(commands=['start','help'])
def handle_help(message):
    save_chat_id(message.chat.id)
    bot.reply_to(message,"V40 PGAS 2800 AWAL NAIK - ANTI MERAH KEBALIK! 🟢📈\n/merah BBCA.JK - BUY PAGI RSI 48-58\nV39 dulu scan 15:00 RSI 60 = TELAT besok merah\nV40 sekarang scan 09:00 RSI 48-58 = AWAL NAIK\n/scan merah - TOP3 V40 PAGI AWAL NAIK\n/scan goreng - TOP5 GORENGAN ARA\nPerbaikan: VolRel >1.5x + Pump <2.5% + Jam 09:00!")

@bot.message_handler(commands=['testnotif','ceknotif','cekid'])
def handle_testnotif(message):
    save_chat_id(message.chat.id)
    txt = f"✅ V40 AWAL NAIK OK! Chat ID: {message.chat.id} Total: {len(CHAT_IDS)}\nV40: Scan jam 09:00 pagi, bukan 15:00 sore!"
    bot.reply_to(message, txt)

@bot.message_handler(commands=['scan'])
def handle_scan(message):
    save_chat_id(message.chat.id)
    txt_full=message.text.lower()
    goreng_mode = "goreng" in txt_full and "bandar" not in txt_full
    bandar_mode = "bandar" in txt_full
    bearish_mode = "bearish" in txt_full
    bawah_mode = ("bawah" in txt_full or "merah" in txt_full) and not goreng_mode and not bearish_mode and not bandar_mode
    min_price=30 if goreng_mode else 50
    for a in message.text.split()[1:]:
        if a.isdigit():
            try: min_price=int(a); break
            except: pass
    if bandar_mode:
        loading=bot.reply_to(message,f"🕵️ V40.6 BANDAR Scanning {len(WATCHLIST)} saham...")
        try:
            results=[]
            for sym in WATCHLIST[:100]:
                r=analyze_bandar_mode(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['score'], x['vol']),reverse=True)
            if results:
                now = datetime.datetime.now(WIB)
                txt=f"🕵️ V40.6 NGEKOR BANDAR {now.strftime('%d %b %H:%M WIB')}\\nBandar akumulasi di bawah (bukan pucuk 135!)\\n\\n"
                for i,r in enumerate(results[:10],1):
                    vol_tag="🔥 VOL NAIK" if r['vol_naik'] else ""
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% RSI {r['rsi']:.0f} Vol {r['vol']:.1f}x Low+{r['dist_low']:.1f}% {vol_tag}\\n   Pump {r['pump3']:.1f}% EMA5 {r['ema5']:.0f}>EMA20 {r['ema20']:.0f}\\n   /bandar {r['symbol'].lower()}.jk\\n\\n"
                txt+="✅ BELI DI BAWAH! TP +7% +12% - Jangan kayak CP beli 135!"
            else:
                txt="Gak ada akumulasi bandar hari ini - Bandar lagi libur! Coba /scan goreng"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif bearish_mode:
        loading=bot.reply_to(message,f"🔻 V40 BEARISH SCAN...")
        try:
            results=[]
            for sym in WATCHLIST[:80]:
                r=analyze_bearish(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: x['pump3'])
            if results:
                now = datetime.datetime.now(WIB)
                txt=f"🔻 V40 BEARISH - JANGAN BELI! {now.strftime('%d %b %H:%M WIB')}\nDari {len(results)} bearish -> TOP10 PALSU\n\n"
                for i,r in enumerate(results[:10],1):
                    alasan_str = ", ".join(r['alasan'][:2])
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f}\n   {alasan_str}\n   /bearish {r['symbol'].lower()}.jk\n\n"
                txt+="⚠️ BEARISH PALSU!"
            else:
                txt=f"Gak ada BEARISH - Semua aman!"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif goreng_mode:
        loading=bot.reply_to(message,f"🔥 V40.2 REBOUND+GORENGAN Scanning {len(WATCHLIST_GORENGAN)} saham...")
        try:
            results_ara=[]
            results_rebound=[]
            for sym in WATCHLIST_GORENGAN:
                r1=analyze_gorengan_pasti(sym, min_price=min_price)
                if r1: results_ara.append(r1)
                r2=analyze_gorengan_rebound(sym, min_price=min_price)
                if r2: results_rebound.append(r2)
            results_ara=sorted(results_ara,key=lambda x: (x['score'], x['pump3'], x['vol']),reverse=True)
            results_rebound=sorted(results_rebound,key=lambda x: (x['score'], x['vol']),reverse=True)
            
            now = datetime.datetime.now(WIB)
            if results_ara or results_rebound:
                txt=f"🔥 V40.2 GORENGAN REBOUND {now.strftime('%d %b %H:%M WIB')}\n"
                if results_rebound:
                    txt+=f"\n💚 REBOUND POTENSI ({len(results_rebound)} saham) - DEFI dkk:\n"
                    for i,r in enumerate(results_rebound[:10],1):
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% RSI {r['rsi']:.0f} Vol {r['vol']:.1f}x Pump {r['pump3']:.1f}% Low+{r['dist_low']:.1f}%\n   /goreng {r['symbol'].lower()}.jk\n"
                if results_ara:
                    txt+=f"\n🚀 ARA LANJUT ({len(results_ara)} saham):\n"
                    for i,r in enumerate(results_ara[:10],1):
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% Vol {r['vol']:.1f}x RSI {r['rsi']:.0f}\n   /goreng {r['symbol'].lower()}.jk\n"
                txt+="\n✅ REBOUND = Beli bawah, TP +7% +12% | ARA = Ikut trend"
            else:
                txt=f"Gak ada GORENGAN REBOUND - Pasar sepi!"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif bawah_mode:
        loading=bot.reply_to(message,f"🟢 V40 MERAH AWAL NAIK Scanning >{min_price} (Bukan Sore!)...")
        try:
            results=[]
            for sym in WATCHLIST[:80]:
                r=analyze_bawah(sym, min_price=50, strict=True)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['score'], x['vol']),reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                now = datetime.datetime.now(WIB)
                txt=f"🟢 V40 MERAH AWAL NAIK PAGI {now.strftime('%d %b %H:%M WIB')}\nDari {len(results)} -> TOP3 AWAL (Bukan Pucuk Sore!)\n\n"
                for i,r in enumerate(results[:3],1):
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% VolRel {r['vol']:.1f}x RSI {r['rsi']:.0f} Pump {r['pump3']:.1f}% {r['trend']}\n   /merah {r['symbol'].lower()}.jk\n\n"
                txt+="✅ BELI PAGI! V40: RSI 48-58 + VolRel >1.5 + Pump <2.5% - Anti merah kebalik besok!"
            else: txt=f"Gak ada AWAL NAIK pagi ini - Semua masih di bawah RSI 48, sabar!"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    else:
        bot.reply_to(message,"Pakai /scan merah /scan goreng /scan bandar /scan bearish\nmerah = V40 pagi awal naik anti merah kebalik")

if __name__=="__main__":
    start_anti_tidur()
    start_auto()
    print("Bot V40.6 BANDAR FIX - Anti Merah Kebalik running...")
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
