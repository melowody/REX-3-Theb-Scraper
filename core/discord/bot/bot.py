import asyncio
from typing import Type

from discord import Intents
from discord.ext import commands, tasks

from core.discord.bot.cogs.add import RExDiscordAddCommand
from core.discord.bot.cogs.epinephrine import RExDiscordEpinephrineCommand
from core.discord.bot.cogs.index import RExDiscordIndexCommand
from core.discord.bot.cogs.leaderboard import RExDiscordLeaderboardCommand
from core.discord.bot.cogs.manual import RExDiscordManualCommand
from core.discord.bot.cogs.register import RExDiscordRegisterCommand
from core.discord.bot.cogs.setup import RExDiscordSetupCommand
from core.discord.bot.cogs.subscribe import RExDiscordSubscribeCommand
from core.discord.bot.cogs.sync import RExDiscordSyncCommand
from core.discord.bot.track_msg import RExDiscordTrackMessage
from core.discord.scraper.runners.scraper import RExTrackerScraper
from core.types.meta import SingletonMeta


class RExDiscordBot(commands.Bot, metaclass=SingletonMeta):
    my_cogs: list[Type[commands.Cog]] = [
        RExDiscordAddCommand,
        RExDiscordEpinephrineCommand,
        RExDiscordIndexCommand,
        RExDiscordLeaderboardCommand,
        RExDiscordManualCommand,
        RExDiscordSetupCommand,
        RExDiscordSubscribeCommand,
        RExDiscordSyncCommand,
        RExDiscordRegisterCommand
    ]

    def __init__(self):
        super().__init__(command_prefix="rex!", intents=Intents.all())
        self.owner_ids = [
            190804082032640000,
            252243543555309586,
            # 227916041567731722,
            # 797942648932794398
        ]

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        self.send_events.start()

    async def setup_hook(self) -> None:
        for cog in self.my_cogs:
            await self.add_cog(cog(self))

    @tasks.loop(seconds=.01)
    async def send_events(self) -> None:
        queue = RExTrackerScraper().queue
        while True:
            try:
                track = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            await RExDiscordTrackMessage(self, track).send_messages()
            queue.task_done()