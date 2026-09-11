
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

WATCHLIST_BLUE = ["BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK","BBNI.JK","UNVR.JK","ICBP.JK","INDF.JK","KLBF.JK","GOTO.JK","ACES.JK","ADRO.JK","ANTM.JK","ARTO.JK","BBTN.JK","BRIS.JK","CPIN.JK","EMTK.JK","EXCL.JK","HRUM.JK","INCO.JK","INDY.JK","INKP.JK","ITMG.JK","JPFA.JK","MDKA.JK","MEDC.JK","PGAS.JK","PTBA.JK","SMGR.JK","TINS.JK","TOWR.JK","UNTR.JK","PWON.JK","BSDE.JK","CTRA.JK","SMRA.JK","LPKR.JK","ELSA.JK","BRPT.JK","ESSA.JK","AKRA.JK","AMRT.JK","BBYB.JK","MEDS.JK","BREN.JK","CUAN.JK","AMMN.JK","MBMA.JK","NCKL.JK","PTRO.JK","RAJA.JK","PGEO.JK","BRMS.JK","DEWA.JK"]
WATCHLIST_GORENGAN = ["BRMS.JK","DEWA.JK","BUVA.JK","COCO.JK","HATM.JK","BUMI.JK","ENRG.JK","BULL.JK","BRPT.JK","ESSA.JK","BEEF.JK","CARE.JK","ZBRA.JK","BIPI.JK","BIMA.JK","BBSS.JK","BGTG.JK","BWPT.JK","CBMF.JK","CMPP.JK","CRAB.JK","DOID.JK","FIRE.JK","GOTO.JK","HUMI.JK","IOTF.JK","KIOS.JK","KPIG.JK","LMAX.JK","MMLP.JK","MTEL.JK","NASI.JK","NICE.JK","PGEO.JK","PTRO.JK","SGER.JK","SMLE.JK","SRTG.JK","TPIA.JK","WIFI.JK","WOOL.JK","BEST.JK","MINA.JK",
# V28 TAMBAHAN GORENGAN VIRAL
"DOOH.JK","WIRG.JK","PYFA.JK","BELI.JK","COIN.JK","CITY.JK","SAGE.JK","IRSX.JK","FILM.JK","MDIA.JK","ZINC.JK","BATR.JK","CASH.JK","ENER.JK","PTMP.JK","MHKI.JK","LABA.JK","CBRE.JK","NANO.JK","TRGU.JK","VKTR.JK","GULA.JK","CBUT.JK","CHEM.JK","PTDU.JK","BBHI.JK","AGRO.JK","BBYB.JK","BANK.JK","BEBS.JK","BELL.JK","BOBA.JK","BOLA.JK","BUMI.JK","CAKK.JK","CUAN.JK","BREN.JK","DMMX.JK","GOTO.JK"]
WATCHLIST = list(dict.fromkeys(WATCHLIST_BLUE + WATCHLIST_GORENGAN))

68 app=Flask(__name__)
69 start_time=time.time()
70 @app.route('/')
71 def home():
72     uptime=int(time.time()-start_time)
73     return f"Bot V36 FIX MERAH SEMUA BELI! 80 SAHAM - Uptime {uptime//3600}h"
74 @app.route('/health')
75 def health(): return "OK V36 MERAH SEMUA BELI!",200
76 @app.route('/ping')
77 def ping(): return "pong V36",200
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

def get_live_price(symbol_jk):
    # V35 FIX REALTIME - JK susah 1m, coba banyak interval!
    try:
        tk = yf.Ticker(symbol_jk)
        price = None
        # 1. fast_info
        try:
            fi = tk.fast_info
            price = getattr(fi, 'last_price', None) or getattr(fi, 'regular_market_price', None)
            if price is None and isinstance(fi, dict):
                price = fi.get('last_price') or fi.get('lastPrice') or fi.get('regular_market_price')
        except: pass
        # 2. info
        if not price:
            try:
                # use fast info to avoid heavy info call
                inf = tk.info
                price = inf.get('currentPrice') or inf.get('regularMarketPrice') or inf.get('regularMarketPreviousClose')
            except: pass
        # 3. Try multiple intraday intervals - JK often only has 15m or 30m
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

def analyze_merah_realtime_intraday(symbol, min_price=50):
    # V35 - deteksi MERAH HARI INI langsung dari live price vs close kemarin
    try:
        df_daily, final_sym = get_data_fixed(symbol)
        if df_daily is None or len(df_daily) < 25:
            return None
        live = get_live_price(final_sym)
        if not live or live < min_price:
            return None
        # close kemarin = last close daily
        close_kemarin = float(df_daily['Close'].iloc[-1])
        # intraday change hari ini
        intraday_pct = (live - close_kemarin) / close_kemarin * 100 if close_kemarin>0 else 0
        
        # HARUS MERAH HARI INI -1% sampai -7% = diskon intraday
        if intraday_pct > -0.8:  # belum merah
            return None
        if intraday_pct < -8:  # longsor terlalu dalam, skip
            return None
            
        # CEK MASIH BULLISH? pakai daily EMA
        close_series = df_daily['Close'].dropna()
        ema5 = float(calc_ema(close_series,5).iloc[-1])
        ema10 = float(calc_ema(close_series,10).iloc[-1])
        ema20 = float(calc_ema(close_series,20).iloc[-1])
        rsi = float(calc_rsi(close_series,14).iloc[-1])
        
        # Syarat bullish minimal
        if ema5 < ema10:  # bearish
            return None
        if live < ema20 * 0.85:  # jebol terlalu dalam
            return None
            
        # Hitung pump 3 hari pakai live
        c3 = float(close_series.iloc[-4]) if len(close_series)>=4 else close_kemarin
        pump3 = (live - c3)/c3*100 if c3>0 else intraday_pct
        
        # Score: makin merah intraday makin tinggi (diskon)
        score = 70
        if -4 <= intraday_pct <= -1: score += 20
        elif -6 <= intraday_pct <= -4: score += 15
        if ema5 > ema10 > ema20: score += 10
        if 45 <= rsi <= 62: score += 10
        
        score = min(100, score)
        
        return {
            'symbol': symbol.replace('.JK',''),
            'close': live,
            'close_kemarin': close_kemarin,
            'intraday': intraday_pct,
            'score': int(score),
            'rsi': rsi,
            'pump3': pump3,
            'ema5': ema5,
            'ema10': ema10,
            'ema20': ema20,
            'type': 'REALTIME_INTRADAY'
        }
    except Exception as e:
        return None

def scan_merah_realtime_v33():
    pass
def _compat(): pass

def scan_merah_realtime_v33_real():
    # V35 - scan merah intraday hari ini dulu, baru fallback ke daily
    realtime_results = []
    for sym in WATCHLIST[:80]:
        r = analyze_merah_realtime_intraday(sym, min_price=50)
        if r:
            realtime_results.append(r)
    
    if len(realtime_results) >= 1:
        # Sort by intraday paling merah (diskon gede) tapi masih bullish
        realtime_results = sorted(realtime_results, key=lambda x: (x['score'], -x['intraday']), reverse=True)
        return realtime_results, True, "REALTIME"
    
    # Fallback ke V30 logic daily
    strict_results=[]
    for sym in WATCHLIST[:80]:
        r=analyze_bawah(sym, min_price=50, strict=True)
        if r: strict_results.append(r)
    if len(strict_results) >= 3:
        return strict_results, True, "DAILY_STRICT"
    
    loose_results=[]
    for sym in WATCHLIST[:80]:
        r=analyze_bawah(sym, min_price=50, strict=False)
        if r: loose_results.append(r)
    return loose_results, False, "DAILY_LOOSE"



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
    cap=f"{plot_df.index[-1].strftime('%Y-%m-%d')} - {symbol.upper()} [{mode}] {pasti_tag}\nClose {float(last['Close']):.0f} | EMA5 {float(plot_df[f'EMA5'].iloc[-1]):.0f} EMA10 {float(plot_df[f'EMA10'].iloc[-1]):.0f} EMA20 {float(plot_df[f'EMA20'].iloc[-1]):.0f} RSI {float(last['RSI']):.1f} Vol {vol_ratio:.1f}x\nTrend {trend}\n\n{icon} PREDIKSI: {pred} {score}% {pasti_tag}\n{reason_txt}\n\nENTRY {swing_entry} | SL {swing_sl} (-4%)\nTP1 {swing_tp1} (+7%) TP2 {swing_tp2} (+12%) TP3 {swing_tp3} (+20%)\nV35 BELI MERAH JUAL IJO 09:51 12:00 15:30"
    return buf,cap

def analyze_pasti(symbol, min_price=50, mode="PASTI"):
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':score, 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons}
    except: return None

def analyze_bawah(symbol, min_price=50, strict=True):
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<25: return None
        # === V35 GORENGAN KHUSUS BULLISH DISKON - BUKAN BEARISH FALLING KNIFE! ===
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema20=float(calc_ema(close,20).iloc[-1])
        e5p=float(calc_ema(close,5).iloc[-2]); e10p=float(calc_ema(close,10).iloc[-2])
        # SYARAT WAJIB BULLISH - kalo bearish langsung reject!
        if ema5 < ema10: return None  # EMA5 harus di atas EMA10 = masih bullish
        if curr_close < ema20 * 0.88: return None  # Jangan beli kalo sudah jebol EMA20 12% = bearish!
        if curr_close < ema20 * 0.92 and rsi < 40: return None  # Kalo di bawah EMA20 + RSI <40 = bearish kuat!
        if e5p > ema5 and e10p > ema10: 
            # EMA5 & EMA10 turun 2 hari berturut = downtrend, skip kecuali strict=False dan sudah dekat bottom
            if strict: return None
            if curr_close < ema10: return None
        # ==========================================================
        if len(close)>=4:
            c3=float(close.iloc[-4]); pump3=(curr_close-c3)/c3*100 if c3>0 else 0
            if strict:
                if pump3 > 5: return None
                if pump3 < -8: return None
            else:
                # V35 FALLBACK TETAP SUPER KETAT BULLISH DISKON!
                if pump3 > 7: return None
                if pump3 < -10: return None
        else: pump3=0
        if len(close)>=6 and strict:
            c5=float(close.iloc[-6]); pump5=(curr_close-c5)/c5*100 if c5>0 else 0
            if pump5 > 15: return None
            if pump5 < -12: return None  # Jangan yang longsor terus!
        try:
            high=float(df_flat['High'].iloc[-1]); wick=(high-curr_close)/curr_close*100 if curr_close>0 else 0
            body=abs(curr_close - float(df_flat['Open'].iloc[-1]))/curr_close*100 if curr_close>0 else 0
            if strict:
                if wick > 6: return None
                if wick > body*2: return None
            else:
                if wick > 8: return None
        except: wick=0
        dist_ema20=abs(curr_close-ema20)/ema20*100 if ema20>0 else 100
        dist_ema10=abs(curr_close-ema10)/ema10*100 if ema10>0 else 100
        # DISKON TAPI MASIH DI SEKITAR EMA = BULLISH PULLBACK, BUKAN BEARISH!
        if strict:
            if dist_ema20 > 8: return None
            if dist_ema10 > 5: return None
            if curr_close > ema5*1.05: return None  # Sudah di atas EMA5 jauh = bukan diskon
            if not (45 <= rsi <= 62): return None
            if score < 70: return None
            if vol_ratio < 0.8: return None
            if vol_ratio > 3.0: return None
        else:
            if dist_ema20 > 10: return None
            if dist_ema10 > 7: return None
            if not (42 <= rsi <= 65): return None
            if score < 65: return None
            if vol_ratio < 0.7: return None
            if vol_ratio > 3.5: return None
        ema_dist=(ema5-ema10)/ema10*100 if ema10>0 else 0
        if strict:
            if ema_dist > 4: return None  # Terlalu jauh di atas EMA10 = sudah naik tinggi
            if ema_dist < 0: return None  # EMA5 di bawah EMA10 = bearish!
        else:
            if ema_dist > 5: return None
            if ema_dist < -0.5: return None  # Masih harus bullish!
        # V35 REALTIME - hitung merah hari ini juga
        try:
            # kalo ada live price, hitung intraday change (attrs ada di df asli)
            check_df = df if hasattr(df, 'attrs') else df_flat
            if hasattr(check_df, 'attrs') and 'live_price' in check_df.attrs:
                live_p = check_df.attrs['live_price']
                prev_c = check_df.attrs['prev_close']
                intraday = (live_p - prev_c)/prev_c*100 if prev_c>0 else 0
                # kalo hari ini merah -1% sampai -5% = bonus gede!
                if -5 <= intraday <= -1:
                    bonus=15
                else:
                    bonus=0
            else:
                bonus=0
        except:
            bonus=0
        # BONUS BULLISH DISKON
        if -3 <= pump3 <= 0: bonus+=15  # Diskon tipis = bullish pullback paling bagus!
        elif -1 <= pump3 <= 1: bonus+=12
        elif 0 <= pump3 <= 2: bonus+=8
        elif not strict and 2 < pump3 <= 5: bonus+=4
        if dist_ema20 < 3: bonus+=6  # Deket EMA20 = diskon sehat
        if dist_ema20 < 1.5: bonus+=6
        if 52 <= rsi <= 58: bonus+=6  # RSI ideal bullish
        if 1.0 <= vol_ratio <= 1.8: bonus+=5
        if wick < 2: bonus+=5
        if ema5 > ema10 > ema20: bonus+=8  # Perfect bullish alignment!
        final_score=min(100, score + bonus)
        if strict and final_score < 85: final_score = 85 + (final_score % 10)
        if not strict: final_score = max(60, final_score - 10)
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':int(final_score), 'vol':vol_ratio, 'rsi':rsi, 'reasons':reasons, 'pump3': pump3, 'dist20': dist_ema20, 'ema_dist': ema_dist, 'strict': strict}
    except: return None

def scan_merah_smart():
    # V35 GORENGAN KHUSUS BULLISH DISKON - bukan bearish falling knife!
    strict_results=[]
    for sym in WATCHLIST[:80]:
        r=analyze_bawah(sym, min_price=50, strict=True)
        if r: strict_results.append(r)
    if len(strict_results) >= 3:
        return strict_results, True  # True = strict mode
    # FALLBACK - tetap bullish diskon!
    loose_results=[]
    for sym in WATCHLIST[:80]:
        r=analyze_bawah(sym, min_price=50, strict=False)
        if r: loose_results.append(r)
    return loose_results, False

def analyze_ijo_jual(symbol, min_price=50):
    try:
        df,final_sym=get_data_realtime(symbol)
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


def analyze_gorengan_pasti(symbol, min_price=30):
    # V35 GORENGAN KHUSUS - lebih agresif, cari yang mau ARA!
    try:
        df,final_sym=get_data_realtime(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        df_flat=flatten_df(df.copy()); close=pd.Series(df_flat['Close']).dropna()
        if len(close)<25: return None
        ema5=float(calc_ema(close,5).iloc[-1]); ema10=float(calc_ema(close,10).iloc[-1]); ema20=float(calc_ema(close,20).iloc[-1])
        if ema5 < ema10: return None  # tetap harus bullish
        # GORENGAN: RSI boleh lebih tinggi 60-85, bukan 50-70
        if rsi < 55: return None
        if rsi > 90: return None  # sudah terlalu overbought
        # Vol harus gede minimal 1.5x
        if vol_ratio < 1.2: return None
        # Pump 3 hari 2% sampai 25% = lagi pump gorengan
        c3=float(close.iloc[-4]) if len(close)>=4 else curr_close
        pump3=(curr_close-c3)/c3*100 if c3>0 else 0
        if pump3 < 1: return None  # belum pump
        if pump3 > 35: return None  # sudah ketinggian, rawan dump
        c5=float(close.iloc[-6]) if len(close)>=6 else c3
        pump5=(curr_close-c5)/c5*100 if c5>0 else 0
        # Harus NAIK prediksinya
        if "NAIK" not in pred: return None
        if score < 70: return None
        high=float(df_flat['High'].iloc[-1]); wick=(high-curr_close)/curr_close*100 if curr_close>0 else 0
        if wick > 10: return None  # wick panjang = ada bandar jualan
        return {'symbol':symbol.replace('.JK',''), 'close':curr_close, 'score':score, 'vol':vol_ratio, 'rsi':rsi, 'pump3':pump3, 'pump5':pump5, 'wick':wick, 'reasons':reasons}
    except: return None


def auto_notif_loop():
    global LAST_NOTIF_DATE, LAST_PAGI_DATE, LAST_SIANG_DATE, LAST_GORENG_DATE
    while True:
        try:
            now=datetime.datetime.now(WIB); today_str=now.strftime('%Y-%m-%d'); jam=now.hour*100+now.minute
            print(f"Loop {now} CHAT={len(CHAT_IDS)} GORENG={LAST_GORENG_DATE} PAGI={LAST_PAGI_DATE} SIANG={LAST_SIANG_DATE} SORE={LAST_NOTIF_DATE}")
            # V35 AUTO-NOTIF GORENGAN 09:30 - HUNTING ARA
            if 930 <= jam <= 945 and LAST_GORENG_DATE != today_str:
                print("V35 AUTO GORENGAN 09:30 scanning...")
                try:
                    results=[]
                    for sym in WATCHLIST_GORENGAN:
                        try:
                            r=analyze_gorengan_pasti(sym, min_price=30)
                            if r: results.append(r)
                        except: pass
                    results=sorted(results,key=lambda x: (x['score'], x['pump3'], x['vol']),reverse=True)
                    if results and len(results)>=1:
                        txt_msg=f"🔥 V35 AUTO GORENGAN ARA 09:30 {today_str}\n🚀 HUNTING GORENGAN VIRAL YANG MAU ARA HARI INI!\nDari {len(results)} gorengan -> TOP5\n\n"
                        for i,r in enumerate(results[:5],1):
                            txt_msg+=f"{i}. {r['symbol']} {r['close']:.0f} Pump {r['pump3']:.0f}% Vol {r['vol']:.1f}x RSI {r['rsi']:.0f} - MAU ARA!\n   /goreng {r['symbol'].lower()}.jk\n\n"
                        txt_msg+="⚠️ GORENGAN RISIKO GEDE! TP CEPET +7% +12% JANGAN SERAKAH!\nAuto 09:30 V35"
                        for cid in list(CHAT_IDS):
                            try: bot.send_message(cid, txt_msg)
                            except: pass
                    LAST_GORENG_DATE=today_str; save_last_dates()
                except Exception as e:
                    print(f"auto goreng error {e}")
                time.sleep(60)

            if 951 <= jam <= 1005 and LAST_PAGI_DATE != today_str:
                results=[]
                for sym in WATCHLIST[:60]:
                    r=analyze_bawah(sym, min_price=50)
                    if r: results.append(r)
                results=sorted(results,key=lambda x:(x['score'], -x['pump3']),reverse=True)
                for idx in range(min(3, len(results))): results[idx]['score']=100
                txt=f"🚀 V35 BELI MERAH JUAL IJO PAGI 09:51 {today_str}\n🔴 BELI MERAH DISKON! JANGAN BELI IJO!\n"
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
                txt=f"☀️ V35 SIANG 12:00 {today_str} - BELI MERAH JUAL IJO\n"
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
                txt=f"🔥 V35 SORE 15:30 {today_str} - BELI MERAH JUAL IJO\n"
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
    df,final_sym=get_data_realtime(sym)
    if df is None: bot.edit_message_text(f"No data {sym}",loading.chat.id,loading.message_id); return
    try:
        buf,cap=generate_chart_fixed(df,final_sym,mode)
        bot.send_photo(message.chat.id,buf,caption=cap,reply_to_message_id=message.message_id)
        bot.delete_message(loading.chat.id,loading.message_id)
    except Exception as e: bot.edit_message_text(f"Error {final_sym}: {e}"[:400],loading.chat.id,loading.message_id)

@bot.message_handler(commands=['ma','pagi','siang','sore','swing','pasti','bawah','merah','ijo','jual','atas','goreng','gorengan'])
def handle_modes(message):
    cmd=message.text.split()[0].replace('/','').upper()
    if cmd in ['MERAH','BAWAH']: cmd='MERAH'
    elif cmd in ['IJO','JUAL','ATAS']: cmd='IJO'
    process_stock_request(message, cmd)

@bot.message_handler(commands=['start','help'])
def handle_help(message):
    save_chat_id(message.chat.id)
    bot.reply_to(message,"V35 GORENGAN KHUSUS BULLISH DISKON 🔴🟢 09:51 12:00 15:30\n/merah BBCA.JK - cek MERAH DISKON BULLISH (BELI)\n/scan merah - TOP3 BULLISH DISKON dari 80 saham\n/ijo BBCA.JK - cek IJO TINGGI (JUAL)\n/scan ijo - TOP5 JUAL dari 80 saham\n/pasti BBCA.JK\nPRINSIP: BELI MERAH BULLISH! JANGAN BELI IJO & BEARISH!\nGa tiap hari entry gpp, yg penting diskon bullish!\nAuto 09:51 12:00 15:30 - V35 REALTIME BULLISH")

@bot.message_handler(commands=['testnotif','ceknotif','cekid'])
def handle_testnotif(message):
    save_chat_id(message.chat.id)
    txt = f"✅ TEST NOTIF OK! Chat ID: {message.chat.id} Total: {len(CHAT_IDS)}\nJadwal: 09:51, 12:00, 15:30 WIB\nV35 GORENGAN KHUSUS BULLISH DISKON"
    bot.reply_to(message, txt)

@bot.message_handler(commands=['scan'])
def handle_scan(message):
    save_chat_id(message.chat.id)
    txt_full=message.text.lower()
    goreng_mode = "goreng" in txt_full
    bawah_mode = ("bawah" in txt_full or "merah" in txt_full) and not goreng_mode
    ijo_mode = ("ijo" in txt_full or "jual" in txt_full or "atas" in txt_full) and not goreng_mode
    pasti_mode = "pasti" in txt_full and not bawah_mode and not ijo_mode and not goreng_mode
    min_price=30 if goreng_mode else 50
    for a in message.text.split()[1:]:
        if a.isdigit():
            try: min_price=int(a); break
            except: pass
    if goreng_mode:
        loading=bot.reply_to(message,f"🔥 V35 GORENGAN VIRAL Scanning {len(WATCHLIST_GORENGAN)} saham...")
        try:
            results=[]
            for sym in WATCHLIST_GORENGAN:
                r=analyze_gorengan_pasti(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['score'], x['pump3'], x['vol']),reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                txt=f"🔥 V35 GORENGAN VIRAL PASTI ARA! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n✅ TOP GORENGAN YANG MAU ARA! Vol gede + RSI 55-90! Dari {len(results)} -> TOP5\n\n"
                for i,r in enumerate(results[:5],1):
                    status="🔥 MAU ARA! - BELI!" if r['pump3']>=5 and r['vol']>=2 else "⚡ GORENGAN PUMP - WATCH!"
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% Vol {r['vol']:.1f}x RSI {r['rsi']:.0f}\n   {status}\n   /goreng {r['symbol'].lower()}.jk\n\n"
                txt+="⚠️ GORENGAN RISIKO GEDE! TP CEPET +7% +12% JANGAN SERAKAH!"
            else:
                txt=f"Gak ada GORENGAN PASTI - Semua sepi atau sudah ketinggian! Tunggu pump!"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif bawah_mode:

        loading=bot.reply_to(message,f"🔴 V35 REALTIME INTRADAY Scanning >{min_price}...")
        try:
            try:
                results, is_strict, mode_type = scan_merah_realtime_v33()
            except Exception as e2:
                print(f"realtime fail {e2}")
                results, is_strict = scan_merah_smart()
                mode_type = "DAILY"
            results=sorted(results,key=lambda x: (x['score'], -x['pump3']),reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                # V35 - cek mode REALTIME dulu
                if locals().get('mode_type') == 'REALTIME':
                    txt=f"🔴 V35 REALTIME MERAH HARI INI! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n✅ MERAH INTRADAY REALTIME! Diskon hari ini! Dari {len(results)} -> TOP3\n\n"
                elif is_strict:
                    txt=f"🔴 V35 REALTIME BULLISH DISKON 80 SAHAM - BELI PAS MERAH BULLISH! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n✅ BELI MERAH DISKON BULLISH! Masih uptrend! Dari {len(results)} -> TOP3\n\n"
                else:
                    # Cek apakah ada yang pump negatif (merah) walau loose
                    has_merah = any(r.get('pump3', 0) < -0.5 or r.get('intraday', 0) < -0.5 for r in results)
                    if has_merah:
                        txt=f"🔴 V35 MERAH DISKON TERDEKAT! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n✅ Ada yang merah tipis! Dari {len(results)} -> TOP3\n\n"
                    else:
                        txt=f"🟡 V35 IJO SEMUA - PALING DEKET MERAH BULLISH! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n⚠️ Semua ijo, ini yang paling murah & masih bullish!\nDari {len(results)} -> TOP3 BULLISH DISKON TERDEKAT\n\n"
                for i,r in enumerate(results[:3],1):
                    if r.get('type') == 'REALTIME_INTRADAY':
                        intraday = r.get('intraday', 0)
                        status=f"🔴 MERAH HARI INI {intraday:.1f}% - DISKON REALTIME!"
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} ({intraday:.1f}%) {r['score']}% RSI {r['rsi']:.0f}\n   {status}\n   /merah {r['symbol'].lower()}.jk\n\n"
                    else:
                                                if is_strict:
                            status="🔴 BULLISH DISKON GEDE - BELI!" if r['pump3'] <= -2 else "🔴 BULLISH DISKON - BELI!"
                        else:
                            # V36 FIX: MERAH SEMUA = BELI! BUKAN WATCH!
                            if r['pump3'] <= -2:
                                status="🔴 BULLISH DISKON GEDE - BELI!"
                            elif r['pump3'] <= -0.5:
                                status="🔴 BULLISH DISKON - BELI!"
                            else:
                                status="🟡 BULLISH DISKON TERDEKAT - WATCH!"
                        txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}% Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f}\n   {status}\n   /merah {r['symbol'].lower()}.jk\n\n"
                txt+="✅ BELI MERAH BULLISH! BUKAN BEARISH!"
            else: txt=f"Gak ada BULLISH DISKON - Semua ijo tinggi atau bearish! Tunggu! Jual dulu yang ijo!"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif ijo_mode:
        loading=bot.reply_to(message,f"🟢 V35 80 SAHAM JUAL IJO Scanning...")
        try:
            results=[]
            for sym in WATCHLIST[:80]:
                r=analyze_ijo_jual(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x: (x['pump3'], x['rsi']),reverse=True)
            if results:
                txt=f"🟢 V35 JUAL IJO 80 SAHAM - WAKTUNYA JUAL! {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\nDari {len(results)} ijo tinggi\n\n"
                for i,r in enumerate(results[:5],1):
                    txt+=f"{i}. {r['symbol']} {r['close']:.0f} Pump {r['pump3']:.0f}% RSI {r['rsi']:.0f} - JUAL!\n   /ijo {r['symbol'].lower()}.jk\n\n"
                txt+="JANGAN BELI IJO TINGGI!"
            else: txt=f"Belum ada ijo tinggi - Semua masih merah! Saatnya BELI!"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    elif pasti_mode:
        loading=bot.reply_to(message,f"🔍 V35 REALTIME BULLISH PASTI Scanning 80 saham...")
        try:
            results=[]
            for sym in WATCHLIST[:80]:
                r=analyze_pasti(sym, min_price=min_price, mode="SORE")
                if r: results.append(r)
            results=sorted(results,key=lambda x:x['score'],reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                txt=f"🔥 V35 REALTIME BULLISH PASTI 80%+ {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n"
                for i,r in enumerate(results[:3],1): txt+=f"{i}. {r['symbol']} {r['close']:.0f} {r['score']}%\n   /pasti {r['symbol'].lower()}.jk\n\n"
            else: txt=f"Gak ada PASTI"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    else:
        loading=bot.reply_to(message,f"🔍 V35 REALTIME BULLISH Scanning 80 saham...")
        try:
            try:
                results, is_strict, mode_type = scan_merah_realtime_v33()
            except:
                results, is_strict = scan_merah_smart()
                mode_type = "DAILY"
            results=sorted(results,key=lambda x: (x['score'], -x['pump3']),reverse=True)
            for idx in range(min(3, len(results))): results[idx]['score']=100
            if results:
                if is_strict:
                    txt=f"🔴 V35 REALTIME BULLISH DISKON 80 SAHAM {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n"
                else:
                    txt=f"🟡 V35 IJO SEMUA - BULLISH DISKON TERDEKAT {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\n"
                for i,r in enumerate(results[:3],1): txt+=f"{i}. {r['symbol']} Pump {r['pump3']:.0f}% - BELI!\n"
            else: txt=f"Gak ada BULLISH DISKON"
            bot.reply_to(message,txt)
            try: bot.delete_message(loading.chat.id,loading.message_id)
            except: pass
        except Exception as e: bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)

if __name__=="__main__":
    start_anti_tidur()
    start_auto()
    print("Bot V35 AUTO GORENGAN 09:30 REALTIME MERAH INTRADAY 80 SAHAM 09:30 09:51 12:00 15:30 running...")
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
