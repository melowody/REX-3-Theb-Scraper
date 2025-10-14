import asyncio
import random
from typing import Type

import discord
from PIL import Image
from io import BytesIO

import requests
from discord import Intents
from discord.ext import commands, tasks

from core.discord.bot.cogs.add import RExDiscordAddCommand
from core.discord.bot.cogs.epinephrine import RExDiscordEpinephrineCommand
from core.discord.bot.cogs.force_register import RExDiscordForceRegisterCommand
from core.discord.bot.cogs.index import RExDiscordIndexCommand
from core.discord.bot.cogs.leaderboard import RExDiscordLeaderboardCommand
from core.discord.bot.cogs.manual import RExDiscordManualCommand
from core.discord.bot.cogs.player import RExDiscordPlayerCommand
from core.discord.bot.cogs.register import RExDiscordRegisterCommand
from core.discord.bot.cogs.setup import RExDiscordSetupCommand
from core.discord.bot.cogs.subscribe import RExDiscordSubscribeCommand
from core.discord.bot.cogs.sync import RExDiscordSyncCommand
from core.discord.bot.track_msg import RExDiscordTrackMessage
from core.discord.scraper.senders.scraper import RExScraper
from core.types.managers.player import RExPlayerManager, RExPlayer
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
        RExDiscordRegisterCommand,
        RExDiscordPlayerCommand,
        RExDiscordForceRegisterCommand
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
        self.change_avatar.start()

    async def setup_hook(self) -> None:
        for cog in self.my_cogs:
            await self.add_cog(cog(self))

    @tasks.loop(seconds=.01)
    async def send_events(self) -> None:
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
        id_endpoint = "https://users.roblox.com/v1/usernames/users"
        thumbnail_fmt = "https://thumbnails.roblox.com/v1/users/avatar?userIds={}&size=250x250&format=Png&isCircular=true"

        player: RExPlayer = random.choice(RExPlayerManager().get_all())
        username = player.player_name

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        player_id_req = requests.post(id_endpoint, headers=headers,
                                      json={"usernames": [username], "excludeBannedUsers": False})
        player_id = player_id_req.json()['data'][0]['id']

        thumbnail_req = requests.get(thumbnail_fmt.format(player_id), headers=headers)
        image_url = thumbnail_req.json()['data'][0]['imageUrl']

        image_req = requests.get(image_url)
        image = Image.open(BytesIO(image_req.content))

        width, height = image.size
        left, top, right, bottom = width / 4, 0, 3 * width / 4, height / 2
        cropped_image = image.crop((left, top, right, bottom))
        out_buf = BytesIO()
        cropped_image.save(out_buf, format='PNG')
        image_bytes = out_buf.getvalue()

        try:
            await self.user.edit(avatar=image_bytes, username=f"Gooberville Tracker")
        except discord.errors.HTTPException:
            return
