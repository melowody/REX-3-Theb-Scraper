import asyncio
import os

from typing_extensions import TYPE_CHECKING

from core.discord.scraper.client import JsonSender


if TYPE_CHECKING:
    from core.discord.scraper.client import DiscordClient

class Heartbeat(JsonSender):

    async def handle_event(self, event: dict, client: "DiscordClient"):
        interval = event["d"]["heartbeat_interval"] / 1000.
        await client.send_queue.put({
            "op": 2,
            "d": {
                "token": os.environ.get("SCRAPER_TOKEN"),
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                }
            }
        })
        while True:
            await asyncio.sleep(interval * .75)
            await client.send_queue.put({
                "op": 1,
                "d": "null"
            })

    def should_handle(self, event: dict) -> bool:
        return event and "d" in event.keys() and isinstance(event["d"], dict) and "heartbeat_interval" in event["d"].keys()