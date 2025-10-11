import typing

from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items
from core.types.managers.ability import RExAbilityManager, RExAbility
from core.types.managers.cave import RExCaveManager, RExCave
from core.types.managers.equipment import RExEquipmentType, RExEquipmentManager, RExEquipment
from core.types.managers.event import RExEventManager, RExEvent
from core.types.managers.layer import RExLayerManager, RExLayer
from core.types.managers.ore import RExOreManager, RExOre
from core.types.managers.recipe import RExRecipeManager, RExRecipeStep
from core.types.managers.spawn import RExSpawnManager, RExSpawn
from core.types.managers.tier import RExTierManager, RExTier
from core.types.managers.tracker import RExTrackerManager, RExTracker
from core.types.managers.variant import RExVariantManager, RExVariant
from core.types.managers.world import RExWorldManager, RExWorld


class RExDiscordAddCommand(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_group(name="add", description="Add items to the game index") # type: ignore[arg-type]
    @commands.is_owner()
    async def add(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply("You must specify what to add!", ephemeral=True)

    @add.command(name="world", description="Add a new world to the index") # type: ignore[arg-type]
    @app_commands.describe(
        world_id = "The internal ID of the World",
        world_name = "The in-game name of the World",
        world_desc = "The in-game description of the World"
    )
    async def add_world(self, ctx: commands.Context, world_id: str, world_name: str, world_desc: str):
        manager = RExWorldManager()
        manager.add(RExWorld(world_id, world_name, world_desc))
        manager.write_to_db()
        await ctx.reply(f"World \"{world_name}\" added to index!", ephemeral=True)

    @add.command(name="cave", description="Add a new cave to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(
        world_id=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name),
        ore_id=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name, secondary=lambda x: "" if (alt := x.alt_name) is None else alt)
    )
    @app_commands.describe(
        cave_id = "The internal ID of the Cave",
        cave_name = "The in-game name of the Cave",
        world_id = "The World the Cave spawns in",
        cave_rarity = "The Cave's rarity constant"
    )
    async def add_cave(self, ctx: commands.Context, cave_id: str, ore_id: str, cave_name: str, world_id: str, cave_rarity: int):
        manager = RExCaveManager()
        manager.add(RExCave(cave_id, ore_id, cave_name, world_id, cave_rarity))
        manager.write_to_db()
        await ctx.reply(f"Cave \"{cave_name}\" added to index!", ephemeral=True)

    @add.command(name="layer", description="Add a new layer to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(
        world_id=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name),
        ore_id=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name, secondary=lambda x: "" if (alt := x.alt_name) is None else alt)
    )
    @app_commands.describe(
        layer_id = "The internal ID of the Layer",
        layer_name = "The in-game name of the Layer",
        world_id = "The World the Layer spawns in",
        min_depth = "The depth the Layer starts at",
        max_depth = "The depth the Layer ends at"
    )
    async def add_layer(self, ctx: commands.Context, layer_id: str, ore_id: str, layer_name: str, world_id: str, min_depth: int, max_depth: int):
        manager = RExLayerManager()
        manager.add(RExLayer(layer_id, ore_id, layer_name, world_id, min_depth, max_depth))
        manager.write_to_db()
        await ctx.reply(f"Layer \"{layer_name}\" added to index!", ephemeral=True)

    @add.command(name="tier", description="Add a new tier to the index") # type: ignore[arg-type]
    @app_commands.describe(
        tier_id = "The internal ID of the Tier",
        tier_name = "The in-game name of the Tier",
        tier_num = "The index of the Tier in ascending rarity (when added will shift everything above it up one)",
        min_rarity = "The minimum rarity in the Tier",
        max_rarity = "The maximum rarity in the Tier",
    )
    async def add_tier(self, ctx: commands.Context, tier_id: str, tier_name: str, tier_num: int, min_rarity: int, max_rarity: int):
        manager = RExTierManager()
        manager.add(RExTier(tier_id, tier_name, tier_num, min_rarity, max_rarity))
        manager.write_to_db()
        await ctx.reply(f"Tier \"{tier_name}\" added to index!", ephemeral=True)

    @add.command(name="ore", description="Add a new ore to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(tier_id=get_items(RExTierManager().get_all(), lambda x: x.tier_id, lambda x: x.tier_name))
    @app_commands.describe(
        ore_id = "The internal ID of the Ore",
        ore_name = "The in-game name of the Ore",
        tier_id = "The Tier the Ore is in"
    )
    async def add_ore(self, ctx: commands.Context, ore_id: str, ore_name: str, tier_id: str, alt_name: typing.Optional[str]):
        manager = RExOreManager()
        manager.add(RExOre(ore_id, ore_name, tier_id, alt_name))
        manager.write_to_db()
        await ctx.reply(f"Ore \"{ore_name}\" added to index!", ephemeral=True)

    @add.command(name="spawn", description="Add a new spawn to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(
        ore_id = get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        layer_id = get_items(RExLayerManager().get_all(), lambda x: x.layer_id, lambda x: x.layer_name),
        cave_id = get_items(RExCaveManager().get_all(), lambda x: x.cave_id, lambda x: x.cave_name)
    )
    @app_commands.describe(
        ore_id = "The Ore found in this Spawn",
        layer_id = "The Layer this Spawn is in",
        cave_id = "The Cave this Spawn is in",
        rarity = "The rarity of the Spawn"
    )
    async def add_spawn(self, ctx: commands.Context, ore_id: str, layer_id: typing.Optional[str], cave_id: typing.Optional[str], rarity: int):
        manager = RExSpawnManager()
        manager.add(RExSpawn(ore_id, layer_id, cave_id, rarity))
        manager.write_to_db()
        await ctx.reply(f"Spawn added to index!", ephemeral=True)

    @add.command(name="equipment", description="Add a new equipment to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(
        world_id=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    @app_commands.describe(
        equip_id="The internal ID of the equipment",
        equip_tier="The tier of the equipment (1 - 10)",
        equip_type="The type of equipment",
        world_id="The world the equipment is found in"
    )
    async def add_equipment(self, ctx: commands.Context, equip_id: str, equip_name: str, equip_desc, equip_tier: int, equip_type: RExEquipmentType, world_id: typing.Optional[str]):
        manager = RExEquipmentManager()
        manager.add(RExEquipment(equip_id, equip_name, equip_desc, equip_tier, equip_type, world_id))
        manager.write_to_db()
        await ctx.reply(f"Equipment added to index!", ephemeral=True)

    @add.command(name="recipe", description="Add a recipe step to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(
        equip_id=get_items(RExEquipmentManager().get_all(), lambda x: x.equip_id, lambda x: x.equip_name),
        ore_id=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name, secondary=lambda x: "" if (alt := x.alt_name) is None else alt)
    )
    @app_commands.describe(
        equip_id="The equipment this recipe concerns",
        ore_id="The ore in this recipe step",
        count="The amount of the ore needed"
    )
    async def add_recipe(self, ctx: commands.Context, equip_id: str, ore_id: str, count: int):
        manager = RExRecipeManager()
        manager.add(RExRecipeStep(equip_id, ore_id, count))
        manager.write_to_db()
        await ctx.reply(f"Recipe Step added to index!", ephemeral=True)

    @add.command(name="ability", description="Add an equipment ability to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(
        equip_id=get_items(RExEquipmentManager().get_all(), lambda x: x.equip_id, lambda x: x.equip_name)
    )
    @app_commands.describe(
        ability_id="The internal ID of the ability",
        equip_id="The equipment this ability concerns",
        ability_name="The ability name",
        ability_desc="A description of the ability",
        ability_rate="The rate at which the ability procs",
        ability_luck="The luck boost of the ability",
        ability_lifespan="The lifespan of the ability",
        ability_area="The area of the ability",
        ability_amount="The amount of the ability's effects"
    )
    async def add_ability(self, ctx: commands.Context, ability_id: str, equip_id: str, ability_name: str, ability_desc: str, ability_rate: int, ability_luck: typing.Optional[str], ability_lifespan: typing.Optional[str], ability_area: typing.Optional[str], ability_amount: typing.Optional[str]):
        manager = RExAbilityManager()
        manager.add(RExAbility(
            ability_id,
            equip_id,
            ability_name,
            ability_desc,
            ability_rate,
            ability_luck,
            ability_lifespan,
            ability_area,
            ability_amount
        ))
        manager.write_to_db()
        await ctx.reply(f"Ability {ability_name} added to index!", ephemeral=True)

    @add.command(name="event", description="Add an event to the index") # type: ignore[arg-type]
    @app_commands.autocomplete(
        ore_id=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name, secondary=lambda x: "" if (alt := x.alt_name) is None else alt),
        world_id=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name)
    )
    @app_commands.describe(
        ore_id="The ore this event is revolved around",
        world_id="The world this event is in",
        event_text="The text displayed in-game when this event is active",
        event_desc="A description of what the event does (primary ore nerf excluded)",
        ore_rarity="The nerfed rarity of the primary ore",
        event_duration="The duration of the event in seconds",
        event_chance="The chance of the event every second"
    )
    async def add_event(self, ctx: commands.Context, ore_id: str, world_id: str, event_text: str, event_desc: str, ore_rarity: int, event_duration: int, event_chance: int):
        manager = RExEventManager()
        manager.add(RExEvent(
            ore_id,
            world_id,
            event_text,
            event_desc,
            ore_rarity,
            event_duration,
            event_chance
        ))
        manager.write_to_db()
        await ctx.reply(f"Event added to index!", ephemeral=True)

    @add.command(name="tracker", description="Add a tracker for the bot to scrape") # type: ignore[arg-type]
    @app_commands.describe(
        tracker_id="The ID of the tracker in the REx server"
    )
    async def add_tracker(self, ctx: commands.Context, tracker_id: str):
        if not tracker_id.isdigit():
            await ctx.reply(f"Invalid tracker ID!", ephemeral=True)
            return
        tracker_num = int(tracker_id)
        manager = RExTrackerManager()
        manager.add(RExTracker(tracker_num))
        manager.write_to_db()
        await ctx.reply(f"Tracker added to index!", ephemeral=True)

    @add.command(name="variant", description="Add a variant to the bot's index") # type: ignore[arg-type]
    async def add_variant(self, ctx: commands.Context, variant_id: str, variant_name: str, variant_num: int):
        manager = RExVariantManager()
        manager.add(RExVariant(variant_id, variant_name, variant_num))
        manager.write_to_db()
        await ctx.reply(f"Variant \"{variant_name}\" added to index!", ephemeral=True)