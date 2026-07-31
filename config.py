import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

# --- SEÇİLEBİLİR VARLIK LİSTELERİ ---
VARLIK_LISTESI = {
    # Kripto Paralar (CCXT / Binance / Bitget)
    "KRIPTO": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", "XRP/USDT"],
    
    # Borsa İstanbul (BIST - YFinance)
    "BIST": ["THYAO.IS", "ASELS.IS", "GARAN.IS", "EREGL.IS"],
    
    # Amerikan Borsaları & Fonlar (YFinance)
    "US_STOCKS": ["AAPL", "NVDA", "TSLA", "MSFT", "QQQ", "SPY"],
    
    # Forex & Emtialar (YFinance)
    "FOREX_EMTIA": ["EURUSD=X", "GBPUSD=X", "GC=F", "CL=F"] # GC=F (Altın), CL=F (Petrol)
}

# --- STRATEJİ VE RISK AYARLARI ---
BASLANGIC_KASASI = 10000.0  # Sanal USDT / USD
GUNLUK_HEDEF_YUZDE = 0.015  # %1.5 Temel Hedef Kar
MAX_KALDIRAC = 3            # Kaldıraç Önerisi (1x - 5x)
STOP_LOSS_YUZDE = 0.015     # %1.5 Zarar Kes
TAKIPLI_STOP_YUZDE = 0.01   # %1.0 Trailing Stop