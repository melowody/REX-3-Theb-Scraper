"""
Implementation for handling reconnect events sent by Discord.
"""

import asyncio
from typing import TYPE_CHECKING

from core.discord.scraper.client import JsonSender


if TYPE_CHECKING:
    from core.discord.scraper.client import DiscordClient

class Reconnect(JsonSender):

    def should_handle(self, event: dict) -> bool:
        return event.get("op") == 7

    async def handle_event(self, event: dict, client: "DiscordClient"):
        for task in client.tasks:
            task.cancel()

        await client.socket.close(code=1000)
        await asyncio.sleep(1)
        client.loop.create_task(client.connect_and_loop())