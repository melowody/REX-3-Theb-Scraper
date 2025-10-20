import typing

from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items
from core.types.manager import NotInIndex
from core.types.managers.ability import RExAbilityManager
from core.types.managers.cave import RExCaveManager
from core.types.managers.equipment import RExEquipmentManager
from core.types.managers.event import RExEventManager
from core.types.managers.layer import RExLayerManager
from core.types.managers.multiplier import RExMultiplierManager
from core.types.managers.ore import RExOreManager
from core.types.managers.recipe import RExRecipeManager
from core.types.managers.spawn import RExSpawnManager
from core.types.managers.tier import RExTierManager
from core.types.managers.variant import RExVariantManager
from core.types.managers.world import RExWorldManager


class RExDiscordRemoveCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="remove", description="Remove an item from the Index")  # type: ignore
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.is_owner()
    async def remove(self, ctx):
        return

    @remove.command(name="ability", description="Remove an Ability from the Index")  # type: ignore
    @app_commands.autocomplete(
        ability=get_items(RExAbilityManager().get_all(), lambda x: x.ability_id, lambda x: x.ability_name)
    )
    async def remove_ability(self, ctx: commands.Context, ability: str):
        manager = RExAbilityManager()
        manager.delete(lambda x: x.ability_id == ability)
        await ctx.reply(f"Removed the Ability \"{ability}\" from the Index")

    @remove.command(name="cave", description="Remove a Cave from the Index")  # type: ignore
    @app_commands.autocomplete(
        cave=get_items(RExCaveManager().get_all(), lambda x: x.cave_id, lambda x: x.cave_name)
    )
    async def remove_cave(self, ctx: commands.Context, cave: str):
        manager = RExCaveManager()
        manager.delete(lambda x: x.cave_id == cave)
        await ctx.reply(f"Removed the Cave \"{cave}\" from the Index")

    @remove.command(name="equip", description="Remove an Equipment from the Index")  # type: ignore
    @app_commands.autocomplete(
        equip=get_items(RExEquipmentManager().get_all(), lambda x: x.equip_id, lambda x: x.equip_name)
    )
    async def remove_equip(self, ctx: commands.Context, equip: str):
        manager = RExEquipmentManager()
        manager.delete(lambda x: x.equip_id == equip)
        await ctx.reply(f"Removed the Equipment \"{equip}\" from the Index")

    @remove.command(name="event", description="Remove an Event from the Index")  # type: ignore
    @app_commands.autocomplete(
        event=get_items(RExEventManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_id if isinstance(ore := x.get_ore(), NotInIndex) else ore.ore_name)
    )
    async def remove_event(self, ctx: commands.Context, event: str):
        manager = RExEventManager()
        manager.delete(lambda x: x.ore_id == event)
        await ctx.reply(f"Removed the Event \"{event}\" from the Index")

    @remove.command(name="layer", description="Remove an Layer from the Index")  # type: ignore
    @app_commands.autocomplete(
        layer=get_items(RExLayerManager().get_all(), lambda x: x.layer_id, lambda x: x.layer_name)
    )
    async def remove_layer(self, ctx: commands.Context, layer: str):
        manager = RExLayerManager()
        manager.delete(lambda x: x.layer_id == layer)
        await ctx.reply(f"Removed the Layer \"{layer}\" from the Index")

    @remove.command(name="multiplier", description="Remove a Multiplier from the Index")  # type: ignore
    @app_commands.autocomplete(
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name),
        tier=get_items(RExTierManager().get_all(), lambda x: x.tier_id, lambda x: x.tier_name)
    )
    async def remove_multiplier(self, ctx: commands.Context, variant: str, tier: str):
        manager = RExMultiplierManager()
        manager.delete(lambda x: x.variant_id == variant and x.tier_id == tier)
        await ctx.reply("Removed the Multiplier from the Index")

    @remove.command(name="ore", description="Remove an Ore from the Index")  # type: ignore
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name)
    )
    async def remove_ore(self, ctx: commands.Context, ore: str):
        manager = RExOreManager()
        manager.delete(lambda x: x.ore_id == ore)
        await ctx.reply(f"Removed the Ore \"{ore}\" from the Index")

    @remove.command(name="recipe", description="Remove a Recipe step from the Index")
    @app_commands.autocomplete(
        equipment=get_items(RExEquipmentManager().get_all(), lambda x: x.equip_id, lambda x: x.equip_name),
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name)
    )
    async def remove_recipe(self, ctx: commands.Context, equipment: str, ore: str, variant: typing.Optional[str] = None):
        manager = RExRecipeManager()
        manager.delete(lambda x: x.equip_id == equipment and x.ore_id == ore and x.variant_id == variant)
        await ctx.reply(f"Removed the Recipe step from the Index")

    @remove.command(name="spawn", description="Remove a Spawn from the Index")  # type: ignore
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        layer=get_items(RExLayerManager().get_all(), lambda x: x.layer_id, lambda x: x.layer_name),
        cave=get_items(RExCaveManager().get_all(), lambda x: x.cave_id, lambda x: x.cave_name)
    )
    async def remove_spawn(self, ctx: commands.Context, ore: str, layer: typing.Optional[str], cave: typing.Optional[str]):
        manager = RExSpawnManager()
        manager.delete(lambda x: x.ore_id == ore and x.layer_id == layer and x.cave_id == cave)
        await ctx.reply(f"Removed the Spawn from the Index")

    @remove.command(name="tier", description="Remove a Tier from the Index")  # type: ignore
    @app_commands.autocomplete(
        tier=get_items(RExTierManager().get_all(), lambda x: x.tier_id, lambda x: x.tier_name)
    )
    async def remove_tier(self, ctx: commands.Context, tier: str):
        manager = RExTierManager()
        manager.delete(lambda x: x.tier_id == tier)
        await ctx.reply(f"Removed the Tier \"{tier}\" from the Index")

    @remove.command(name="variant", description="Remove a Variant from the Index")  # type: ignore
    @app_commands.autocomplete(
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name)
    )
    async def remove_variant(self, ctx: commands.Context, variant: str):
        manager = RExVariantManager()
        manager.delete(lambda x: x.variant_id == variant)
        await ctx.reply(f"Removed the Variant \"{variant}\" from the Index")

    @remove.command(name="world", description="Remove a World from the Index")  # type: ignore
    @app_commands.autocomplete(
        world=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    async def remove_world(self, ctx: commands.Context, world: str):
        manager = RExWorldManager()
        manager.delete(lambda x: x.world_id == world)
        await ctx.reply(f"Removed the World \"{world}\" from the Index")