import typing

import discord
from PIL.SpiderImagePlugin import isInt
from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items, Pagination
from core.types.manager import NotInIndex
from core.types.managers.cave import RExCaveManager, RExCave
from core.types.managers.event import RExEventManager
from core.types.managers.layer import RExLayer
from core.types.managers.multiplier import RExMultiplier
from core.types.managers.ore import RExOreManager, RExOre
from core.types.managers.spawn import RExSpawn
from core.types.managers.variant import RExVariantManager, RExVariant


class OreIndexPaginator(Pagination[RExSpawn]):

    def __init__(self, ore: RExOre, spawns: list[RExSpawn], context: commands.Context | discord.Interaction):
        super().__init__(spawns, context)
        self.ore = ore
        self.cave_spawns = [i for i in spawns if i.cave_id]
        self.layer_spawns = [i for i in spawns if i.layer_id]
        self.create_buttons()

    def get_button_callback(self, index: int):
        async def open_cave(interaction: discord.Interaction):
            self.index = index
            await self.update(interaction)
        return open_cave

    def create_buttons(self):
        if len(self.items) <= 1:
            return
        if self.layer_spawns:
            layer_button = discord.ui.Button(label="Layer")
            layer_button.callback = self.get_button_callback(self.items.index(self.layer_spawns[0]))
            self.add_item(layer_button)
        for cave_spawn in self.cave_spawns:
            cave = cave_spawn.get_location()
            if isinstance(cave, NotInIndex):
                continue
            cave_button = discord.ui.Button(label=cave.cave_name)
            cave_button.callback = self.get_button_callback(self.items.index(cave_spawn))
            self.add_item(cave_button)


    def get_embed(self) -> discord.Embed:
        tier = self.ore.get_tier()
        out = discord.Embed(
            color=discord.Color.from_str("#1A1A1E") if isinstance(tier, NotInIndex) else tier.color,
            title=f"{self.ore.ore_name} ({"Unknown" if isinstance(tier, NotInIndex) else tier.tier_name})",
        )
        return out

    def get_page(self, spawn: RExSpawn, cave: bool = False) -> tuple[discord.Embed, typing.Optional[discord.File]]:
        embed = self.get_embed()
        location = spawn.get_location()
        if isinstance(location, RExLayer):
            embed.description = location.layer_name
        elif isinstance(location, RExCave):
            embed.description = location.cave_name
        embed.add_field(name="Base Rarity", value=f"{spawn.rarity:,}")

        tier = self.ore.get_tier()
        variants = RExVariantManager().get_all()
        mults: list[tuple[RExVariant, RExMultiplier]] = []
        if not isinstance(tier, NotInIndex):
            for variant in variants:
                mult = variant.get_multiplier(tier)
                mults.append((variant, mult))
                embed.add_field(name=f"{variant.variant_name} Rarity", value=f"{mult.multiplier * spawn.rarity:,}", inline=True)

        if not cave:
            event = RExEventManager().get_one(lambda x: x.ore_id == self.ore.ore_id, None)
            if not isinstance(event, NotInIndex):
                embed.add_field(name="Event Rarity", value=f"{event.ore_rarity:,}")
                for variant, mult in mults:
                    embed.add_field(name=f"Event {variant.variant_name} Rarity", value=f"{event.ore_rarity * mult.multiplier:,}", inline=True)

            layers = []
            for layer_spawn in self.layer_spawns:
                layer = layer_spawn.get_location()
                if not isinstance(layer, RExLayer):
                    continue
                layers.append(layer.layer_name)
            embed.add_field(name="Layers", value=", ".join(layers))
        else:
            rarity = spawn.adjusted_rarity
            if not isinstance(rarity, NotInIndex):
                embed.add_field(name="Adjusted Rarity", value=f"{rarity:,}")
                for variant, mult in mults:
                    embed.add_field(name=f"Adjusted {variant.variant_name} Rarity", value=f"{rarity * mult.multiplier:,}", inline=True)


        return embed, None

    def to_page(self, item: RExSpawn) -> tuple[discord.Embed, typing.Optional[discord.File]]:
        if item in self.layer_spawns:
            return self.get_page(item)
        return self.get_page(item, cave=True)

    def set_button_properties(self):
        pass


class RExDiscordIndexCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="index", description="Get information about an item in the Index")  # type: ignore
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def index(self, ctx):
        return

    @index.command(name="ore", description="Get information about an Ore")  # type: ignore
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name,
                      secondary=lambda x: x.alt_name if x.alt_name else "")
    )
    async def ore(self, ctx: commands.Context, ore: str):
        if isinstance(rex_ore := RExOreManager().get_one(lambda x: x.ore_id == ore, None), NotInIndex):
            await ctx.reply("You must enter a valid Ore!", ephemeral=True)
            return

        spawns = rex_ore.get_spawns()
        layer_spawns = [i for i in spawns if i.layer_id]
        if layer_spawns:
            worlds = []
            for layer_spawn in layer_spawns:
                loc = layer_spawn.get_location()
                if isinstance(loc, NotInIndex):
                    continue
                world = loc.get_world()
                if world in worlds or isinstance(world, NotInIndex):
                    continue
                worlds.append(world)
                cave = RExCaveManager().get_one(lambda x: x.cave_id.startswith("gilded") and x.world_id == world.world_id, None)
                if not isinstance(cave, NotInIndex):
                    spawns.append(RExSpawn(
                        rex_ore.ore_id,
                        None,
                        cave.cave_id,
                        round(layer_spawn.rarity * 2.5)
                    ))

        await OreIndexPaginator(rex_ore, spawns, ctx).open()