import os
import asyncio
from telegram import Update, Document
from telegram.ext import ContextTypes
from deep_translator import GoogleTranslator

SUPPORTED_EXTENSIONS = [".srt", ".vtt", ".ass"]

LANGUAGE_CODES = {
    "বাংলা": "bn",
    "English": "en",
    "Español": "es",
    "Français": "fr",
    "Deutsch": "de",
    "हिन्दी": "hi",
    "العربية": "ar",
    "中文": "zh-CN",
    "Русский": "ru",
    "Português": "pt",
    "日本語": "ja",
    "한국어": "ko",
    "Italiano": "it",
    "Türkçe": "tr",
    "فارسی": "fa",
    "اردو": "ur",
    "Thai": "th",
    "Vietnamese": "vi",
    "Polski": "pl",
    "Nederlands": "nl",
    "Українська": "uk",
    "Čeština": "cs",
    "Ελληνικά": "el",
    "עברית": "he",
    "Svenska": "sv",
    "Norsk": "no",
    "Dansk": "da",
    "Suomi": "fi",
    "Magyar": "hu",
    "Română": "ro",
    "Slovenčina": "sk",
    "Slovenščina": "sl",
    "Hrvatski": "hr",
    "Srpski": "sr",
    "Català": "ca",
    "Filipino": "tl",
    "Indonesian": "id",
    "Malay": "ms",
    "Burmese": "my",
    "Khmer": "km",
    "Lao": "lo",
    "Nepali": "ne",
    "Sinhala": "si",
    "Swahili": "sw",
    "Zulu": "zu",
    "Xhosa": "xh",
    "Afrikaans": "af",
    "Esperanto": "eo",
    "Basque": "eu",
    "Galician": "gl",
    "Icelandic": "is",
    "Macedonian": "mk",
    "Maltese": "mt",
    "Welsh": "cy",
    "Yiddish": "yi",
    "Armenian": "hy",
    "Georgian": "ka",
    "Kazakh": "kk",
    "Uzbek": "uz",
    "Tajik": "tg",
    "Mongolian": "mn",
    "Tibetan": "bo",
    "Amharic": "am",
    "Somali": "so",
    "Hausa": "ha",
    "Igbo": "ig",
    "Yoruba": "yo",
    "Maori": "mi",
    "Samoan": "sm",
    "Tongan": "to",
    "Fijian": "fj",
    "Haitian Creole": "ht",
    "Luxembourgish": "lb",
    "Corsican": "co",
    "Scottish Gaelic": "gd",
    "Irish": "ga",
    "Latin": "la",
    "Esperanto": "eo",
    "Interlingua": "ia",
    "Volapük": "vo",
    "Klingon": "tlh",
    "Elvish": "qya",
    "Sindarin": "sjn",
    "Quenya": "qya",
    "Dothraki": "dothraki",
    "Valyrian": "valyrian",
    "Minionese": "minionese",
    "Pirate": "pirate",
    "Leet Speak": "l33t",
    "Pig Latin": "piglatin",
    "Emoji": "emoji",
    "Gibberish": "gibberish",
    "Morse Code": "morse",
    "Binary": "binary",
    "Braille": "braille",
    "Sign Language": "sign",
    "Navajo": "nv",
    "Cherokee": "chr",
    "Inuktitut": "iu",
    "Greenlandic": "kl",
    "Hawaiian": "haw",
    "Maithili": "mai",
    "Bhojpuri": "bho",
    "Chhattisgarhi": "hne",
    "Magahi": "mag",
    "Awadhi": "awa",
    "Marwari": "mwr",
    "Rajasthani": "raj",
    "Santali": "sat",
    "Dogri": "doi",
    "Konkani": "kok",
    "Bodo": "brx",
    "Kashmiri": "ks",
    "Sindhi": "sd",
    "Assamese": "as",
    "Manipuri": "mni",
    "Mizo": "lus",
    "Khasi": "kha",
    "Garo": "grt",
    "Nepali (India)": "ne-IN",
    "Bengali (India)": "bn-IN",
    "Bengali (Bangladesh)": "bn-BD",
    "Tamil (India)": "ta-IN",
    "Tamil (Sri Lanka)": "ta-LK",
    "Telugu (India)": "te-IN",
    "Kannada (India)": "kn-IN",
    "Malayalam (India)": "ml-IN",
    "Odia (India)": "or-IN",
    "Punjabi (India)": "pa-IN",
    "Punjabi (Pakistan)": "pa-PK",
    "Urdu (India)": "ur-IN",
    "Urdu (Pakistan)": "ur-PK",
    "Hindi (India)": "hi-IN",
    "Hindi (Fiji)": "hi-FJ",
    "Hindi (Mauritius)": "hi-MU",
    "Hindi (Nepal)": "hi-NP",
    "Hindi (Trinidad & Tobago)": "hi-TT",
    "Hindi (United Arab Emirates)": "hi-AE",
    "Hindi (United Kingdom)": "hi-GB",
    "Hindi (United States)": "hi-US"
}

async def subtr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("⚠️ অনুগ্রহ করে একটি সাবটাইটেল ফাইলের রিপ্লাই দিয়ে `/subtr` কমান্ড দিন।")
        return

    document: Document = update.message.reply_to_message.document
    file_extension = os.path.splitext(document.file_name)[1].lower()

    if file_extension not in SUPPORTED_EXTENSIONS:
        await update.message.reply_text("⚠️ শুধুমাত্র .srt, .vtt, এবং .ass ফাইল সমর্থিত।")
        return

    # ভাষা নির্বাচন
    language_buttons = [[lang] for lang in LANGUAGE_CODES.keys()]
    reply_markup = {
        "keyboard": language_buttons,
        "one_time_keyboard": True,
        "resize_keyboard": True
    }
    await update.message.reply_text("🌐 অনুগ্রহ করে লক্ষ্যভাষা নির্বাচন করুন:", reply_markup=reply_markup)

    # ভাষা নির্বাচন অপেক্ষা
    def check_language_selection(msg):
        return msg.from_user.id == update.message.from_user.id and msg.text in LANGUAGE_CODES

    try:
        language_msg = await context.bot.wait_for("message", timeout=60, check=check_language_selection)
        target_language = LANGUAGE_CODES[language_msg.text]
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ সময়সীমা অতিক্রম করেছে। অনুগ্রহ করে পুনরায় চেষ্টা করুন।")
        return

    # ফাইল ডাউনলোড
    file = await context.bot.get_file(document.file_id)
    file_path = f"downloads/{document.file_name}"
    await file.download_to_drive(file_path)

    # অনুবাদ প্রক্রিয়া
    await update.message.reply_text("🔄 অনুবাদ শুরু হচ্ছে...")

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        translated_lines = []
        total_lines = len(lines)
        for index, line in enumerate(lines, start=1):
            if line.strip() and not line.strip().isdigit() and "-->" not in line:
                translated = GoogleTranslator(source='auto', target=target_language).translate(line.strip())
                translated_lines.append(translated + "\n")
            else:
                translated_lines.append(line)

            # লাইভ প্রগ্রেস আপডেট
            if index % 10 == 0 or index == total_lines:
                progress = (index / total_lines) * 100
                await update.message.reply_text(f"📊 অনুবাদ প্রক্রিয়া: {progress:.2f}% সম্পন্ন")

        translated_file_path = f"downloads/translated_{document.file_name}"
        with open(translated_file_path, "w", encoding="utf-8") as f:
            f.writelines(translated_lines)

        await update.message.reply_document(document=open(translated_file_path, "rb"), filename=f"translated_{document.file_name}", caption="✅ অনুবাদ সম্পন্ন!")

        # অস্থায়ী ফাইল মুছে ফেলা
        os.remove(file_path)
        os.remove(translated_file_path)

    except Exception as e:
        await update.message.reply_text(f"❌ ত্রুটি: {e}")
