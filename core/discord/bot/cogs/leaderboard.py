import typing

import discord
from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items
from core.types.manager import NotInIndex
from core.types.managers.guild import RExGuildManager
from core.types.managers.player import RExPlayerManager, RExPlayer
from core.types.managers.track import get_player_rarest, RExTrack


def get_rarest_msgs(tracks: list[RExTrack], adjusted: bool) -> list[tuple[str, str, int]]:
    out = []
    for track in tracks:
        ore = track.get_ore()
        if isinstance(ore, NotInIndex):
            continue
        rarity = track.get_base_rarity() if not adjusted else track.get_adjusted_rarity()
        if isinstance(rarity, NotInIndex):
            continue
        out.append((track.player_name, ore.ore_name, rarity, "" if (variant := track.get_variant()) is None else f"{variant.variant_name} "))
    return out

def leaderboard_predicate(interaction: discord.Interaction, player: RExPlayer) -> bool:
    for guild in player.get_guilds():
        if interaction in [i.user_id for i in guild.get_players()]:
            return True
    return False

class RExDiscordLeaderboardCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="leaderboard", aliases=["lb"], description="Get various leaderboards! (Defaults to server rarest)") # type: ignore[arg-type]
    async def leaderboard(self, ctx: commands.Context, adjusted: typing.Optional[bool] = False):
        await ctx.reply(":D")

    @leaderboard.command(name="guild", description="Global Leaderboard") # type: ignore[arg-type]
    async def guild_lb(self, ctx: commands.Context, adjusted: typing.Optional[bool]):
        guild = ctx.guild
        if not guild:
            await ctx.reply("You must be in a guild to use this command!", ephemeral=True)
            return
        rex_guild = RExGuildManager().get_one(lambda x: x.guild_id == guild.id, guild.id)
        if isinstance(rex_guild, NotInIndex):
            await ctx.reply("This guild is not set up! Use /setup", ephemeral=True)
            return
        players = rex_guild.get_players()

        rarests: list[RExTrack] = []
        for player in players:
            rarests += get_player_rarest(player)

        rarest_msgs = sorted(get_rarest_msgs(rarests, bool(adjusted)), key=lambda x: x[2], reverse=True)
        await ctx.reply(f"## {rex_guild.guild_name} Top {len(rarests)}\n{'\n'.join(f"**{i + 1}.** {j[0]} - {j[3]}{j[1]} (1 in {j[2]:,})" for i, j in enumerate(rarest_msgs))}")

    @leaderboard.command(name="player", description="Get a single player's rarest finds") # type: ignore[arg-type]
    @app_commands.autocomplete(
        player_id=get_items(RExPlayerManager().get_all(), lambda x: str(x.user_id), lambda x: x.player_name, predicate=leaderboard_predicate)
    )
    async def player(self, ctx: commands.Context, player_id: str, adjusted: typing.Optional[bool] = False):
        player = RExPlayerManager().get_one(lambda x: x.user_id == int(player_id), int(player_id))
        if isinstance(player, NotInIndex):
            await ctx.reply(f"Player not found, try again!", ephemeral=True)
            return
        rarests = get_player_rarest(player, 10)
        rarest_msgs = sorted(get_rarest_msgs(rarests, bool(adjusted)), key=lambda x: x[2], reverse=True)
        await ctx.reply(
            f"## {player.player_name} Top {len(rarests)}\n{'\n'.join(f"**{i + 1}.** {j[0]} - {j[3]}{j[1]} (1 in {j[2]:,})" for i, j in enumerate(rarest_msgs))}")