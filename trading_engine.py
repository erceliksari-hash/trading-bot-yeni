import json
import os
from datetime import datetime
from config import BASLANGIC_KASASI, MAX_KALDIRAC, STOP_LOSS_YUZDE

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
            with open(self.log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.kasa = data.get("kasa", BASLANGIC_KASASI)
                self.acik_pozisyonlar = data.get("acik_pozisyonlar", {})
                self.gecmis_islemler = data.get("gecmis_islemler", [])

    def kaydet(self):
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump({
                "kasa": self.kasa,
                "acik_pozisyonlar": self.acik_pozisyonlar,
                "gecmis_islemler": self.gecmis_islemler
            }, f, indent=4)

    def pozisyon_ac(self, sembol, yon, fiyat, tp_fiyat, sl_fiyat, sebep):
        if sembol in self.acik_pozisyonlar:
            return None # Zaten açık pozisyon var
            
        miktar = (self.kasa * 0.10 * self.kaldirac) / fiyat # Kasanın %10'u ile pozisyon
        self.acik_pozisyonlar[sembol] = {
            "yon": yon, # "LONG" veya "SHORT"
            "giris_fiyati": fiyat,
            "miktar": miktar,
            "tp_fiyat": tp_fiyat,
            "sl_fiyat": sl_fiyat,
            "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "giris_sebebi": sebep
        }
        self.kaydet()
        return self.acik_pozisyonlar[sembol]

    def pozisyon_kapat(self, sembol, mevcut_fiyat, kapanis_sebebi):
        if sembol not in self.acik_pozisyonlar:
            return None
            
        poz = self.acik_pozisyonlar.pop(sembol)
        giris = poz["giris_fiyati"]
        miktar = poz["miktar"]
        yon = poz["yon"]
        
        if yon == "LONG":
            kar_zarar = (mevcut_fiyat - giris) * miktar
        else: # SHORT
            kar_zarar = (giris - mevcut_fiyat) * miktar
            
        self.kasa += kar_zarar
        
        kayit = {
            "sembol": sembol,
            "yon": yon,
            "giris": giris,
            "cikis": mevcut_fiyat,
            "kar_zarar": kar_zarar,
            "kapanis_sebebi": kapanis_sebebi,
            "hatali_islem_mi": kar_zarar < 0,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.gecmis_islemler.append(kayit)
        self.kaydet()
        return kayit