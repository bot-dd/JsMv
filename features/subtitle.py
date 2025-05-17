# features/subtitle.py

import os
import re
from deep_translator import GoogleTranslator
from telegram import Update, Document
from telegram.ext import ContextTypes

user_states = {}

def get_sub_format(filename):
    if filename.endswith('.srt'):
        return 'srt'
    elif filename.endswith('.vtt'):
        return 'vtt'
    elif filename.endswith('.ass'):
        return 'ass'
    else:
        return None

async def subtr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📥 Please send your subtitle file (.srt, .vtt, .ass)")
    user_states[update.effective_user.id] = "awaiting_sub"

async def handle_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_states.get(user_id) != "awaiting_sub":
        return

    document: Document = update.message.document
    sub_format = get_sub_format(document.file_name)

    if not sub_format:
        await update.message.reply_text("⚠️ Only .srt, .vtt or .ass files are supported.")
        return

    msg = await update.message.reply_text("⏳ Downloading file...")

    file = await document.get_file()
    input_path = f"{user_id}_{document.file_name}"
    output_path = f"{user_id}_translated.{sub_format}"
    await file.download_to_drive(input_path)

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        translated_lines = []
        translator = GoogleTranslator(source='auto', target='bn')

        for idx, line in enumerate(lines):
            if sub_format == 'srt':
                is_dialogue = not line.strip().isdigit() and '-->' not in line and line.strip()
            elif sub_format == 'vtt':
                is_dialogue = '-->' not in line and re.match(r'^\d\d:\d\d', line.strip()) is None and line.strip()
            elif sub_format == 'ass':
                is_dialogue = line.startswith("Dialogue:")

            if is_dialogue:
                try:
                    if sub_format == 'ass':
                        parts = line.split(",", 9)
                        if len(parts) >= 10:
                            original_text = parts[9].strip()
                            translated_text = translator.translate(original_text)
                            parts[9] = translated_text
                            translated_lines.append(",".join(parts) + '\n')
                        else:
                            translated_lines.append(line)
                    else:
                        translated = translator.translate(line.strip())
                        translated_lines.append(translated + '\n')
                except:
                    translated_lines.append(line)
            else:
                translated_lines.append(line)

            if idx % 10 == 0:
                await msg.edit_text(f"⚙️ Translating... {idx}/{len(lines)} lines")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(translated_lines)

        await msg.edit_text("✅ Done! Sending translated subtitle...")
        await update.message.reply_document(document=open(output_path, 'rb'), filename=os.path.basename(output_path))

    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        user_states.pop(user_id, None)
