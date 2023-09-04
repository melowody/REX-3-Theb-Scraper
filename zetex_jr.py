import discord
from discord import ApplicationCommand
from discord.ext import tasks, commands
import time
import websocket
import os
import asyncio
import heartbeat
import event_tracker
import item_manager
import asyncio
import json


class TrackerBot(discord.Bot):

    def add_error(self, err):
        self.error_queue.append(err)

    async def register_command(self, command: ApplicationCommand, force: bool = True,
                               guild_ids: list[int] | None = None) -> None:
        pass

    def __init__(self):
        super().__init__(command_prefix="$")
        self.et = None
        self.hb = None
        self.test_channel = None
        self.error_queue = []

    async def on_ready(self):
        print("zetex jr. ready")
        await self.start_tracking()
        channel = self.get_channel(1147287507608805406)
        await channel.send("restarted!")

    async def start_tracking(self):
        ws = websocket.WebSocket()
        self.hb = heartbeat.HeartBeat(ws)
        self.et = event_tracker.EventTracker(ws)

        self.hb.start()
        task_et = asyncio.create_task(self.et.start())

        await task_et
        self.send_event.start()
        self.send_error.start()

    @tasks.loop(seconds=1.0)
    async def send_event(self):
        if self.et.queue.qsize() != 0:
            event = self.et.queue.get()
            for event_type in event.get_event_types():
                self.et.tracks += 1
                await self.get_channel(event_type.value).send(
                    event.format(event_type))

    @tasks.loop(seconds=1.0)
    async def send_error(self):
        if len(self.error_queue) != 0:
            err = self.error_queue.pop()
            await self.get_channel(item_manager.get_channel("ERROR_CHANNEL")).send(
                f"new error just dropped :bangbang: :fire: ```{err}```"
            )
            os.system("cd ~ ; ./restart.sh")


tracker_bot = TrackerBot()


async def get_event(ctx: discord.AutocompleteContext):
    world = ctx.options['world']
    match world:
        case 'World 1':
            return ["None", "Vaporwave Crystal", "Inclemetite", "Spristium", "Candilium", "Lucidium",
                    "Sentient Viscera", "Temporum", "Idolium", "Vitrilyx", "Magnetyx", "Cleopatrite", "Euclideum",
                    "Combustal", "Quandrium", "Pastelorium", "Ω", "Inkonium", "Blazuine", "Illusory Bubblegram"]
        case 'Subworld 1':
            return ["None", "Sagittarius Quasar", "Legacy Flaeon", "Legacy Freon", "Legacy Poiseon", "Vaporwave Pulsar",
                    "Legacy Codex", "Legacy Astatine", "Protoflare", "RGB Pulsar"]
        case 'World 2':
            return ["None", "Galactic Rupture", "Heart of the Frosted", "Atomium", "Coronal Flare", "Neutronium",
                    "Estrela", "Circeterra", "NOO S-Sing. T1", "Spiritian", "Vitriol", "Catastormite", "Plasmonium",
                    "Frostranium", "Obliveracy Endmost", "Acrimony"]


def check_owner(ctx):
    return ctx.author.id in [797942648932794398, 190804082032640000, 302920327699103744]


@tracker_bot.command()
@commands.check(check_owner)
async def manual(ctx,
                 username: str,
                 ore: str,
                 special: discord.Option(str, choices=["None", "Ionized", "Spectral"]),
                 tier: discord.Option(str, choices=[e.capitalize() for e in event_tracker.Rarity.__members__]),
                 rarity: int,
                 blocks: int,
                 pickaxe: discord.Option(str, choices=["Default", "Steel Sickle", "Miner's Mallet", "Stone Ravager",
                                                       "Big Slammer", "Darkstone Pick", "Trinity Claymore",
                                                       "57 Leaf Clover", "Poly Pickaxe", "Legacy Trinity Claymore",
                                                       "Nostalgic Axe", "NilAxe", "Christmas Crusher",
                                                       "Permafrost Pick", "Poison Pick", "Electraver",
                                                       "Dimensional Scythe", "Celestial Smasher", "Moon Scepter",
                                                       "Soul Scythe", "Prism of Chaos"]),
                 world: discord.Option(str, choices=["World 1", "Subworld 1", "World 2"]),
                 event: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_event))
                 ):
    ore_event = event_tracker.OreEvent()
    ore_event.event = event
    ore_event.pickaxe = pickaxe
    ore_event.blocks = blocks
    ore_event.special = event_tracker.SpecialType[special.upper()]
    ore_event.rarity = event_tracker.Rarity[tier.upper()]
    ore_event.ore = ore
    ore_event.base_rarity = '{:,}'.format(rarity)
    ore_event.username = username
    tracker_bot.et.queue.put(ore_event)
    await ctx.respond("manual ore successfully submitted :3", ephemeral=True)


@tracker_bot.command()
@commands.check(check_owner)
async def restart(ctx):
    await ctx.respond("Restarting!")
    os.system("/root/restart.sh")

def format_num(number):
    return str('{:,}'.format(int(number)))

@tracker_bot.command()
async def adjusted(ctx, ore: str, variant: discord.Option(str, choices=["Normal", "Ionized", "Spectral"])):
    file = open("cave_ores.json")
    cave_ores = json.load(file)
    message_contents = "# " + variant + " " + ore
    if variant == "Normal": message_contents = message_contents.replace("Normal ", "")
    adjusted_found = False
    for cave_type in cave_ores:
        for i in cave_ores[cave_type]["ores"]:
            if ore.lower() == i.lower():
                adjusted_found = True
                message_contents = message_contents.replace(ore, i)
                match variant:
                    case "Normal":   variantnum = 0
                    case "Ionized":  variantnum = 1
                    case "Spectral": variantnum = 2
                base_rarity = cave_ores[cave_type]["ores"][i][variantnum]
                cave_rarity = cave_ores[cave_type]["rarity"]
                message_contents += f"\n## {cave_type} Cave (1 in " + format_num(cave_rarity) + ")"
                message_contents += "\n**Base Rarity**: 1 in " + format_num(base_rarity)
                message_contents += "\n**Adjusted Rarity**: 1 in " + format_num(base_rarity * cave_rarity * 1.88)
    if not adjusted_found:
        message_contents += "\nNo cave type contains this ore.\n(/adjusted does not currently support Gilded cave ores that aren't HHQ, sorry!)"
        if ore in ["π", "Ω", "Legacy Ω", "Σ", "Legacy Σ"]:
            message_contents += "\n(P.S. you can just type 'Pi', 'Sigma', 'Omega' etc.)"
        if ore == "Aurora Polaris":
            message_contents = "nice try"
    await ctx.respond(message_contents)

def send_error(err):
    tracker_bot.add_error(err)
