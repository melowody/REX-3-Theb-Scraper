import discord
from discord import ApplicationCommand
from discord.ext import tasks, commands
import time
import websocket
import os
import asyncio
import heartbeat
import event_tracker

class TrackerBot(discord.Bot):

    async def register_command(self, command: ApplicationCommand, force: bool = True,
                               guild_ids: list[int] | None = None) -> None:
        pass

    def __init__(self):
        super().__init__(command_prefix="$")
        self.et = None
        self.hb = None
        self.test_channel = None

    async def on_ready(self):
        print("zetex jr. ready")
        await self.start_tracking()
        
    async def start_tracking(self):
        ws = websocket.WebSocket()
        self.hb = heartbeat.HeartBeat(ws)
        self.et = event_tracker.EventTracker(ws)

        self.hb.start()
        task_et = asyncio.create_task(self.et.start())

        loggingchannel = self.get_channel(1147287507608805406)
        await loggingchannel.send("restarted!")
        
        await task_et
        self.send_event.start()

    @tasks.loop(seconds=1.0)
    async def send_event(self):
        if self.et.queue.qsize() != 0:
            event = self.et.queue.get()
            for event_type in event.get_event_types():
                self.et.tracks += 1
                await self.get_channel(event_type.value).send(
                    event.format(event_type))
        #print(error_present)
        #print(error_data)
        #print(error_restart)
        #if error_present:
            #channel = self.get_channel(1076318101769039972)
            #await channel.send(f"new error just dropped\n``` {error_data} ```")
            #if do_restart:
                #os.system("cd ~ ; ./restart.sh")

tracker_bot = TrackerBot()


async def get_event(ctx: discord.AutocompleteContext):
    world = ctx.options['world']
    match world:
        case 'World 1':
            return ["None", "Vaporwave Crystal", "Inclemetite", "Spristium", "Candilium", "Lucidium", "Sentient Viscera", "Temporum", "Idolium", "Vitrilyx", "Magnetyx", "Cleopatrite", "Euclideum", "Combustal", "Quandrium", "Pastelorium", "Ω", "Inkonium", "Blazuine", "Illusory Bubblegram"]
        case 'Subworld 1':
            return ["None", "Sagittarius Quasar", "Legacy Flaeon", "Legacy Freon", "Legacy Poiseon", "Vaporwave Pulsar", "Legacy Codex", "Legacy Astatine", "Protoflare", "RGB Pulsar"]
        case 'World 2':
            return ["None", "Galactic Rupture", "Heart of the Frosted", "Atomium", "Coronal Flare", "Neutronium", "Estrela", "Circeterra", "NOO S-Sing. T1", "Spiritian", "Vitriol", "Catastormite", "Plasmonium", "Frostranium", "Obliveracy Endmost", "Acrimony"]

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
                 pickaxe: discord.Option(str, choices=["Default", "Steel Sickle", "Miner's Mallet", "Stone Ravager", "Big Slammer", "Darkstone Pick", "Trinity Claymore", "57 Leaf Clover", "Poly Pickaxe", "Legacy Trinity Claymore", "Nostalgic Axe", "NilAxe", "Christmas Crusher", "Permafrost Pick", "Poison Pick", "Electraver", "Dimensional Scythe", "Celestial Smasher", "Moon Scepter", "Soul Scythe", "Prism of Chaos"]),
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
