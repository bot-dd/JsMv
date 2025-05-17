from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
)
import os
from langdetect import detect
import webvtt
import pysubs2

user_files = {}

# Mock translate function (Replace with your API later)
def translate(text, dest='en'):
    return f"[{dest}] {text}"

LANGUAGES = {
    "বাংলা": "bn",
    "ইংরেজি": "en",
    "হিন্দি": "hi",
    "আরবি": "ar",
    "তামিল": "ta",
    "তেলুগু": "te",
    "জাপানি": "ja",
    "চাইনিজ": "zh-cn",
    "ফরাসি": "fr",
    "স্প্যানিশ": "es"
}

async def subtr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "অনুগ্রহ করে অনুবাদ করতে একটি সাবটাইটেল ফাইল পাঠান।\nসমর্থিত ফরম্যাট: `.srt`, `.vtt`, `.ass`"
    )

async def handle_subtitle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    user_id = update.message.from_user.id
    ext = os.path.splitext(doc.file_name)[-1].lower()

    if ext not in [".srt", ".vtt", ".ass"]:
        await update.message.reply_text("❌ `.srt`, `.vtt`, `.ass` ফাইলই শুধু সমর্থিত।")
        return

    user_files[user_id] = {"file_id": doc.file_id, "file_name": doc.file_name, "ext": ext}
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"subtr_lang_{code}")]
        for name, code in LANGUAGES.items()
    ]
    await update.message.reply_text(
        "অনুবাদ করার ভাষা নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    lang_code = query.data.split("_")[-1]
    if user_id not in user_files:
        await query.edit_message_text("❌ অনুগ্রহ করে আগে একটি ফাইল পাঠান।")
        return

    await query.edit_message_text("ফাইল ডাউনলোড হচ্ছে...")

    file_data = user_files[user_id]
    file = await context.bot.get_file(file_data["file_id"])
    input_path = f"downloads/{user_id}_{file_data['file_name']}"
    output_path = f"downloads/{user_id}_translated_{lang_code}{file_data['ext']}"
    await file.download_to_drive(input_path)

    progress = await context.bot.send_message(query.message.chat_id, text="⏳ অনুবাদ শুরু হয়েছে...")

    try:
        if file_data["ext"] == ".srt":
            with open(input_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            translated = []
            for i, line in enumerate(lines):
                if "-->" not in line and not line.strip().isdigit() and line.strip():
                    line = translate(line, dest=lang_code)
                translated.append(line)
                if i % 10 == 0:
                    percent = int((i+1) / len(lines) * 100)
                    await progress.edit_text(f"{percent}% অনুবাদ সম্পন্ন...")

            with open(output_path, "w", encoding="utf-8") as f:
                f.writelines(translated)

        elif file_data["ext"] == ".vtt":
            vtt = webvtt.read(input_path)
            for i, caption in enumerate(vtt):
                caption.text = translate(caption.text, dest=lang_code)
                if i % 2 == 0:
                    percent = int((i+1) / len(vtt) * 100)
                    await progress.edit_text(f"{percent}% অনুবাদ সম্পন্ন...")
            vtt.save(output_path)

        elif file_data["ext"] == ".ass":
            subs = pysubs2.load(input_path)
            for i, line in enumerate(subs):
                line.text = translate(line.text, dest=lang_code)
                if i % 2 == 0:
                    percent = int((i+1) / len(subs) * 100)
                    await progress.edit_text(f"{percent}% অনুবাদ সম্পন্ন...")
            subs.save(output_path)

        await progress.edit_text("✅ অনুবাদ সম্পন্ন। অনুবাদিত ফাইল পাঠানো হচ্ছে...")

        await context.bot.send_document(
            query.message.chat_id,
            document=open(output_path, "rb"),
            filename=os.path.basename(output_path),
            caption=(
                "**অনুবাদ সফল!**\n\n"
                "**Created by [Rahat](https://t.me/RahatMx)**\n"
                "**Powered by [RM Movie Flix](https://t.me/RM_Movie_Flix)**"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Done", callback_data="subtr_done")]
            ])
        )

    except Exception as e:
        await progress.edit_text(f"❌ অনুবাদে ত্রুটি: {e}")

    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)
        user_files.pop(user_id, None)

async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("ধন্যবাদ!")

# Handler Registration Wrapper
def include_handlers(app):
    app.add_handler(CommandHandler("subtr", subtr_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_subtitle_file))
    app.add_handler(CallbackQueryHandler(handle_language_selection, pattern="subtr_lang_"))
    app.add_handler(CallbackQueryHandler(done_callback, pattern="subtr_done"))
