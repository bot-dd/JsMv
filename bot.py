import sys
import glob
import importlib
from pathlib import Path
import logging
import logging.config
from datetime import date, datetime
from typing import Union, Optional, AsyncGenerator

import asyncio
import pytz
import pyrogram.utils
from aiohttp import web
from pyrogram import Client, __version__, types, idle
from pyrogram.raw.all import layer

from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from plugins import web_server
from Jisshu.bot import JisshuBot
from Jisshu.util.keepalive import ping_server
from Jisshu.bot.clients import initialize_clients

from subtr import include_handlers  # <-- নতুন Import

# Logging Config
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

# Load all plugins
ppath = "plugins/*.py"
files = glob.glob(ppath)
JisshuBot.start()
loop = asyncio.get_event_loop()

# Set MIN_CHANNEL_ID
pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

async def Jisshu_start():
    print('\n')
    print('Initalizing Jisshu Filter Bot')
    bot_info = await JisshuBot.get_me()
    JisshuBot.username = bot_info.username
    await initialize_clients()

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
            print("Jisshu Filter Bot Imported => " + plugin_name)

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

    logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    logging.info(script.LOGO)

    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")

    await JisshuBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(me.mention, today, time))
    await JisshuBot.send_message(chat_id=SUPPORT_GROUP, text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>")

    # Setup web server
    app = await web_server()
    include_handlers(app)  # <-- এখানে include_handlers কল করা হয়েছে
    runner = web.AppRunner(app)
    await runner.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(runner, bind_address, PORT).start()

    await idle()

    for admin in ADMINS:
        await JisshuBot.send_message(chat_id=admin, text=f"<b>{me.mention} ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ ✅</b>")


if __name__ == '__main__':
    try:
        loop.run_until_complete(Jisshu_start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
