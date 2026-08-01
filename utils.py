# utils.py - Ortak Yardımcı Fonksiyonlar ve Veri Yönetimi
import json
import logging
import pandas as pd
import yfinance as yf
import ccxt

binance = ccxt.binance({'enableRateLimit': True})

def varlik_listesini_oku():
    try:
        with open("varlik_listesi.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        from config import VARLIK_LISTESI
        varlik_listesini_kaydet(VARLIK_LISTESI)
        return VARLIK_LISTESI

def varlik_listesini_kaydet(data):
    try:
        with open("varlik_listesi.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"JSON Kaydetme Hatası: {e}")

def veri_getir(sembol, kitle="KRIPTO", timeframe='1h', limit=150):
    try:
        if kitle.upper() == "KRIPTO":
            ohlcv = binance.fetch_ohlcv(sembol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        else:
            period = "60d" if timeframe in ['1h', '4h'] else "1y"
            yf_interval = "1h" if timeframe == '1h' else "1d"
            
            ticker = yf.Ticker(sembol)
            df = ticker.history(period=period, interval=yf_interval)
            
            if df is None or df.empty:
                return None
                
            df = df.reset_index()
            df.columns = [str(c).lower() for c in df.columns]
            
            rename_dict = {}
            for col in df.columns:
                if col in ['date', 'datetime', 'index']:
                    rename_dict[col] = 'timestamp'
            
            df.rename(columns=rename_dict, inplace=True)
            
            if 'timestamp' in df.columns and pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                if df['timestamp'].dt.tz is not None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                    
            return df
    except Exception as e:
        print(f"⚠️ Veri çekme hatası [{sembol} - {timeframe}]: {e}")
        return None

def ust_trend_tespit_et(sembol, kitle):
    from analysis_engine import AnalysisEngine
    df_4h = veri_getir(sembol, kitle, timeframe="4h", limit=100)
    if df_4h is None or len(df_4h) < 30:
        return "NETRAL"
        
    engine_4h = AnalysisEngine(df_4h)
    df_islenmis = engine_4h.indikatorleri_hesapla()
    
    if df_islenmis is None or len(df_islenmis) == 0:
        return "NETRAL"

    son_bar = df_islenmis.iloc[-1]
    ema50 = son_bar.get('EMA_50', 0)
    ema200 = son_bar.get('EMA_200', 0)
    
    if ema50 > ema200:
        return "BOGA"
    elif ema50 < ema200:
        return "AYI"
    return "NETRAL"