import typing

from discord import app_commands
from discord.ext import commands
from psycopg2 import sql

from core.discord.bot.util import get_items
from core.types.manager import Selector, Comparator, NotInIndex
from core.types.managers.ore import RExOreManager
from core.types.managers.track import track_query
from core.types.managers.variant import RExVariantManager


class RExDiscordPlayerCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="player", description="Commands related to specific player queries")
    async def player(self, ctx: commands.Context):
        await ctx.reply(":3")

    @player.command(name="search", description="Search for players with a specific ore")
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name)
    )
    async def search(self, ctx: commands.Context, ore: str, variant: typing.Optional[str], limit: typing.Optional[int] = 10):
        selectors = [
            sql.SQL("tbl.player_name IN (SELECT PLAYER_NAME FROM players)"),
            Selector("ore_id", ore, Comparator.EQUAL)
        ]
        if variant:
            selectors.append(Selector("variant_id", variant, Comparator.EQUAL))
        else:
            selectors.append(sql.SQL("variant_id IS NULL"))
        tracks = track_query(limit, *selectors)

        ore = RExOreManager().get_one(lambda x: x.ore_id == ore, None)
        if isinstance(ore, NotInIndex):
            await ctx.reply("Ore not in index! Try again!", ephemeral=True)
            return

        players = [f"<@{i.get_player().user_id}>" for i in tracks]

        message = await ctx.reply(f"Players that have {ore.ore_name}: ")
        await message.edit(content=f"Players that have found {ore.ore_name}: {', '.join(players)}")