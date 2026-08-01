# telegram_notifier.py - Telegram Bildirim Yardımcı Modülü
import requests
from config import TELEGRAM_TOKEN, CHAT_ID

def send_telegram_msg(message: str):
    if not TELEGRAM_TOKEN or not CHAT_ID or TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN":
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram mesaj gönderme hatası: {e}")

def send_telegram_photo(photo_buffer, caption: str = ""):
    if not TELEGRAM_TOKEN or not CHAT_ID or TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN":
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("grafik.png", photo_buffer, "image/png")}
    data = {
        "chat_id": CHAT_ID,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data, files=files, timeout=15)
    except Exception as e:
        print(f"⚠️ Telegram fotoğraf gönderme hatası: {e}")