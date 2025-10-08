import typing

from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from core.discord.bot.track_msg import RExDiscordTrackMessage
from core.discord.bot.util import get_items
from core.discord.scraper.runners.scraper import RExTrack
from core.types.manager import NotInIndex
from core.types.managers.cave import RExCaveManager
from core.types.managers.equipment import RExEquipmentManager, RExEquipmentType
from core.types.managers.event import RExEventManager
from core.types.managers.ore import RExOreManager, RExOre
from core.types.managers.variant import RExVariantManager
from core.types.managers.world import RExWorldManager


class RExDiscordManualCommand(commands.Cog):
    """A command to manually track a find in case the official trackers missed it"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="manual", description="Manually track an ore in case the official tracker missed it") # type: ignore[arg-type]
    @commands.is_owner()
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        world=get_items(RExWorldManager().get_all(), lambda x: x.world_id, lambda x: x.world_name),
        pickaxe=get_items(RExEquipmentManager().get(lambda x: x.equip_type == RExEquipmentType.PICKAXE),
                          lambda x: x.equip_id, lambda x: x.equip_name),
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name),
        cave=get_items(RExCaveManager().get_all(), lambda x: x.cave_id, lambda x: x.cave_name),
        event=get_items(RExEventManager().get_all(), lambda x: x.ore_id,
                        lambda x: x.event_text if isinstance(ore := RExOreManager().get_one(lambda i: i.ore_id == x.ore_id, x.ore_id), NotInIndex) else ore.ore_name)
    )
    async def manual(self, ctx: Context,
                     player_name: str,
                     ore: str,
                     world: str,
                     blocks_mined: int,
                     pickaxe: str,
                     variant: typing.Optional[str],
                     cave: typing.Optional[str],
                     event: typing.Optional[str]) -> None:
        await RExDiscordTrackMessage(self.bot, RExTrack(
            player_name,
            variant,
            ore,
            cave,
            world,
            blocks_mined,
            event,
            equip_ids=[pickaxe]
        )).send_messages()
        await ctx.reply("Ore manually tracked!", ephemeral=True)