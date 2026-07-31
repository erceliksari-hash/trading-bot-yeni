import time
import pandas as pd
import yfinance as yf
import ccxt
import schedule
from datetime import datetime

from config import VARLIK_LISTESI
from analysis_engine import AnalysisEngine
from trading_engine import TradingEngine
from telegram_notifier import send_telegram_msg

trading_system = TradingEngine()
binance = ccxt.binance({'enableRateLimit': True})

def veri_getir(sembol, kitle="KRIPTO"):
    """Binance ve YFinance üzerinden veri çekme köprüsü."""
    try:
        if kitle == "KRIPTO":
            ohlcv = binance.fetch_ohlcv(sembol, timeframe='15m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        else:
            ticker = yf.Ticker(sembol)
            df = ticker.history(period="5d", interval="15m")
            df = df.reset_index()
            df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
            return df
    except Exception as e:
        print(f"Veri çekme hatası [{sembol}]: {e}")
        return None

def analiz_dongusu_15dk():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 15 Dakikalık Analiz Taraması Başladı...")
    
    for kategori, varliklar in VARLIK_LISTESI.items():
        for sembol in varliklar:
            df = veri_getir(sembol, kategori)
            if df is None or len(df) < 50:
                continue
                
            analiz = AnalysisEngine.sahte_sinyal_ve_trend_analizi(df)
            destek, direnc = AnalysisEngine.destek_direnc_hesapla(df)
            fib = AnalysisEngine.fibonacci_seviyeleri(df)
            
            fiyat = analiz['fiyat']
            
            # --- OTOMATİK LONG / SHORT TİCARET KARARI ---
            if analiz['long_sinyal']:
                tp = fiyat * 1.02  # %2 TP
                sl = destek if destek < fiyat else fiyat * 0.985 # Stop Loss
                islem = trading_system.pozisyon_ac(sembol, "LONG", fiyat, tp, sl, "15m RSI/MACD Boğa Kırılımı")
                if islem:
                    send_telegram_msg(f"🟢 *LONG İŞLEM AÇILDI*\n\n📌 **Varlık:** {sembol}\n💵 **Giriş Fiyatı:** `${fiyat:.2f}`\n🎯 **TP:** `${tp:.2f}` | 🛑 **SL:** `${sl:.2f}`")
                    
            elif analiz['short_sinyal']:
                tp = fiyat * 0.98  # %2 TP
                sl = direnc if direnc > fiyat else fiyat * 1.015 # Stop Loss
                islem = trading_system.pozisyon_ac(sembol, "SHORT", fiyat, tp, sl, "15m RSI/MACD Ayı Kırılımı")
                if islem:
                    send_telegram_msg(f"🔴 *SHORT İŞLEM AÇILDI*\n\n📌 **Varlık:** {sembol}\n💵 **Giriş Fiyatı:** `${fiyat:.2f}`\n🎯 **TP:** `${tp:.2f}` | 🛑 **SL:** `${sl:.2f}`")

            # --- AÇIK POZİSYON KONTROLÜ (LONG VE SHORT TP/SL) ---
            if sembol in trading_system.acik_pozisyonlar:
                poz = trading_system.acik_pozisyonlar[sembol]
                
                # LONG Pozisyon Kontrolü
                if poz['yon'] == "LONG":
                    if fiyat >= poz['tp_fiyat']:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "TAKE_PROFIT")
                        send_telegram_msg(f"✅ *LONG KARLA KAPANDI!*\n{sembol} | Kar: `${k['kar_zarar']:.2f}`\nYeni Kasa: `${trading_system.kasa:.2f}`")
                    elif fiyat <= poz['sl_fiyat']:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "STOP_LOSS")
                        send_telegram_msg(f"❌ *LONG STOP OLDU!*\n{sembol} | Zarar: `${k['kar_zarar']:.2f}`\nYeni Kasa: `${trading_system.kasa:.2f}`")
                
                # SHORT Pozisyon Kontrolü (Eklendi)
                elif poz['yon'] == "SHORT":
                    if fiyat <= poz['tp_fiyat']:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "TAKE_PROFIT")
                        send_telegram_msg(f"✅ *SHORT KARLA KAPANDI!*\n{sembol} | Kar: `${k['kar_zarar']:.2f}`\nYeni Kasa: `${trading_system.kasa:.2f}`")
                    elif fiyat >= poz['sl_fiyat']:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "STOP_LOSS")
                        send_telegram_msg(f"❌ *SHORT STOP OLDU!*\n{sembol} | Zarar: `${k['kar_zarar']:.2f}`\nYeni Kasa: `${trading_system.kasa:.2f}`")

def saatlik_telegram_raporu():
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"📊 *SAATLİK PİYASA VE PORTFÖY RAPORU* ({zaman})\n"
    msg += f"-----------------------------------\n"
    msg += f"💼 *Sanal Kasa Bakiyesi:* `${trading_system.kasa:.2f}`\n"
    msg += f"🔓 *Açık Pozisyon Sayısı:* `{len(trading_system.acik_pozisyonlar)}`\n\n"
    
    # Kripto BTC Örnek Analiz
    df_btc = veri_getir("BTC/USDT", "KRIPTO")
    if df_btc is not None:
        analiz = AnalysisEngine.sahte_sinyal_ve_trend_analizi(df_btc)
        destek, direnc = AnalysisEngine.destek_direnc_hesapla(df_btc)
        msg += f"🟡 *BTC/USDT Durumu:*\n"
        msg += f"• Fiyat: `${analiz['fiyat']:.2f}` | Trend: `{analiz['trend']}`\n"
        msg += f"• Destek: `${destek:.2f}` | Direnç: `${direnc:.2f}`\n"
        msg += f"• RSI: `{analiz['rsi']:.1f}`\n"
    
    send_telegram_msg(msg)

# --- ZAMANLAYICI (SCHEDULE) ---
schedule.every(15).minutes.do(analiz_dongusu_15dk)
schedule.every(1).hours.do(saatlik_telegram_raporu)

if __name__ == "__main__":
    send_telegram_msg("🚀 *Otonom Analiz & Ticaret Botu Başlatıldı!*")
    analiz_dongusu_15dk() # İlk çalıştırma
    
    while True:
        schedule.run_pending()
        time.sleep(1)