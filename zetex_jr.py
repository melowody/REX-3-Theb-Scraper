import discord
from discord import ApplicationCommand
from discord.ext import tasks
import websocket
import os

import heartbeat
import event_tracker


class ZetexJr(discord.Bot):

    async def register_command(self, command: ApplicationCommand, force: bool = True,
                               guild_ids: list[int] | None = None) -> None:
        pass

    def __init__(self):
        super().__init__(command_prefix="$")
        self.et = None
        self.hb = None
        self.test_channel = None

    async def on_ready(self):
        print("Zetex Jr ready for action!")
        await self.get_channels()
        await self.start_tracking()
        channel = self.get_channel(1061709849391534082)
        await channel.send("<:sober:1077353673052672120>")

    async def get_channels(self):
        self.test_channel = self.get_channel(1075585315483439166)

    async def start_tracking(self):
        ws = websocket.WebSocket()
        self.hb = heartbeat.HeartBeat(ws)
        self.et = event_tracker.EventTracker(ws)

        self.hb.start()
        self.et.start()
        self.send_event.start()

    @tasks.loop(seconds=1.0)
    async def send_event(self):
        if self.et.queue.qsize() != 0:
            event = self.et.queue.get()
            for event_type in event.get_event_types():
                self.et.tracks += 1
                await self.get_channel(event_type.value).send(
                    event.format(event_type))


zetex_jr = ZetexJr()


@zetex_jr.command()
async def hefuckingdied(ctx):
    await ctx.respond("Restarting!")
    os.system("/root/restart.sh")
