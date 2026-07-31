import streamlit as st
import pandas as pd
import plotly.graph_objects as gg
from plotly.subplots import make_subplots
import json
import os

# Proje Modüllerimizden Veri Çekme Fonksiyonları
from main import veri_getir
from analysis_engine import AnalysisEngine
from config import VARLIK_LISTESI, BASLANGIC_KASASI

st.set_page_config(page_title="Otonom Ticaret & Analiz Paneli", layout="wide", page_icon="📈")

# --- BAŞLIK VE KASA BİLGİLERİ ---
st.title("🚀 Otonom Finansal Analiz & Ticaret Paneli")

# Sanal Kasa Verilerini Okuma
islem_gecmisi_dosyasi = "islem_gecmisi.json"
kasa_miktari = BASLANGIC_KASASI
acik_pozisyonlar = {}
gecmis_islemler = []

if os.path.exists(islem_gecmisi_dosyasi):
    with open(islem_gecmisi_dosyasi, "r", encoding="utf-8") as f:
        data = json.load(f)
        kasa_miktari = data.get("kasa", BASLANGIC_KASASI)
        acik_pozisyonlar = data.get("acik_pozisyonlar", {})
        gecmis_islemler = data.get("gecmis_islemler", [])

# Özet Bakiye Metrikleri
col1, col2, col3 = st.columns(3)
col1.metric("💰 Sanal Kasa Bakiyesi", f"${kasa_miktari:,.2f}", f"{((kasa_miktari - BASLANGIC_KASASI)/BASLANGIC_KASASI)*100:.2f}%")
col2.metric("🔓 Açık Pozisyonlar", len(acik_pozisyonlar))
col3.metric("📜 Toplam Tamamlanan İşlem", len(gecmis_islemler))

st.markdown("---")

# --- YAN MENÜ (VARLIK SEÇİMİ) ---
st.sidebar.header("🎯 Analiz Edilecek Varlık")
kategori = st.sidebar.selectbox("Kategori Seçin", list(VARLIK_LISTESI.keys()))
sembol = st.sidebar.selectbox("Varlık Seçin", VARLIK_LISTESI[kategori])

# --- CANLI GRAFİK OLUŞTURMA ---
df = veri_getir(sembol, kategori)

if df is not None and len(df) > 30:
    df = AnalysisEngine.indikatörleri_ekle(df)
    destek, direnc = AnalysisEngine.destek_direnc_hesapla(df)
    fib = AnalysisEngine.fibonacci_seviyeleri(df)
    analiz = AnalysisEngine.sahte_sinyal_ve_trend_analizi(df)

    # Candlestick ve RSI için 2 Alt Grafik (Subplot)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])

    # 1. Mum Grafiği (Price)
    fig.add_trace(gg.Candlestick(
        x=df['timestamp'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="Fiyat"
    ), row=1, col=1)

    # EMA 20 & 50 Çizgileri
    fig.add_trace(gg.Scatter(x=df['timestamp'], y=df['EMA_20'], mode='lines', name='EMA 20', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(gg.Scatter(x=df['timestamp'], y=df['EMA_50'], mode='lines', name='EMA 50', line=dict(color='blue', width=1)), row=1, col=1)

    # Destek ve Direnç Seviyeleri Çizgileri
    fig.add_hline(y=destek, line_dash="dash", line_color="green", annotation_text=f"Destek: {destek:.2f}", row=1, col=1)
    fig.add_hline(y=direnc, line_dash="dash", line_color="red", annotation_text=f"Direnç: {direnc:.2f}", row=1, col=1)

    # 2. RSI Grafiği
    fig.add_trace(gg.Scatter(x=df['timestamp'], y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

    fig.update_layout(title=f"{sembol} Canlı Analiz Grafiği", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- TEKNİK ANALİZ SİNYAL VE YORUM PANORAMASI ---
    st.subheader("💡 Yapay Zekâ ve Teknik Değerlendirme")
    col_a, col_b, col_c = st.columns(3)
    col_a.info(f"**Mevcut Fiyat:** ${analiz['fiyat']:.2f}")
    col_b.warning(f"**Piyasa Trendi:** {analiz['trend']}")
    col_c.error(f"**Sahte Sinyal Riski:** {'Var (Fakeout)' if analiz['sahte_sinyal_riski'] else 'Temiz / Güvenli'}")

    st.markdown("##### 🔢 Fibonacci Seviyeleri")
    st.json(fib)

else:
    st.warning("Seçilen varlık için yeterli mum verisi alınamadı.")

# --- İŞLEM GEÇMİŞİ VE PORTFÖY TABLOSU ---
st.markdown("---")
st.subheader("📜 Geçmiş İşlem Kayıtları & Hata Günlüğü")
if gecmis_islemler:
    df_gecmis = pd.DataFrame(gecmis_islemler)
    st.dataframe(df_gecmis, use_container_width=True)
else:
    st.info("Henüz tamamlanmış bir sanal işlem bulunmuyor.")