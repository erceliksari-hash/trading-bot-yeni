# main.py - Otonom Ticaret ve Bot Orkestratörü
import time
import io
import threading
import pandas as pd
import schedule
import matplotlib.pyplot as plt
from datetime import datetime

from config import GIRIS_PERIYODU, TREND_PERIYODU, TARAMA_PERIYODU_DAKIKA, BASLANGIC_KASASI
from analysis_engine import AnalysisEngine
from trading_engine import TradingEngine
from sentiment_engine import SentimentEngine
from telegram_notifier import send_telegram_msg, send_telegram_photo
from telegram_bot import bot_uygulamasini_baslat
from utils import varlik_listesini_oku, veri_getir, ust_trend_tespit_et

trading_system = TradingEngine()
sentiment_system = SentimentEngine()

def grafik_olustur_ve_hazirla(df, sembol, sinyal_turu):
    try:
        df_plot = df.tail(45).copy()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        fig.patch.set_facecolor('#1a1a1a')
        
        for ax in [ax1, ax2]:
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='white', labelsize=8)
            for spine in ax.spines.values():
                spine.set_color('#333333')

        ax1.plot(df_plot['timestamp'], df_plot['close'], label='Fiyat', color='white', linewidth=1.5)
        if 'EMA_20' in df_plot.columns:
            ax1.plot(df_plot['timestamp'], df_plot['EMA_20'], label='EMA 20', color='#ff9900', linestyle='--')
        if 'EMA_50' in df_plot.columns:
            ax1.plot(df_plot['timestamp'], df_plot['EMA_50'], label='EMA 50', color='#00ccff', linestyle='--')

        ax1.set_title(f"{sembol} - {sinyal_turu} Sinyal Görünümü", color='white', fontsize=11, fontweight='bold')
        ax1.legend(loc='upper left', facecolor='#2b2b2b', edgecolor='none', labelcolor='white', fontsize=8)
        ax1.grid(True, color='#262626', linestyle=':', alpha=0.6)

        if 'RSI' in df_plot.columns:
            ax2.plot(df_plot['timestamp'], df_plot['RSI'], color='#e056fd', label='RSI (14)')
            ax2.axhline(70, color='#ff5252', linestyle='--', alpha=0.6)
            ax2.axhline(30, color='#1dd1a1', linestyle='--', alpha=0.6)
            ax2.set_ylim(0, 100)
            ax2.legend(loc='upper left', facecolor='#2b2b2b', edgecolor='none', labelcolor='white', fontsize=8)
            ax2.grid(True, color='#262626', linestyle=':', alpha=0.6)

        plt.xticks(rotation=15)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"⚠️ Grafik çizim hatası: {e}")
        return None

def saatlik_kasa_raporu():
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M")
    kasa = trading_system.kasa
    toplam_kar = kasa - BASLANGIC_KASASI
    yuzde = (toplam_kar / BASLANGIC_KASASI) * 100
    durum = "📈" if toplam_kar >= 0 else "📉"
    
    msg = (
        f"⏰ *SAATLİK KASA VE PORTFÖY RAPORU* ({zaman})\n"
        f"-----------------------------------\n"
        f"💰 *Mevcut Kasa Bakiyesi:* `${kasa:,.2f}`\n"
        f"{durum} *Toplam Kâr/Zarar:* `${toplam_kar:+,.2f}` (%{yuzde:+.2f})\n"
        f"🔓 *Açık Pozisyon:* `{len(trading_system.acik_pozisyonlar)}` adet\n"
        f"📜 *Geçmiş İşlemler:* `{len(trading_system.gecmis_islemler)}` adet"
    )
    send_telegram_msg(msg)

def analiz_dongusu():
    zaman_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n[{zaman_str}] Taramalar Başlatıldı...")
    
    varlik_listesi = varlik_listesini_oku()
    
    for kategori, varliklar in varlik_listesi.items():
        for sembol in varliklar:
            ust_trend = ust_trend_tespit_et(sembol, kategori)
            df_1h = veri_getir(sembol, kategori, timeframe=GIRIS_PERIYODU, limit=150)
            
            if df_1h is None or len(df_1h) < 30:
                continue
                
            engine = AnalysisEngine(df_1h)
            engine.indikatorleri_hesapla()
            
            if not engine.sahte_sinyal_kontrolu():
                continue

            sinyal, fiyat, sl, tp, sebep = engine.sinyal_uret(ust_trend_yonu=ust_trend)
            clean_symbol = sembol.replace("_", "\\_").replace("=", "\\=").replace(".", "\\.")
            
            if sinyal in ["LONG", "SHORT"]:
                islem = trading_system.pozisyon_ac(sembol, sinyal, fiyat, tp, sl, sebep)
                if islem:
                    emoji = "🟢" if sinyal == "LONG" else "🔴"
                    msg = (
                        f"{emoji} *{sinyal} İŞLEM AÇILDI*\n\n"
                        f"📌 *Varlık:* `{clean_symbol}` ({kategori})\n"
                        f"💵 *Giriş Fiyatı:* `${fiyat:.2f}`\n"
                        f"🎯 *TP:* `${tp:.2f}` | 🛑 *SL:* `${sl:.2f}`\n"
                        f"💡 *Sebep:* {sebep}"
                    )
                    send_telegram_msg(msg)
                    
                    chart_buf = grafik_olustur_ve_hazirla(df_1h, sembol, sinyal)
                    if chart_buf:
                        send_telegram_photo(chart_buf, caption=f"📊 `{clean_symbol}` Giriş Grafiği")

            if sembol in trading_system.acik_pozisyonlar:
                poz = trading_system.acik_pozisyonlar[sembol]
                
                if poz['yon'] == "LONG":
                    if fiyat >= poz['tp_fiyat'] and poz['tp_fiyat'] > 0:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "TAKE_PROFIT")
                        send_telegram_msg(f"✅ *LONG KARLA KAPANDI! (TP)*\n📌 `{clean_symbol}`\n💵 Kâr: `${k['kar_zarar']:+,.2f}`\n💰 *GÜNCEL KASA:* `${k['guncel_kasa']:,.2f}`")
                    elif fiyat <= poz['sl_fiyat'] and poz['sl_fiyat'] > 0:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "STOP_LOSS")
                        send_telegram_msg(f"❌ *LONG STOP OLDU! (SL)*\n📌 `{clean_symbol}`\n💸 Zarar: `${k['kar_zarar']:+,.2f}`\n💰 *GÜNCEL KASA:* `${k['guncel_kasa']:,.2f}`")
                
                elif poz['yon'] == "SHORT":
                    if fiyat <= poz['tp_fiyat'] and poz['tp_fiyat'] > 0:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "TAKE_PROFIT")
                        send_telegram_msg(f"✅ *SHORT KARLA KAPANDI! (TP)*\n📌 `{clean_symbol}`\n💵 Kâr: `${k['kar_zarar']:+,.2f}`\n💰 *GÜNCEL KASA:* `${k['guncel_kasa']:,.2f}`")
                    elif fiyat >= poz['sl_fiyat'] and poz['sl_fiyat'] > 0:
                        k = trading_system.pozisyon_kapat(sembol, fiyat, "STOP_LOSS")
                        send_telegram_msg(f"❌ *SHORT STOP OLDU! (SL)*\n📌 `{clean_symbol}`\n💸 Zarar: `${k['kar_zarar']:+,.2f}`\n💰 *GÜNCEL KASA:* `${k['guncel_kasa']:,.2f}`")

def zamanlayici_dongusu():
    schedule.every(TARAMA_PERIYODU_DAKIKA).minutes.do(analiz_dongusu)
    schedule.every(1).hours.do(saatlik_kasa_raporu)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    send_telegram_msg("🚀 *İnteraktif Bot Servisi ve Taramalar Başlatıldı!*")
    saatlik_kasa_raporu()
    
    t = threading.Thread(target=zamanlayici_dongusu, daemon=True)
    t.start()
    
    bot_app = bot_uygulamasini_baslat()
    if bot_app:
        # Sinyal çakışmasını (uvloop add_signal_handler hatasını) önlemek için stop_signals=None eklendi
        bot_app.run_polling(stop_signals=None)