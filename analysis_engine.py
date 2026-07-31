import pandas as pd
import pandas_ta as ta

class AnalysisEngine:
    
    @classmethod
    def indikatörleri_ekle(cls, df):
        """DataFrame üzerine RSI, MACD, EMA ve ATR indikatörlerini ekler."""
        df = df.copy()
        
        # Yeterli veri yoksa işlem yapmadan döndür
        if df is None or len(df) < 30:
            return df

        # 1. RSI (14) Hesaplama
        rsi = df.ta.rsi(length=14)
        df['RSI'] = rsi.squeeze() if isinstance(rsi, pd.DataFrame) else rsi

        # 2. EMA (50 ve 200) Hesaplama
        ema50 = df.ta.ema(length=50)
        df['EMA_50'] = ema50.squeeze() if isinstance(ema50, pd.DataFrame) else ema50

        # Veri sayısı 200'den az ise hata vermemesi için kontrol
        if len(df) >= 200:
            ema200 = df.ta.ema(length=200)
            df['EMA_200'] = ema200.squeeze() if isinstance(ema200, pd.DataFrame) else ema200
        else:
            # 200'den az mum varsa hata almamak için EMA_50 değerini atıyoruz
            df['EMA_200'] = df['EMA_50']

        # 3. MACD Hesaplama
        macd = df.ta.macd(fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty and macd.shape[1] >= 3:
            df['MACD'] = macd.iloc[:, 0]        # MACD Çizgisi
            df['MACD_Hist'] = macd.iloc[:, 1]   # Histogram
            df['MACD_Signal'] = macd.iloc[:, 2] # Sinyal Çizgisi

        # 4. ATR Hesaplama
        atr = df.ta.atr(length=14)
        df['ATR'] = atr.squeeze() if isinstance(atr, pd.DataFrame) else atr

        return df

    @classmethod
    def sahte_sinyal_ve_trend_analizi(cls, df):
        """Trendi ve Alım/Satım sinyallerini analiz eder."""
        df = cls.indikatörleri_ekle(df)
        
        if df is None or len(df) < 2:
            return {'fiyat': 0, 'rsi': 50, 'trend': 'YOK', 'long_sinyal': False, 'short_sinyal': False}

        son_bar = df.iloc[-1]
        onceki_bar = df.iloc[-2]
        
        fiyat = son_bar['close']
        rsi = son_bar.get('RSI', 50)
        
        # Trend Tespiti
        trend = "NOTR"
        if son_bar.get('EMA_50', 0) > son_bar.get('EMA_200', 0):
            trend = "YUKARI (BOGA)"
        elif son_bar.get('EMA_50', 0) < son_bar.get('EMA_200', 0):
            trend = "ASAGI (AYI)"
            
        # MACD Sinyal Kesişimi
        macd_boga_kesisim = (onceki_bar.get('MACD', 0) <= onceki_bar.get('MACD_Signal', 0)) and (son_bar.get('MACD', 0) > son_bar.get('MACD_Signal', 0))
        macd_ayi_kesisim = (onceki_bar.get('MACD', 0) >= onceki_bar.get('MACD_Signal', 0)) and (son_bar.get('MACD', 0) < son_bar.get('MACD_Signal', 0))
        
        long_sinyal = macd_boga_kesisim and rsi > 45 and trend == "YUKARI (BOGA)"
        short_sinyal = macd_ayi_kesisim and rsi < 55 and trend == "ASAGI (AYI)"
        
        return {
            'fiyat': fiyat,
            'rsi': rsi,
            'trend': trend,
            'long_sinyal': long_sinyal,
            'short_sinyal': short_sinyal
        }

    @staticmethod
    def destek_direnc_hesapla(df, period=20):
        """Son periyot içindeki en düşük ve en yüksek seviyeleri hesaplar."""
        destek = df['low'].tail(period).min()
        direnc = df['high'].tail(period).max()
        return destek, direnc

    @staticmethod
    def fibonacci_seviyeleri(df):
        """Fibonacci seviyelerini üretir."""
        en_yüksek = df['high'].max()
        en_düşük = df['low'].min()
        fark = en_yüksek - en_düşük
        
        return {
            'fib_0.236': en_yüksek - (fark * 0.236),
            'fib_0.382': en_yüksek - (fark * 0.382),
            'fib_0.500': en_yüksek - (fark * 0.500),
            'fib_0.618': en_yüksek - (fark * 0.618)
        }

# Class dışında (sol hizada) yer almalı
if __name__ == '__main__':
    print("AnalysisEngine modülü başarıyla yüklendi ve teste hazır.")