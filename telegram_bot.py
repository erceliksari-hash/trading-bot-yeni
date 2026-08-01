# telegram_bot.py - İnteraktif Telegram Bot Modülü
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes
)

from config import TELEGRAM_TOKEN, BASLANGIC_KASASI
from analysis_engine import AnalysisEngine
from trading_engine import TradingEngine
from utils import varlik_listesini_oku, varlik_listesini_kaydet, veri_getir, ust_trend_tespit_et

logging.basicConfig(level=logging.INFO)
trading_system = TradingEngine()

def ana_menu_klavyesi():
    keyboard = [
        [
            InlineKeyboardButton("🟡 Kripto Analizleri", callback_data="analiz_KRIPTO"),
            InlineKeyboardButton("🇹🇷 BIST Taraması", callback_data="analiz_BIST")
        ],
        [
            InlineKeyboardButton("🇺🇸 ABD Hisseleri", callback_data="analiz_US_STOCKS"),
            InlineKeyboardButton("🥇 Emtia & Forex", callback_data="analiz_FOREX_EMTIA")
        ],
        [
            InlineKeyboardButton("💼 Portföy / Kasa Durumu", callback_data="kasa_durumu"),
            InlineKeyboardButton("⚙️ İzleme Listesi", callback_data="liste_yonetimi")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 *Otonom Finansal Analiz & Ticaret Botu*\n\n"
        "Aşağıdaki menüden kategori seçerek anlık analiz raporu alabilir, "
        "kasa durumunuzu inceleyebilir veya izleme listenizi yönetebilirsiniz."
    )
    await update.message.reply_text(msg, reply_markup=ana_menu_klavyesi(), parse_mode="Markdown")

async def buton_tiklama_olayi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("analiz_"):
        kategori = data.replace("analiz_", "")
        varliklar = varlik_listesini_oku().get(kategori, [])

        await query.edit_message_text(
            f"⏳ *{kategori}* kategorisindeki {len(varliklar)} varlık taranıyor, lütfen bekleyin...",
            parse_mode="Markdown"
        )

        rapor = f"📊 *{kategori} CANLI TARAMA RAPORU*\n"
        rapor += "-----------------------------------\n"
        
        for sembol in varliklar:
            clean_symbol = sembol.replace("_", "\\_").replace("=", "\\=").replace(".", "\\.")
            df = veri_getir(sembol, kategori, timeframe="1h", limit=100)
            
            if df is not None and len(df) > 30:
                ust_trend = ust_trend_tespit_et(sembol, kategori)
                engine = AnalysisEngine(df)
                sinyal, fiyat, sl, tp, gerekce = engine.sinyal_uret(ust_trend_yonu=ust_trend)
                
                durum_emoji = "🟢" if sinyal == "LONG" else ("🔴" if sinyal == "SHORT" else "⚪")
                rapor += f"{durum_emoji} `{clean_symbol}`: *{sinyal}* | Fiyat: `${fiyat:.2f}`\n"
            else:
                rapor += f"⚠️ `{clean_symbol}`: Veri Alınamadı\n"

        await query.edit_message_text(rapor, reply_markup=ana_menu_klavyesi(), parse_mode="Markdown")

    elif data == "kasa_durumu":
        kasa = trading_system.kasa
        toplam_kar = kasa - BASLANGIC_KASASI
        yuzde = (toplam_kar / BASLANGIC_KASASI) * 100
        durum = "📈" if toplam_kar >= 0 else "📉"

        msg = (
            f"💼 *CANLI KASA VE PORTFÖY RAPORU*\n"
            f"-----------------------------------\n"
            f"💰 *Mevcut Kasa:* `${kasa:,.2f}`\n"
            f"{durum} *Toplam Kâr/Zarar:* `${toplam_kar:+,.2f}` (%{yuzde:+.2f})\n"
            f"🔓 *Açık Pozisyon Sayısı:* `{len(trading_system.acik_pozisyonlar)}`\n"
            f"📜 *Geçmiş İşlem Sayısı:* `{len(trading_system.gecmis_islemler)}`"
        )
        await query.edit_message_text(msg, reply_markup=ana_menu_klavyesi(), parse_mode="Markdown")

    elif data == "liste_yonetimi":
        data_json = varlik_listesini_oku()
        msg = "⚙️ *MEVCUT İZLEME LİSTELERİ*\n\n"
        for kat, liste in data_json.items():
            clean_liste = [v.replace("_", "\\_").replace("=", "\\=").replace(".", "\\.") for v in liste]
            msg += f"📌 *{kat}*: {', '.join(clean_liste)}\n"

        msg += (
            "\n➕ *Varlık Eklemek İçin:* `/ekle KATEGORİ KOD`\n"
            "Örn: `/ekle KRIPTO AVAX/USDT` veya `/ekle BIST THYAO.IS`\n\n"
            "➖ *Varlık Çıkarmak İçin:* `/cikar KATEGORİ KOD`\n"
            "Örn: `/cikar US_STOCKS TSLA`"
        )
        await query.edit_message_text(msg, reply_markup=ana_menu_klavyesi(), parse_mode="Markdown")

async def varlik_ekle_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kategori = context.args[0].upper()
        kod = context.args[1].upper()

        data = varlik_listesini_oku()
        if kategori in data:
            if kod not in data[kategori]:
                data[kategori].append(kod)
                varlik_listesini_kaydet(data)
                await update.message.reply_text(f"✅ `{kod}`, *{kategori}* listesine eklendi.", parse_mode="Markdown")
            else:
                await update.message.reply_text(f"⚠️ `{kod}` zaten *{kategori}* listesinde var.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ Geçersiz kategori. Kategoriler: {list(data.keys())}")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Hatalı kullanım! Örnek: `/ekle KRIPTO AVAX/USDT`", parse_mode="Markdown")

async def varlik_cikar_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kategori = context.args[0].upper()
        kod = context.args[1].upper()

        data = varlik_listesini_oku()
        if kategori in data and kod in data[kategori]:
            data[kategori].remove(kod)
            varlik_listesini_kaydet(data)
            await update.message.reply_text(f"🗑️ `{kod}`, *{kategori}* listesinden çıkarıldı.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ `Kod` bulunamadı veya kategori hatalı.", parse_mode="Markdown")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Hatalı kullanım! Örnek: `/cikar BIST SASA.IS`", parse_mode="Markdown")

def bot_uygulamasini_baslat():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN":
        print("⚠️ Telegram token geçerli değil, bot başlatılamadı.")
        return None

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_komutu))
    app.add_handler(CommandHandler("menu", start_komutu))
    app.add_handler(CommandHandler("ekle", varlik_ekle_komutu))
    app.add_handler(CommandHandler("cikar", varlik_cikar_komutu))
    app.add_handler(CallbackQueryHandler(buton_tiklama_olayi))
    return app