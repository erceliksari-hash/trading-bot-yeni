# trading_engine.py - Sanal Kasa ve Pozisyon Yönetim Motoru
import json
import os
from datetime import datetime
from config import BASLANGIC_KASASI, MAX_KALDIRAC, ISLEM_BASI_RISK_YUZDESI

class TradingEngine:
    def __init__(self, log_file="islem_gecmisi.json"):
        self.log_file = log_file
        self.kasa = BASLANGIC_KASASI
        self.acik_pozisyonlar = {}
        self.gecmis_islemler = []
        self.kaldirac = MAX_KALDIRAC
        self._yukle()

    def _yukle(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.kasa = data.get("kasa", BASLANGIC_KASASI)
                    self.acik_pozisyonlar = data.get("acik_pozisyonlar", {})
                    self.gecmis_islemler = data.get("gecmis_islemler", [])
            except Exception as e:
                print(f"⚠️ Kasa kayıtları okunamadı: {e}")

    def kaydet(self):
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump({
                    "kasa": self.kasa,
                    "acik_pozisyonlar": self.acik_pozisyonlar,
                    "gecmis_islemler": self.gecmis_islemler
                }, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Kasa kaydetme hatası: {e}")

    def pozisyon_ac(self, sembol: str, yon: str, fiyat: float, tp_fiyat: float, sl_fiyat: float, sebep: str):
        if sembol in self.acik_pozisyonlar or fiyat <= 0 or self.kasa <= 0:
            return None

        marjin = self.kasa * ISLEM_BASI_RISK_YUZDESI
        pozisyon_buyuklugu = marjin * self.kaldirac
        miktar = pozisyon_buyuklugu / fiyat

        self.acik_pozisyonlar[sembol] = {
            "yon": yon,
            "giris_fiyati": fiyat,
            "miktar": miktar,
            "tp_fiyat": tp_fiyat,
            "sl_fiyat": sl_fiyat,
            "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "giris_sebebi": sebep
        }
        self.kaydet()
        return self.acik_pozisyonlar[sembol]

    def pozisyon_kapat(self, sembol: str, mevcut_fiyat: float, kapanis_sebebi: str):
        if sembol not in self.acik_pozisyonlar:
            return None
            
        poz = self.acik_pozisyonlar.pop(sembol)
        giris = poz["giris_fiyati"]
        miktar = poz["miktar"]
        yon = poz["yon"]
        
        if yon == "LONG":
            kar_zarar = (mevcut_fiyat - giris) * miktar
        else:
            kar_zarar = (giris - mevcut_fiyat) * miktar
            
        self.kasa += kar_zarar
        
        kayit = {
            "sembol": sembol,
            "yon": yon,
            "giris": giris,
            "cikis": mevcut_fiyat,
            "kar_zarar": kar_zarar,
            "guncel_kasa": self.kasa, 
            "kapanis_sebebi": kapanis_sebebi,
            "hatali_islem_mi": kar_zarar < 0,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.gecmis_islemler.append(kayit)
        self.kaydet()
        return kayit