import os

import websocket
from dotenv import load_dotenv

from core.discord.scraper.runners.heartbeat import Heartbeat
from core.discord.scraper.runners.scraper import RExTrackerScraper
from database.database import RExDBPool

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    load_dotenv()

    with RExDBPool().get_cursor() as cursor:
        cursor.execute(open(os.path.join(ROOT_DIR, "misc", "create.sql"), "r").read())

    from core.discord.bot.bot import RExDiscordBot

    socket = websocket.WebSocket()
    Heartbeat().ensure_socket(socket)
    Heartbeat().start()
    RExTrackerScraper().ensure_socket(socket)
    RExTrackerScraper().start()

    token = os.environ.get("BOT_TOKEN")
    if token:
        RExDiscordBot().run(token)

