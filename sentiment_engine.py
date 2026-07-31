import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY"))

class SentimentEngine:
    @staticmethod
    def duygu_analizi_yap(sembol, son_haberler_metni):
        """
        Piyasa haberlerini GPT-4o ile analiz eder.
        Döndürülen Değerler: 
        - duygu_skoru (-100: Aşırı Ayı, +100: Aşırı Boğa)
        - karar ("LONG_ONAY", "SHORT_ONAY", "PAS")
        """
        prompt = f"""
        Sen kıdemli bir finansal analiz uzmanısın. Aşağıda belirtilen varlığa ait son haber ve piyasa bilgilerini değerlendir.
        
        Varlık: {sembol}
        Piyasa Haberleri / Özet:
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
            print(f"Piyasa Duygu Analiz Hatası: {e}")
            return {"duygu_skoru": 0, "karar": "PAS", "ozet_yorum": "Analiz sırasında hata oluştu."}