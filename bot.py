import sys
import glob
import importlib
from pathlib import Path
import logging
import logging.config
import asyncio

# Pyrogram related
from pyrogram import Client, __version__, idle
from pyrogram.raw.all import layer
import pyrogram.utils

# aiohttp for health check
from aiohttp import web

# Project-specific imports
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script 
from Jisshu.bot import JisshuBot
from Jisshu.util.keepalive import ping_server
from Jisshu.bot.clients import initialize_clients

# Time
from datetime import date, datetime 
import pytz

# Telegram Bot (python-telegram-bot)
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from features.subtitle import subtr, handle_sub

# Configure Logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

# Force channel ID range
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

# Plugin Loader
ppath = "plugins/*.py"
files = glob.glob(ppath)

# Telegram Bot Token (python-telegram-bot)
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Telegram.Bot (telegram.ext) Runner
async def run_telegram_ext_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("subtr", subtr))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_sub))
    print("Telegram.ext Bot is running...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    return application

# Pyrogram-based Bot Runner
async def Jisshu_start():
    print('\nInitalizing Jisshu Filter Bot...')
    await JisshuBot.start()
    bot_info = await JisshuBot.get_me()
    JisshuBot.username = bot_info.username
    await initialize_clients()

    # Load all plugins
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("Imported Plugin => " + plugin_name)

    if ON_HEROKU:
        asyncio.create_task(ping_server())

    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    await Media.ensure_indexes()

    me = await JisshuBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    temp.B_LINK = me.mention
    JisshuBot.username = '@' + me.username

    logging.info(f"{me.first_name} | Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    logging.info(script.LOGO)

    # Send Restart Notifications
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    today = date.today()
    await JisshuBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(me.mention, today, time))
    await JisshuBot.send_message(chat_id=SUPPORT_GROUP, text=f"<b>{me.mention} restarted 🤖</b>")

    # Run healthcheck server
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    # Start telegram.ext bot (subtr)
    await run_telegram_ext_bot()

    await idle()

    # Notify Admins
    for admin in ADMINS:
        await JisshuBot.send_message(chat_id=admin, text=f"<b>{me.mention} bot restarted ✅</b>")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(Jisshu_start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
