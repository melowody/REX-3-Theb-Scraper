import typing

import discord
from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items
from core.types.manager import NotInIndex
from core.types.managers.ability import RExAbilityManager, RExAbility
from core.types.managers.cave import RExCaveManager, RExCave
from core.types.managers.equipment import RExEquipmentManager, RExEquipmentType, RExEquipment
from core.types.managers.event import RExEventManager, RExEvent
from core.types.managers.layer import RExLayerManager, RExLayer
from core.types.managers.multiplier import RExMultiplierManager, RExMultiplier
from core.types.managers.ore import RExOreManager, RExOre
from core.types.managers.recipe import RExRecipeManager, RExRecipeStep
from core.types.managers.spawn import RExSpawnManager, RExSpawn
from core.types.managers.tier import RExTierManager, RExTier
from core.types.managers.variant import RExVariantManager, RExVariant
from core.types.managers.world import RExWorldManager, RExWorld


class RExDiscordSetCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="set", description="Add an item to the Index")  # type: ignore
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.is_owner()
    async def add(self, _: commands.Context):
        return

    @add.command(name="ability", description="Add an Ability to the Index")  # type: ignore
    @app_commands.autocomplete(
        equipment=get_items(RExAbilityManager().get_all(), lambda x: x.ability_id, lambda x: x.ability_name)
    )
    async def ability(self, ctx: commands.Context,
                      ability_id: str,
                      equipment: str,
                      name: str,
                      description: str,
                      proc_rate: int,
                      luck: typing.Optional[str] = None,
                      lifespan: typing.Optional[str] = None,
                      area: typing.Optional[str] = None,
                      amount: typing.Optional[str] = None,
                      pinned_luck: typing.Optional[str] = None
                      ):
        if not RExEquipmentManager().exists(lambda x: x.equip_id == equipment):
            await ctx.reply("You must enter a valid Equipment!")
            return
        manager = RExAbilityManager()
        ability = RExAbility(
            ability_id,
            equipment,
            name,
            description,
            proc_rate,
            luck,
            lifespan,
            area,
            amount,
            pinned_luck
        )
        manager.upsert(ability)
        manager.write_to_db()
        await ctx.reply(f"Ability \"{name}\" added to the Index!")

    @add.command(name="cave", description="Add a Cave to the Index")  # type: ignore
    @app_commands.autocomplete(
        wall_ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        world=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    async def cave(self, ctx: commands.Context,
                   cave_id: str,
                   name: str,
                   wall_ore: str,
                   world: str,
                   rarity: int
                   ):
        if not RExOreManager().exists(lambda x: x.ore_id == wall_ore):
            await ctx.reply("You must enter a valid Ore!")
            return
        if not RExWorldManager().exists(lambda x: x.world_id == world):
            await ctx.reply("You must enter a valid World!")
            return
        manager = RExCaveManager()
        cave = RExCave(
            cave_id,
            wall_ore,
            name,
            world,
            rarity
        )
        manager.upsert(cave)
        manager.write_to_db()
        await ctx.reply(f"Cave \"{name}\" added to the Index!")

    @add.command(name="equipment", description="Add an Equipment to the Index")  # type: ignore
    @app_commands.autocomplete(
        world=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    async def equipment(self, ctx: commands.Context,
                        equip_id: str,
                        name: str,
                        description: str,
                        tier: int,
                        equip_type: RExEquipmentType,
                        world: typing.Optional[str] = None):
        if world and not RExWorldManager().exists(lambda x: x.world_id == world):
            await ctx.reply("You must enter a valid World!")
            return
        manager = RExEquipmentManager()
        equipment = RExEquipment(
            equip_id,
            name,
            description,
            tier,
            equip_type,
            world
        )
        manager.upsert(equipment)
        manager.write_to_db()
        await ctx.reply(f"Equipment \"{name}\" added to the Index!")

    @add.command(name="event", description="Add an Event to the Index")  # type: ignore
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        world=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    async def event(self, ctx: commands.Context,
                    ore: str,
                    world: str,
                    spawn_text: str,
                    description: str,
                    new_rarity: int,
                    duration: int,
                    chance: int
                    ):
        if isinstance(rex_ore := RExOreManager().get_one(lambda x: x.ore_id == ore, None), NotInIndex):
            await ctx.reply("You must enter a valid Ore!")
            return
        if not RExWorldManager().exists(lambda x: x.world_id == world):
            await ctx.reply("You must enter a valid World!")
            return
        manager = RExEventManager()
        event = RExEvent(
            ore,
            world,
            spawn_text,
            description,
            new_rarity,
            duration,
            chance
        )
        manager.upsert(event)
        manager.write_to_db()
        await ctx.reply(f"Event \"{rex_ore.ore_name}\" added to the Index!")

    @add.command(name="layer", description="Add a Layer to the Index")  # type: ignore
    @app_commands.autocomplete(
        layer_ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        world=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    async def layer(self, ctx: commands.Context,
                    layer_id: str,
                    layer_ore: str,
                    name: str,
                    world: str,
                    min_depth: int,
                    max_depth: int):
        if not RExOreManager().exists(lambda x: x.ore_id == layer_ore):
            await ctx.reply("You must enter a valid Ore!")
            return
        if not RExWorldManager().exists(lambda x: x.world_id == world):
            await ctx.reply("You must enter a valid World!")
            return
        manager = RExLayerManager()
        layer = RExLayer(
            layer_id,
            layer_ore,
            name,
            world,
            min_depth,
            max_depth
        )
        manager.upsert(layer)
        manager.write_to_db()
        await ctx.reply(f"Layer \"{name}\" added to the Index!")

    @add.command(name="multiplier", description="Add a Multiplier to the Index")  # type: ignore
    @app_commands.autocomplete(
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name),
        tier=get_items(RExTierManager().get_all(), lambda x: x.tier_id, lambda x: x.tier_name)
    )
    async def multiplier(self, ctx: commands.Context,
                         variant: str,
                         tier: str,
                         multiplier: int
                         ):
        if not RExVariantManager().exists(lambda x: x.variant_id == variant):
            await ctx.reply("You must enter a valid Variant!")
            return
        if not RExTierManager().exists(lambda x: x.tier_id == tier):
            await ctx.reply("You must enter a valid Tier!")
            return
        manager = RExMultiplierManager()
        rex_multiplier = RExMultiplier(
            variant,
            tier,
            multiplier
        )
        manager.upsert(rex_multiplier)
        manager.write_to_db()
        await ctx.reply(f"Multiplier added to the Index!")

    @add.command(name="ore", description="Add an Ore to the Index")  # type: ignore
    @app_commands.autocomplete(
        tier=get_items(RExTierManager().get_all(), lambda x: x.tier_id, lambda x: x.tier_name)
    )
    async def ore(self, ctx: commands.Context,
                  ore_id: str,
                  name: str,
                  tier: str,
                  alt_name: typing.Optional[str] = None
                  ):
        if not RExTierManager().exists(lambda x: x.tier_id == tier):
            await ctx.reply("You must enter a valid Tier!")
            return
        manager = RExOreManager()
        rex_ore = RExOre(
            ore_id,
            name,
            tier,
            alt_name
        )
        manager.upsert(rex_ore)
        manager.write_to_db()
        await ctx.reply(f"Ore \"{name}\" added to the Index!")

    @add.command(name="recipe", description="Add a step of a Recipe to the Index")  # type: ignore
    @app_commands.autocomplete(
        equipment=get_items(RExEquipmentManager().get_all(), lambda x: x.equip_id, lambda x: x.equip_name),
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name)
    )
    async def recipe(self, ctx: commands.Context,
                     equipment: str,
                     ore: str,
                     count: int,
                     variant: typing.Optional[str] = None
                     ):
        if not RExEquipmentManager().exists(lambda x: x.equip_id == equipment):
            await ctx.reply("You must enter a valid Equipment!")
            return
        if not RExOreManager().exists(lambda x: x.ore_id == ore):
            await ctx.reply("You must enter a valid Ore!")
            return
        if not RExVariantManager().exists(lambda x: x.variant_id == variant):
            await ctx.reply("You must enter a valid Variant!")
            return
        manager = RExRecipeManager()
        rex_recipe = RExRecipeStep(
            equipment,
            ore,
            count,
            variant
        )
        manager.upsert(rex_recipe)
        manager.write_to_db()
        await ctx.reply("Added Recipe step to Index!")

    @add.command(name="spawn", description="Add a Spawn to the Index")  # type: ignore
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        layer=get_items(RExLayerManager().get_all(), lambda x: x.layer_id, lambda x: x.layer_name),
        cave=get_items(RExCaveManager().get_all(), lambda x: x.cave_id, lambda x: x.cave_name),
    )
    async def spawn(self, ctx: commands.Context,
                    ore: str,
                    rarity: int,
                    layer: typing.Optional[str] = None,
                    cave: typing.Optional[str] = None
                    ):
        if not RExOreManager().exists(lambda x: x.ore_id == ore):
            await ctx.reply("You must enter a valid Ore!")
            return
        if layer and not RExLayerManager().exists(lambda x: x.layer_id == layer):
            await ctx.reply("You must enter a valid Layer!")
            return
        if cave and not RExCaveManager().exists(lambda x: x.cave_id == cave):
            await ctx.reply("You must enter a valid Cave!")
            return
        manager = RExSpawnManager()
        rex_spawn = RExSpawn(
            ore,
            layer,
            cave,
            rarity
        )
        manager.upsert(rex_spawn)
        manager.write_to_db()
        await ctx.reply(f"Spawn added to the Index!")

    @add.command(name="tier", description="Add a Tier to the Index")  # type: ignore
    async def tier(self, ctx: commands.Context,
                   tier_id: str,
                   name: str,
                   num: int,
                   min_rarity: int,
                   max_rarity: int,
                   color: str
                   ):
        manager = RExTierManager()
        rex_tier = RExTier(
            tier_id,
            name,
            num,
            min_rarity,
            max_rarity,
            discord.Color.from_str(color)
        )
        manager.upsert(rex_tier)
        manager.write_to_db()
        await ctx.reply(f"Tier \"{name}\" added to the Index!")

    @add.command(name="variant", description="Add a Variant to the Index")  # type: ignore
    async def variant(self, ctx: commands.Context,
                      variant_id: str,
                      name: str,
                      num: int
                      ):
        manager = RExVariantManager()
        rex_variant = RExVariant(
            variant_id,
            name,
            num
        )
        manager.upsert(rex_variant)
        manager.write_to_db()
        await ctx.reply(f"Variant \"{name}\" added to the Index!")

    @add.command(name="world", description="Add a World to the Index")  # type: ignore
    async def world(self, ctx: commands.Context,
                    world_id: str,
                    name: str,
                    description: str
                    ):
        manager = RExWorldManager()
        rex_world = RExWorld(
            world_id,
            name,
            description
        )
        manager.upsert(rex_world)
        manager.write_to_db()
        await ctx.reply(f"World \"{name}\" added to the Index!")