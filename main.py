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
    return f"Bot V17 ANTI-PUCUK 100% - Uptime {uptime//3600}h {(uptime%3600)//60}m {datetime.datetime.now(WIB).strftime('%H:%M:%S WIB')}"
@app.route('/health')
def health(): return "OK V17 ANTI-PUCUK",200
@app.route('/ping')
def ping(): return "pong V17 ANTI-PUCUK",200
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
        # Trend naik 2 hari berturut?
        naik_2hari = curr_close > prev_close and prev_close > float(close.iloc[-3])
        
        # --- V17 ANTI-PUCUK FILTER ---
        close_3d_ago = float(close.iloc[-4]) if len(close)>=4 else curr_close
        close_5d_ago = float(close.iloc[-6]) if len(close)>=6 else curr_close
        pump_3d = (curr_close - close_3d_ago)/close_3d_ago*100 if close_3d_ago>0 else 0
        pump_5d = (curr_close - close_5d_ago)/close_5d_ago*100 if close_5d_ago>0 else 0
        # wick panjang = (high - close) / close
        try:
            last_high = float(df['High'].iloc[-1])
            last_low = float(df['Low'].iloc[-1])
            wick_up = (last_high - curr_close)/curr_close*100 if curr_close>0 else 0
        except:
            last_high = curr_close
            last_low = curr_close
            wick_up = 0
        
        score=50; reasons=[]
        # Filter pucuk dulu
        if pump_3d > 50:
            score-=35
            reasons.append(f"⛔ PUCUK! Naik {pump_3d:.0f}% 3 hari -35%")
        elif pump_3d > 35:
            score-=20
            reasons.append(f"⚠️ Udah naik tinggi {pump_3d:.0f}% 3hr -20%")
        if pump_5d > 70:
            score-=20
            reasons.append(f"⛔ Pompom {pump_5d:.0f}% 5 hari -20%")
        if wick_up > 15:
            score-=15
            reasons.append(f"⛔ Wick panjang {wick_up:.0f}% distribution -15%")
        
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
    cap=f"{plot_df.index[-1].strftime('%Y-%m-%d')} - {symbol.upper()} [{mode}] {pasti_tag}\nClose {float(last['Close']):.0f} | EMA5 {float(plot_df[f'EMA{ema_fast}'].iloc[-1]):.0f} EMA10 {float(plot_df[f'EMA{ema_mid}'].iloc[-1]):.0f} EMA20 {float(plot_df[f'EMA{ema_slow}'].iloc[-1]):.0f} RSI {float(last['RSI']):.1f} Vol {vol_ratio:.1f}x\nTrend {trend}\n\n{icon} PREDIKSI: {pred} {score}% {pasti_tag}\n{reason_txt}\n\nENTRY {swing_entry} | SL {swing_sl} (-4%)\nTP1 {swing_tp1} (+7%) TP2 {swing_tp2} (+12%) TP3 {swing_tp3} (+20%)\nV17 ANTI-PUCUK 100% - Hanya 80%+ yang keluar!"
    return buf,cap

def analyze_pasti(symbol, min_price=50):
    try:
        df,final_sym=get_data_fixed(symbol)
        if df is None: return None
        pred,score,reasons,vol_ratio,rsi,curr_close=predict_next(df)
        if curr_close < min_price: return None
        if "NAIK" not in pred: return None
        
        # V17 ANTI-PUCUK - HARD BLOCK
        df_flat=flatten_df(df.copy())
        close=pd.Series(df_flat['Close']).dropna()
        # pump check
        if len(close)>=4:
            c3 = float(close.iloc[-4])
            pump3 = (curr_close-c3)/c3*100 if c3>0 else 0
            if pump3 > 30:  # MEDS 71->93 = 30%+ -> BLOCK
                return None
        # wick check
        try:
            high = float(df_flat['High'].iloc[-1])
            wick = (high-curr_close)/curr_close*100 if curr_close>0 else 0
            if wick > 12:  # MEDS wick 18% -> BLOCK
                return None
        except:
            pass
        
        # FILTER PASTI - SUPER KETAT
        # 1. Score minimal 80%
        if score < 80: return None
        # 2. Volume minimal 1.5x rame (gak mau sepi kayak IOTF 0.2x)
        if vol_ratio < 1.5: return None
        # 3. RSI ideal 50-68 (gak overbought)
        if not (50 <= rsi <= 68): return None
        # 4. Harus bullish atau baru cross up
        ema5=calc_ema(close,5).iloc[-1]; ema10=calc_ema(close,10).iloc[-1]; ema20=calc_ema(close,20).iloc[-1]
        if not (ema5>ema10): return None  # minimal EMA5 di atas EMA10
        # 5. Close di atas EMA5 (kuat)
        if curr_close < ema5: return None

        return {'symbol':final_sym.replace('.JK',''), 'close':curr_close, 'rsi':rsi, 'pred':pred, 'score':score, 'vol':vol_ratio, 'reasons':reasons[:2]}
    except: return None

def auto_notif_loop():
    global LAST_NOTIF_DATE, LAST_PAGI_DATE
    while True:
        try:
            now=datetime.datetime.now(WIB)
            today_str=now.strftime("%Y-%m-%d")
            if now.weekday() >= 5:
                time.sleep(3600)
                continue
            if now.hour==9 and now.minute in [15,16] and LAST_PAGI_DATE!=today_str and len(CHAT_IDS)>0:
                results=[r for r in [analyze_pasti(s) for s in WATCHLIST[:60]] if r]
                results=sorted(results,key=lambda x:x['score'],reverse=True)[:5]
                if results:
                    txt=f"🔥 AUTO PASTI 09:15 - {today_str}\nHanya yang 80%+ & Vol rame!\n\n"
                    for r in results:
                        txt+=f"✅ {r['symbol']} {r['close']:.0f} {r['score']}% Vol {r['vol']:.1f}x RSI {r['rsi']:.0f}\n  /pagi {r['symbol'].lower()}.jk\n"
                    txt+="\nYang PASTI aja!"
                else:
                    txt=f"🔔 AUTO PASTI 09:15 - {today_str}\nHari ini gak ada yang PASTI 80%+, skip dulu, jaga modal!\nCek /scan buat 70%+"
                for cid in list(CHAT_IDS):
                    try: bot.send_message(cid, txt)
                    except: pass
                LAST_PAGI_DATE=today_str
            if now.hour==15 and now.minute in [30,31] and LAST_NOTIF_DATE!=today_str and len(CHAT_IDS)>0:
                # sore tetap kasih yang pasti juga
                results=[r for r in [analyze_pasti(s) for s in WATCHLIST[:60]] if r]
                results=sorted(results,key=lambda x:x['score'],reverse=True)[:5]
                if results:
                    txt=f"🚀 GAS SORE! AUTO PASTI SORE 15:30 - {today_str}\nAda {len(results)} buat besok PAGI:\n\n"
                    for r in results:
                        sl = int(r['close']*0.96)
                        tp = int(r['close']*1.07)
                        txt+=f"✅ {r['symbol']} {r['close']:.0f} | {r['score']}% | Vol {r['vol']:.1f}x\n  ENTRY {r['close']:.0f} SL {sl} TP {tp}\n  /sore {r['symbol'].lower()}.jk\n\n"
                    txt+="KLO ADA MASUK AJA! Hold buat PAGI!"
                else:
                    txt=f"🔔 AUTO SORE 15:30 - {today_str}\nGak ada yang PASTI hari ini, istirahat!"
                for cid in list(CHAT_IDS):
                    try: bot.send_message(cid, txt)
                    except: pass
                LAST_NOTIF_DATE=today_str
                time.sleep(120)
            time.sleep(30)
        except Exception as e:
            print(e); time.sleep(60)

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
    loading=bot.reply_to(message,f"⏳ {mode} {sym} cek PASTI...")
    df,final_sym=get_data_fixed(sym)
    if df is None:
        bot.edit_message_text(f"No data {sym}",loading.chat.id,loading.message_id); return
    try:
        buf,cap=generate_chart_fixed(df,final_sym,mode)
        bot.send_photo(message.chat.id,buf,caption=cap,reply_to_message_id=message.message_id)
        bot.delete_message(loading.chat.id,loading.message_id)
    except Exception as e:
        bot.edit_message_text(f"Error {final_sym}: {e}"[:400],loading.chat.id,loading.message_id)

@bot.message_handler(commands=['ma','pagi','sore','swing','pasti'])
def handle_modes(message):
    cmd=message.text.split()[0].replace('/','').upper()
    process_stock_request(message, cmd)

@bot.message_handler(commands=['start','help'])
def handle_help(message):
    save_chat_id(message.chat.id)
    bot.reply_to(message,"V17 ANTI-PUCUK MODE 🔥\nHanya yang 80%+ & Vol rame!\n\n/pasti BRMS.JK - cek apakah PASTI 80%+\n/pagi BRMS.JK - mode pagi\n/sore BRMS.JK - mode sore\n/scan pasti - hanya 80%+ pasti\n/scan - semua 70%+\n\nAuto 09:15 & 15:30 hanya ngasih yang PASTI!")

@bot.message_handler(commands=['scan'])
def handle_scan(message):
    save_chat_id(message.chat.id)
    txt_full=message.text.lower()
    pasti_mode = "pasti" in txt_full
    min_price=50
    for a in message.text.split()[1:]:
        if a.isdigit():
            try: min_price=int(a); break
            except: pass

    if pasti_mode:
        loading=bot.reply_to(message,f"🔍 V17 ANTI-PUCUK Scanning 60 saham >{min_price} hanya 80%+ Vol>1.5x...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                r=analyze_pasti(sym, min_price=min_price)
                if r: results.append(r)
            results=sorted(results,key=lambda x:x['score'],reverse=True)
            if not results:
                txt=f"🔍 V17 ANTI-PUCUK >{min_price} - {datetime.datetime.now(WIB).strftime('%d %b %H:%M')}\nGak ada yang PASTI 80%+ hari ini.\n\nArtinya market belum ada yang bener-bener kuat + volume rame.\nMending jaga modal, cek /scan buat yang 70%+."
            else:
                txt=f"🔥 V17 ANTI-PUCUK 80%+ - {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\nFilter >{min_price} | Vol>1.5x | RSI 50-68 | Total {len(results)}\n\n✅ YANG PASTI AJA ({len(results)}):\n"
                for i,r in enumerate(results[:10],1):
                    txt+=f"{i}. {r['symbol']} - {r['close']:.0f} | {r['score']}% | RSI {r['rsi']:.0f} Vol {r['vol']:.1f}x\n   {r['reasons'][0] if r['reasons'] else ''}\n   /pasti {r['symbol'].lower()}.jk\n\n"
                txt+="\nIni yang paling aman buat PAGI-SORE & SWING!"
            bot.reply_to(message,txt)
            bot.delete_message(loading.chat.id,loading.message_id)
        except Exception as e:
            bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)
    else:
        # scan longgar 70%+ V17 ANTI-PUCUK juga
        loading=bot.reply_to(message,f"🔍 V17 ANTI-PUCUK Scanning 60 saham >{min_price} 70%+...")
        try:
            results=[]
            for sym in WATCHLIST[:60]:
                df,_=get_data_fixed(sym)
                if df is None: continue
                # ANTI-PUCUK filter juga buat /scan
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
                except:
                    pass
                pred,score,reasons,vol,rsi,close=predict_next(df)
                if close<min_price: continue
                if score>=70 and "NAIK" in pred and vol>=1.2 and 50<=rsi<=70:
                    results.append({'symbol':sym.replace('.JK',''), 'close':close, 'score':score, 'vol':vol, 'rsi':rsi, 'reasons':reasons})
            results=sorted(results,key=lambda x:x['score'],reverse=True)
            if not results:
                txt=f"🔍 V17 ANTI-PUCUK >{min_price} {datetime.datetime.now(WIB).strftime('%d %b %H:%M')}\nGak ada 70%+ ANTI-PUCUK hari ini.\nMarket banyak pucuk/distribution."
            else:
                txt=f"🔥 V17 ANTI-PUCUK SCAN 70%+ - {datetime.datetime.now(WIB).strftime('%d %b %H:%M WIB')}\nTotal {len(results)} (udah filter pucuk)\n\n"
                for i,r in enumerate(results[:15],1):
                    tag="🔥 PASTI" if r['score']>=80 else "⚡"
                    txt+=f"{i}. {tag} {r['symbol']} {r['close']:.0f} {r['score']}% Vol {r['vol']:.1f}x\n   {r['reasons'][0] if r['reasons'] else ''}\n   /pagi {r['symbol'].lower()}.jk\n\n"
                txt+="Ketik /scan pasti buat yang 80%+ aja!"
            bot.reply_to(message,txt)
            bot.delete_message(loading.chat.id,loading.message_id)
        except Exception as e:
            bot.edit_message_text(f"Error: {e}"[:400],loading.chat.id,loading.message_id)

if __name__=="__main__":
    start_anti_tidur()
    start_auto()
    print("Bot V17 ANTI-PUCUK 100% PASTI running...")
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
