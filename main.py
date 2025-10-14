import os

from dotenv import load_dotenv

from core.database import RExDBPool
from core.discord.scraper.client import DiscordClient

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    load_dotenv()

    with RExDBPool().get_cursor() as cursor:
        cursor.execute(open(os.path.join(ROOT_DIR, "data", "create.sql"), "r").read())

    from core.discord.bot.bot import RExDiscordBot

    DiscordClient().start()

    token = os.environ.get("BOT_TOKEN")
    if token:
        RExDiscordBot().run(token)

