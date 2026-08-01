# analysis_engine.py - Teknik Analiz ve Sinyal Motoru
import pandas as pd
import pandas_ta as ta

class AnalysisEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy() if df is not None else None

    def ozel_pin_script_indikatoru(self) -> pd.DataFrame:
        if self.df is None or len(self.df) < 5:
            return self.df
        self.df['OZEL_INDIKATOR_SIGNAL'] = "NETRAL" 
        self.df['OZEL_INDIKATOR_SKOR'] = 0.0
        return self.df

    def indikatorleri_hesapla(self) -> pd.DataFrame:
        if self.df is None or len(self.df) < 30:
            return self.df

        self.df.columns = [c.lower() for c in self.df.columns]

        rsi = self.df.ta.rsi(length=14)
        self.df['RSI'] = rsi.squeeze() if isinstance(rsi, pd.DataFrame) else rsi

        ema20 = self.df.ta.ema(length=20)
        self.df['EMA_20'] = ema20.squeeze() if isinstance(ema20, pd.DataFrame) else ema20

        ema50 = self.df.ta.ema(length=50)
        self.df['EMA_50'] = ema50.squeeze() if isinstance(ema50, pd.DataFrame) else ema50

        if len(self.df) >= 200:
            ema200 = self.df.ta.ema(length=200)
            self.df['EMA_200'] = ema200.squeeze() if isinstance(ema200, pd.DataFrame) else ema200
        else:
            self.df['EMA_200'] = self.df['EMA_50']

        macd = self.df.ta.macd(fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty and macd.shape[1] >= 3:
            self.df['MACD'] = macd.iloc[:, 0]
            self.df['MACD_Hist'] = macd.iloc[:, 1]
            self.df['MACD_Signal'] = macd.iloc[:, 2]

        atr = self.df.ta.atr(length=14)
        self.df['ATR'] = atr.squeeze() if isinstance(atr, pd.DataFrame) else atr

        self.ozel_pin_script_indikatoru()
        return self.df

    def fibonacci_seviyeleri(self) -> dict:
        if self.df is None or len(self.df) < 20:
            return {}
        
        en_yuksek = self.df['high'].max()
        en_dusuk = self.df['low'].min()
        fark = en_yuksek - en_dusuk
        
        return {
            "Fib_0.236": en_yuksek - (fark * 0.236),
            "Fib_0.382": en_yuksek - (fark * 0.382),
            "Fib_0.500": en_yuksek - (fark * 0.500),
            "Fib_0.618": en_yuksek - (fark * 0.618)
        }

    def sahte_sinyal_kontrolu(self) -> bool:
        if self.df is None or len(self.df) < 5:
            return True
            
        son_bar = self.df.iloc[-1]
        govde = abs(son_bar['close'] - son_bar['open'])
        toplam_boy = son_bar['high'] - son_bar['low']
        
        if toplam_boy > 0 and (govde / toplam_boy) < 0.20:
            return False 
        return True

    def sinyal_uret(self, ust_trend_yonu: str = "NETRAL"):
        df_islenmis = self.indikatorleri_hesapla()
        if df_islenmis is None or len(df_islenmis) < 2:
            return "PAS", 0.0, 0.0, 0.0, "Yetersiz veri."

        son_bar = df_islenmis.iloc[-1]
        onceki_bar = df_islenmis.iloc[-2]

        fiyat = son_bar['close']
        rsi = son_bar.get('RSI', 50)
        atr = son_bar.get('ATR', fiyat * 0.015)
        if pd.isna(atr) or atr <= 0:
            atr = fiyat * 0.015

        ema50 = son_bar.get('EMA_50', 0)
        ema200 = son_bar.get('EMA_200', 0)

        macd_boga = (onceki_bar.get('MACD', 0) <= onceki_bar.get('MACD_Signal', 0)) and (son_bar.get('MACD', 0) > son_bar.get('MACD_Signal', 0))
        macd_ayi = (onceki_bar.get('MACD', 0) >= onceki_bar.get('MACD_Signal', 0)) and (son_bar.get('MACD', 0) < son_bar.get('MACD_Signal', 0))

        sinyal = "PAS"
        gerekce = "Belirgin sinyal yok veya 4H trend teyit etmiyor."

        if macd_boga and rsi > 45 and ema50 > ema200:
            if ust_trend_yonu in ["BOGA", "NETRAL"]:
                sinyal = "LONG"
                gerekce = f"1H MACD Boğa Kesişimi + 4H Boğa Trend Teyidi (RSI: {rsi:.1f})"

        elif macd_ayi and rsi < 55 and ema50 < ema200:
            if ust_trend_yonu in ["AYI", "NETRAL"]:
                sinyal = "SHORT"
                gerekce = f"1H MACD Ayı Kesişimi + 4H Ayı Trend Teyidi (RSI: {rsi:.1f})"

        if sinyal == "LONG":
            sl = fiyat - (atr * 1.5)
            tp = fiyat + (atr * 3.0)
        elif sinyal == "SHORT":
            sl = fiyat + (atr * 1.5)
            tp = fiyat - (atr * 3.0)
        else:
            sl, tp = 0.0, 0.0

        return sinyal, fiyat, sl, tp, gerekce