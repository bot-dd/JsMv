from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import CHANNELS, MOVIE_UPDATE_CHANNEL, ADMINS , LOG_CHANNEL
from database.ia_filterdb import save_file, unpack_new_file_id
from utils import get_poster, temp
import re
from database.users_chats_db import db
import random

processed_movies = set()
media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    bot_id = bot.me.id
    media = getattr(message, message.media.value, None)
    if media.mime_type in ['video/mp4', 'video/x-matroska']: 
        media.file_type = message.media.value
        media.caption = message.caption
        success_sts = await save_file(media)
        if success_sts == 'suc' and await db.get_send_movie_update_status(bot_id):
            file_id, file_ref = unpack_new_file_id(media.file_id)
            await send_movie_updates(bot, file_name=media.file_name, caption=media.caption, file_id=file_id)

async def get_imdb(file_name):
    imdb_file_name = await movie_name_format(file_name)
    imdb = await get_poster(imdb_file_name)
    if imdb:
        return imdb.get('poster')
    return None

async def movie_name_format(file_name):
    # @, [], {}, () এগুলোর মধ্যে থাকা টেক্সট বাদ দেওয়া হচ্ছে
    file_name = re.sub(r'@\S+|\[.*?\]|\(.*?\)|\{.*?\}', '', file_name)
    file_name = re.sub(r'http\S+', '', file_name).replace('_', ' ').replace('.', ' ')
    file_name = re.sub(r'[^a-zA-Z0-9\s]', '', file_name).strip()
    return file_name

async def check_qualities(text, qualities: list):
    quality = []
    for q in qualities:
        if q.lower() in text.lower():
            quality.append(f"#{q}")
    return ", ".join(quality) if quality else "#HDRip"

async def send_movie_updates(bot, file_name, caption, file_id):
    try:
        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None      
        pattern = r"(?i)(?:s|season)0*(\d{1,2})"
        season = re.search(pattern, caption) or re.search(pattern, file_name)
        
        if year:
            file_name = file_name[:file_name.find(year) + 4]      
        elif season:
            file_name = file_name[:file_name.find(season.group(1)) + 1]

        qualities = ["ORG", "HDCAM", "HQ", "HDRip", "CAMRip", "WEB-DL", "HDTC", "DVDscr", "HDTS"]
        quality = await check_qualities(caption, qualities)

        nb_languages = ["Hindi", "Bengali", "English", "Marathi", "Tamil", "Telugu", "Malayalam", 
                        "Kannada", "Punjabi", "Gujarati", "Korean", "Japanese", "Bhojpuri", "Dual", "Multi"]
        language = ", ".join([f"#{lang}" for lang in nb_languages if lang.lower() in caption.lower()]) or "#NotIdea"

        movie_name = await movie_name_format(file_name)
        if movie_name in processed_movies:
            return 
        processed_movies.add(movie_name)    

        poster_url = await get_imdb(movie_name)
        no_poster_images = [
            "https://envs.sh/xF.jpg",
            "https://envs.sh/xQ.jpg",
            "https://envs.sh/xt.jpg"
        ]
        selected_poster = poster_url or random.choice(no_poster_images)

        caption_message = f"#New_File_Added ✅\n\n● ꜰɪʟᴇ_ɴᴀᴍᴇ: <code>{movie_name}</code>\n\n● ʟᴀɴɢᴜᴀɢᴇ: {language}\n\n● Qᴜᴀʟɪᴛʏ: {quality}"
        search_movie = movie_name.replace(" ", '-')
        movie_update_channel = await db.movies_update_channel_id()

        btn = [[
            InlineKeyboardButton('📂 Get File 📂', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
        ], [
            InlineKeyboardButton('♻️ How To Download ♻️', url='https://t.me/RM_Movi')
        ]]
        reply_markup = InlineKeyboardMarkup(btn)

        await bot.send_photo(movie_update_channel if movie_update_channel else MOVIE_UPDATE_CHANNEL, 
                             photo=selected_poster, caption=caption_message, reply_markup=reply_markup)

    except Exception as e:
        print('Failed to send movie update. Error - ', e)
        await bot.send_message(LOG_CHANNEL, f'Failed to send movie update. Error - {e}')
