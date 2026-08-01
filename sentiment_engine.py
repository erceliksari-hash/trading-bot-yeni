# sentiment_engine.py - GPT-4o Tabanlı Piyasa Duygu Analiz Motoru
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key and api_key != "YOUR_OPENAI_KEY" and len(api_key) > 10 else None

class SentimentEngine:
    @staticmethod
    def duygu_analizi_yap(sembol: str, son_haberler_metni: str) -> dict:
        if not client:
            return {
                "duygu_skoru": 0,
                "karar": "PAS",
                "ozet_yorum": "OpenAI API anahtarı tanımlanmadığı için nötr kabul edildi."
            }

        if not son_haberler_metni or len(son_haberler_metni.strip()) < 10:
            return {
                "duygu_skoru": 0,
                "karar": "PAS",
                "ozet_yorum": "Yeterli metin verisi sağlanmadı."
            }

        prompt = f"""
        Sen kıdemli bir finansal analiz uzmanısın. Aşağıda belirtilen varlığa ait bilgileri değerlendir.
        
        Varlık: {sembol}
        Piyasa Durumu / Haber Özeti:
        {son_haberler_metni}
        
        Sadece ve sadece aşağıdaki JSON formatında yanıt ver:
        {{
            "duygu_skoru": < -100 ile +100 arasında tamsayı >,
            "karar": "< LONG_ONAY / SHORT_ONAY / PAS >",
            "ozet_yorum": "< 1-2 cümlelik kısa finansal gerekçe >"
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Finansal duygu analizi yapan hassas bir yapay zekasın. Yalnızca istenen JSON çıktısını üret."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            sonuc = json.loads(response.choices[0].message.content)
            return sonuc
            
        except Exception as e:
            print(f"⚠️ Piyasa Duygu Analiz Hatası [{sembol}]: {e}")
            return {
                "duygu_skoru": 0, 
                "karar": "PAS", 
                "ozet_yorum": f"Analiz hatası: {str(e)}"
            }