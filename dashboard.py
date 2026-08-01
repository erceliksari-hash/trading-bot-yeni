# dashboard.py - Streamlit Web Dashboard & Canlı Grafik Paneli
import streamlit as st
import pandas as pd
import plotly.graph_objects as gg
from plotly.subplots import make_subplots
import json
import os

from utils import veri_getir, ust_trend_tespit_et, varlik_listesini_oku
from analysis_engine import AnalysisEngine
from config import BASLANGIC_KASASI, VERI_DOSYALARI

st.set_page_config(page_title="Otonom Ticaret Paneli", layout="wide", page_icon="📈")

st.title("🚀 Otonom Finansal Analiz & Ticaret Paneli (1H / 4H)")

islem_gecmisi_dosyasi = VERI_DOSYALARI.get("WALLETS", "islem_gecmisi.json")
kasa_miktari = BASLANGIC_KASASI
acik_pozisyonlar = {}
gecmis_islemler = []

if os.path.exists(islem_gecmisi_dosyasi):
    try:
        with open(islem_gecmisi_dosyasi, "r", encoding="utf-8") as f:
            data = json.load(f)
            kasa_miktari = data.get("kasa", BASLANGIC_KASASI)
            acik_pozisyonlar = data.get("acik_pozisyonlar", {})
            gecmis_islemler = data.get("gecmis_islemler", [])
    except Exception as e:
        st.error(f"Kasa verisi hatası: {e}")

col1, col2, col3 = st.columns(3)
kar_orani = ((kasa_miktari - BASLANGIC_KASASI) / BASLANGIC_KASASI) * 100
col1.metric("💰 Sanal Kasa Bakiyesi", f"${kasa_miktari:,.2f}", f"{kar_orani:+.2f}%")
col2.metric("🔓 Açık Pozisyonlar", len(acik_pozisyonlar))
col3.metric("📜 Toplam Tamamlanan İşlem", len(gecmis_islemler))

st.markdown("---")

aktif_varlik_listesi = varlik_listesini_oku()

st.sidebar.header("🎯 Varlık Seçimi")
kategori = st.sidebar.selectbox("Kategori", list(aktif_varlik_listesi.keys()))
sembol = st.sidebar.selectbox("Varlık", aktif_varlik_listesi[kategori])
zaman_dilimi = st.sidebar.selectbox("Periyot", ["1h", "4h"], index=0)

df = veri_getir(sembol, kategori, timeframe=zaman_dilimi)

if df is not None and len(df) > 30:
    ust_trend = ust_trend_tespit_et(sembol, kategori)
    engine = AnalysisEngine(df)
    df_islenmis = engine.indikatorleri_hesapla()
    fib = engine.fibonacci_seviyeleri()
    güvenli_mi = engine.sahte_sinyal_kontrolu()
    sinyal, fiyat, sl, tp, gerekce = engine.sinyal_uret(ust_trend_yonu=ust_trend)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
    time_col = 'timestamp' if 'timestamp' in df_islenmis.columns else df_islenmis.index

    fig.add_trace(gg.Candlestick(
        x=df_islenmis[time_col],
        open=df_islenmis['open'], high=df_islenmis['high'],
        low=df_islenmis['low'], close=df_islenmis['close'], name="Fiyat"
    ), row=1, col=1)

    if 'EMA_20' in df_islenmis.columns:
        fig.add_trace(gg.Scatter(x=df_islenmis[time_col], y=df_islenmis['EMA_20'], mode='lines', name='EMA 20', line=dict(color='orange', width=1)), row=1, col=1)
    if 'EMA_50' in df_islenmis.columns:
        fig.add_trace(gg.Scatter(x=df_islenmis[time_col], y=df_islenmis['EMA_50'], mode='lines', name='EMA 50', line=dict(color='blue', width=1)), row=1, col=1)

    if fib:
        fig.add_hline(y=fib.get("Fib_0.618", 0), line_dash="dash", line_color="green", annotation_text=f"Fib 0.618: {fib.get('Fib_0.618', 0):.2f}", row=1, col=1)

    if 'RSI' in df_islenmis.columns:
        fig.add_trace(gg.Scatter(x=df_islenmis[time_col], y=df_islenmis['RSI'], mode='lines', name='RSI', line=dict(color='purple')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

    fig.update_layout(title=f"{sembol} ({zaman_dilimi.upper()}) Canlı Analiz Grafiği", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 Yapay Zekâ & Multi-Timeframe Değerlendirme")
    col_a, col_b, col_c = st.columns(3)
    col_a.info(f"**Mevcut Fiyat:** ${fiyat:.2f}")
    col_b.warning(f"**4H Ana Trend:** {ust_trend} | **1H Sinyal:** {sinyal}")
    col_c.error(f"**Sahte Kırılım Riski:** {'GÜVENLİ' if güvenli_mi else 'RİSKLİ (Doji/Kararsız)'}")

    st.markdown("##### 🔢 Hedefler & Gerekçe")
    st.caption(f"**Gerekçe:** {gerekce}")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.json(fib)
    with col_f2:
        st.write(f"🎯 **Hedef (Take Profit):** ${tp:.2f}")
        st.write(f"🛑 **Zarar Kes (Stop Loss):** ${sl:.2f}")

else:
    st.warning("Seçilen varlık için yeterli veri alınamadı.")

st.markdown("---")
st.subheader("📜 Geçmiş İşlem Kayıtları")
if gecmis_islemler:
    st.dataframe(pd.DataFrame(gecmis_islemler), use_container_width=True)
else:
    st.info("Henüz tamamlanmış bir işlem bulunmuyor.")