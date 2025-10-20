"""
Loads the required data, boots up the DB connection, and starts the bots
"""

import os

from dotenv import load_dotenv

from core.database import RExDBPool
from core.discord.scraper.client import DiscordClient

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    # Load the .env file
    load_dotenv()

    # Initialize the database
    with RExDBPool().get_cursor() as cursor:
        with open(os.path.join(ROOT_DIR, "data", "create.sql"), "r", encoding="utf8") as f:
            cursor.execute(f.read())

    # Start the bots
    from core.discord.bot.bot import RExDiscordBot

    DiscordClient().start()

    token = os.environ.get("BOT_TOKEN")
    if token:
        RExDiscordBot().run(token)
