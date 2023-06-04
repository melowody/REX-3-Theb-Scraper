import discord
from discord import ApplicationCommand
from discord.ext import tasks, commands
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


async def get_event(ctx: discord.AutocompleteContext):
    world = ctx.options['world']
    match world:
        case 'World 1':
            return ["None", "Vaporwave Crystal", "Inclemetite", "Spristium", "Candilium", "Lucidium", "Sentient Viscera", "Temporum", "Idolium", "Vitrilyx", "Magnetyx", "Cleopatrite", "Euclideum", "Combustal", "Quandrium", "Pastelorium", "Ω", "Inkonium", "Blazuine", "Illusory Bubblegram"]
        case 'Subworld 1':
            return ["None", "Sagittarius Quasar", "Legacy Flaeon", "Legacy Freon", "Legacy Poiseon", "Vaporwave Pulsar", "Legacy Codex", "Legacy Astatine", "Protoflare", "RGB Pulsar"]

def check_owner(ctx):
	return ctx.author.id in [797942648932794398, 190804082032640000, 609478516655915044]

@zetex_jr.command()
@commands.check(check_owner)
async def manual(_,
                 username: str,
                 ore: str,
                 special: discord.Option(str, choices=["None", "Ionized", "Spectral"]),
                 tier: discord.Option(str, choices=["Rare", "Master", "Surreal", "Mythic", "Exotic", "Transcendent", "Enigmatic", "Unfathomable", "Zenith"]),
                 rarity: int,
                 blocks: int,
                 pickaxe: discord.Option(str, choices=["Default", "Steel Sickle", "Miner's Mallet", "Stone Ravager", "Big Slammer", "Darkstone Pick", "Trinity Claymore", "57 Leaf Clover", "Poly Pickaxe", "Legacy Trinity Claymore", "Nostalgic Axe", "NilAxe"]),
                 world: discord.Option(str, choices=["World 1", "Subworld 1"]),
                 event: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_event))
                 ):
    ore_event = event_tracker.OreEvent()
    ore_event.event = event
    ore_event.pickaxe = pickaxe
    ore_event.blocks = blocks
    ore_event.special = event_tracker.SpecialType[special.upper()]
    ore_event.rarity = event_tracker.Rarity[tier.upper()]
    ore_event.ore = ore
    ore_event.base_rarity = rarity
    ore_event.username = username
    zetex_jr.et.queue.put(ore_event)
    await ctx.send("Ore successfully submitted :thumbsup:")
