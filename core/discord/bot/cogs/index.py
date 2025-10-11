from typing import Any

from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items, get_string
from core.types.manager import NotInIndex
from core.types.managers.cave import RExCaveManager, RExCave
from core.types.managers.event import RExEventManager
from core.types.managers.layer import RExLayerManager, RExLayer
from core.types.managers.multiplier import RExMultiplier
from core.types.managers.ore import RExOreManager, RExOre
from core.types.managers.spawn import RExSpawnManager
from core.types.managers.tier import RExTierManager
from core.types.managers.variant import RExVariantManager
from core.types.managers.world import RExWorldManager, RExWorld


class RExDiscordIndexCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="index", description="Get information about items in the game") # type: ignore[arg-type]
    async def index(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply("You must specify what you want information about!", ephemeral=True)

    @index.command(name="world", description="Get information about a world in REx") # type: ignore[arg-type]
    @app_commands.autocomplete(
        world_id=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    async def world(self, ctx: commands.Context, world_id: str):
        world = RExWorldManager().get_one(lambda x: x.world_id == world_id, world_id)
        if isinstance(world, NotInIndex):
            await ctx.reply(f"World {world_id} not found", ephemeral=True)
            return
        await ctx.reply(f"## {world.world_name}\n{world.world_desc}", ephemeral=True)

    @index.command(name="ore", description="Get information about an ore in REx") # type: ignore[arg-type]
    @app_commands.autocomplete(
        ore_id=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name, secondary=lambda x: "" if (alt := x.alt_name) is None else alt)
    )
    async def ore(self, ctx: commands.Context, ore_id: str):
        ore = RExOreManager().get_one(lambda x: x.ore_id == ore_id, ore_id)
        if isinstance(ore, NotInIndex):
            await ctx.reply(f"Ore {ore_id} not found", ephemeral=True)
            return

        tier = RExTierManager().get_one(lambda x: x.tier_id == ore.tier_id, ore.tier_id)
        tier_str = f" ({get_string(tier, lambda x: x.tier_name)})"

        spawns = RExSpawnManager().get(lambda x: x.ore_id == ore.ore_id)
        layer_spawns = [i for i in spawns if i.layer_id]
        rarity_msg = "**Normal:** NOT IN INDEX"
        if len(layer_spawns) > 0 and not isinstance(tier, NotInIndex):
            base_rarity = layer_spawns[0].rarity
            variants: list[tuple[str, Any]] = [("Normal", base_rarity)]
            for variant in RExVariantManager().get_all():
                multiplier = variant.get_multiplier(tier)
                if isinstance(multiplier, RExMultiplier):
                    variants.append((variant.variant_name.title(), multiplier.multiplier * base_rarity))
                else:
                    variants.append((variant.variant_name.title(), "NOT IN INDEX"))
            rarity_msg = "\n".join(f"**{i[0]}:** {i[1]}" for i in variants)

        locations = []
        for spawn in spawns:
            if loc := spawn.get_location():
                if isinstance(loc, RExLayer):
                    locations.append(loc.layer_name)
                elif isinstance(loc, RExCave):
                    locations.append(loc.cave_name)

        event = RExEventManager().get_one(lambda x: x.ore_id == ore.ore_id, ore.ore_id)
        if isinstance(event, NotInIndex):
            event_msg = f"This ore does not have an event"
        else:
            event_msg = f'Event Rarity: 1 in {event.ore_rarity:,}'

        await ctx.reply(f"## {ore.ore_name}{tier_str}\n{rarity_msg}\n\nLocation{'' if len(spawns) == 1 else 's'}: **{'NOT IN INDEX' if len(locations) == 0 else ', '.join(locations)}**\n{event_msg}")

    @index.command(name="cave", description="Get information about a cave") # type: ignore[arg-type]
    @app_commands.autocomplete(
        cave_id=get_items(RExCaveManager().get_all(), lambda x: x.cave_id, lambda x: x.cave_name)
    )
    async def cave(self, ctx: commands.Context, cave_id: str):
        cave = RExCaveManager().get_one(lambda x: x.cave_id == cave_id, cave_id)
        if isinstance(cave, NotInIndex):
            await ctx.reply(f"Cave {cave_id} not found", ephemeral=True)
            return

        ore_msg = get_string(cave.get_ore(), lambda x: x.ore_name)
        world_msg = get_string(cave.get_world(), lambda x: x.world_name)

        await ctx.reply(f"## {cave.cave_name}\n**Cave Wall:** {ore_msg}\n**Rarity:** {cave.cave_rarity}\n**World:** {world_msg}")

    @index.command(name="layer", description="Get information about a layer") # type: ignore[arg-type]
    @app_commands.autocomplete(
        layer_id=get_items(RExLayerManager().get_all(), lambda x: x.layer_id, lambda x: x.layer_name)
    )
    async def layer(self, ctx: commands.Context, layer_id: str):
        layer = RExLayerManager().get_one(lambda x: x.layer_id == layer_id, layer_id)
        if isinstance(layer, NotInIndex):
            await ctx.reply(f"Layer {layer_id} not found", ephemeral=True)
            return

        ore_msg = get_string(layer.get_ore(), lambda x: x.ore_name)
        world_msg = get_string(layer.get_world(), lambda x: x.world_name)

        await ctx.reply(f"## {layer.layer_name}\n**Layer Ore:** {ore_msg}\n**Depth:** {layer.min_depth} - {layer.max_depth}\n**World:** {world_msg}")