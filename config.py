# config.py - Çoklu Piyasa & Otonom Ticaret Konfigürasyonu
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

VARLIK_LISTESI = {
    "KRIPTO": [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT", 
        "XRP/USDT", "BNB/USDT", "ADA/USDT", "LINK/USDT"
    ],
    "BIST": [
        "THYAO.IS", "ASELS.IS", "GARAN.IS", "EREGL.IS", 
        "KCHOL.IS", "SASA.IS"
    ],
    "US_STOCKS": [
        "AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMD", 
        "QQQ", "SPY"
    ],
    "FOREX_EMTIA": [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", 
        "GC=F", "CL=F"
    ]
}

TARAMA_PERIYODU_DAKIKA = 60
GIRIS_PERIYODU = "1h"
TREND_PERIYODU = "4h"

BASLANGIC_KASASI = 10000.0
ISLEM_BASI_RISK_YUZDESI = 0.02
GUNLUK_HEDEF_YUZDE = 0.015
MAX_KALDIRAC = 3
STOP_LOSS_YUZDE = 0.015         
TAKIPLI_STOP_YUZDE = 0.01       
RISK_REWARD_ORANI = 2.0         

VERI_DOSYALARI = {
    "WALLETS": "islem_gecmisi.json",
    "TRADE_ERRORS": "trade_errors.json"
}