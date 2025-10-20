"""
Implementation of the main Discord Bot.
"""

import asyncio
import random
from typing import Type

import discord
from discord import Intents
from discord.ext import commands, tasks

from core.discord.bot.cogs.epinephrine import RExDiscordEpinephrineCommand
from core.discord.bot.cogs.index import RExDiscordIndexCommand
from core.discord.bot.cogs.leaderboard import RExDiscordLeaderboardCommand
from core.discord.bot.cogs.manual import RExDiscordManualCommand
from core.discord.bot.cogs.player import RExDiscordPlayerCommand
from core.discord.bot.cogs.remove import RExDiscordRemoveCommand
from core.discord.bot.cogs.set import RExDiscordSetCommand
from core.discord.bot.cogs.sync import RExDiscordSyncCommand
from core.discord.bot.track_msg import RExDiscordTrackMessage
from core.discord.bot.util import get_avatar
from core.discord.scraper.senders.scraper import RExScraper
from core.types.managers.player import RExPlayerManager, RExPlayer
from core.types.meta import SingletonMeta


class RExDiscordBot(commands.Bot, metaclass=SingletonMeta):
    """
    The main Discord Bot people will be interacting with.
    """
    my_cogs: list[Type[commands.Cog]] = [
        RExDiscordSetCommand,
        RExDiscordRemoveCommand,
        RExDiscordIndexCommand,
        RExDiscordSyncCommand,
        RExDiscordEpinephrineCommand,
        RExDiscordPlayerCommand,
        RExDiscordManualCommand,
        RExDiscordLeaderboardCommand
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
        # self.change_avatar.start()

    async def setup_hook(self) -> None:
        for cog in self.my_cogs:
            await self.add_cog(cog(self))

    @tasks.loop(seconds=.01)
    async def send_events(self) -> None:
        """
        Sends out all the tracker messages
        """
        queue = RExScraper().track_queue
        while True:
            try:
                track = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            await RExDiscordTrackMessage(self, track).send_messages()
            queue.task_done()

    @tasks.loop(minutes=30)
    async def change_avatar(self) -> None:
        """
        Changes the bot's avatar to a random player's
        """
        player: RExPlayer = random.choice(RExPlayerManager().get_all())

        avatar = get_avatar(player)

        try:
            if self.user:
                await self.user.edit(avatar=avatar.getvalue(), username="Gooberville Tracker")
        except discord.errors.HTTPException:
            return
