import requests
from config import TELEGRAM_TOKEN, CHAT_ID

def send_telegram_msg(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram Token veya Chat ID bulunamadı.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Gönderim Hatası: {e}")