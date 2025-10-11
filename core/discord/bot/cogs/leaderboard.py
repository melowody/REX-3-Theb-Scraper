import sys
import typing
from typing import Callable

from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items
from core.types.manager import NotInIndex, Selector
from core.types.managers.guild import RExGuildManager
from core.types.managers.ore import RExOre
from core.types.managers.player import RExPlayer, RExPlayerManager
from core.types.managers.track import RExTrack, get_player_rarest, track_query
from core.types.managers.variant import RExVariant


def get_rarity(track: RExTrack, adjusted: bool) -> int | NotInIndex:
    return track.get_adjusted_rarity() if adjusted else track.get_base_rarity()

def get_player_rarests(players: list[RExPlayer], adjusted: bool, count: int = 10, start: int = 0) -> list[RExTrack]:
    out: list[RExTrack] = []
    for player in players:
        rarests = get_player_rarest(player, count)
        out += [i for i in rarests if not isinstance(get_rarity(i, adjusted), NotInIndex)]

    out = sorted(out, key=lambda x: get_rarity(x, adjusted), reverse=True)[start:start + count]
    return out

async def send_lb_message(ctx: commands.Context, title: str, tracks: list[RExTrack], formatter: Callable[[RExTrack], str]) -> None:
    messages: list[str] = []
    out = f"## {title}"
    for i, track in enumerate(tracks):
        line = f"\n**{i + 1}.** {formatter(track)}"
        if len(out) + len(line) > 2000:
            messages.append(out)
            out = line
        else:
            out += line
    if len(messages) > 0:
        await ctx.reply(messages.pop(0))
        for message in messages:
            await ctx.send(message)
    await ctx.send(out)

def check_mutual_guilds(user: int, player: RExPlayer) -> bool:
    for guild in player.get_discord_guilds():
        if not guild.get_member(user):
            return False
    return True

class RExDiscordLeaderboardCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="leaderboard", aliases=["lb"], description="Look at the rarest finds of people, guilds, or across the bot!") # type: ignore[arg-type]
    async def leaderboard(self, ctx: commands.Context):
        await ctx.reply(":D")

    @leaderboard.command(name="guild", description="Get the rarest finds in the current Guild") # type: ignore[arg-type]
    async def guild_lb(self, ctx: commands.Context, adjusted: typing.Optional[bool] = False, limit: typing.Optional[int] = 10, start: typing.Optional[int] = 0):
        guild = ctx.guild
        if guild is None:
            await ctx.reply("You must be in a guild to use this command!", ephemeral=True)
            return

        rex_guild = RExGuildManager().get_one(lambda x: x.guild_id == guild.id, guild.id)
        if isinstance(rex_guild, NotInIndex):
            await ctx.reply("This guild is not set up! Tell an admin to use /setup", ephemeral=True)
            return

        players = rex_guild.get_players()
        rarests = get_player_rarests(players, adjusted, limit, start)

        await send_lb_message(
            ctx,
            f"{rex_guild.guild_name} Top {min(limit, len(rarests))}",
            rarests,
            lambda x: f"{x.player_name} - {"" if not isinstance(var := x.get_variant(), RExVariant) else (var.variant_name + " ")}{"NotInIndex" if not isinstance(ore := x.get_ore(), RExOre) else ore.ore_name} (1 in {get_rarity(x, adjusted):,})")

    @leaderboard.command(name="player", description="Get the rarest finds of a specific Player")
    @app_commands.autocomplete(
        player=get_items(RExPlayerManager().get_all(), lambda x: str(x.user_id), lambda x: x.player_name, predicate=lambda interaction, player: check_mutual_guilds(interaction.user.id, player))
    )
    async def player_lb(self, ctx: commands.Context, player: str, adjusted: typing.Optional[bool] = False, limit: typing.Optional[int] = 10, start: typing.Optional[int] = 0):
        player_id = int(player)
        rex_player = RExPlayerManager().get_one(lambda x: x.user_id == player_id, None)
        if isinstance(rex_player, NotInIndex):
            await ctx.reply("That player isn't signed up for the bot!", ephemeral=True)
            return
        rarests = get_player_rarests([rex_player], adjusted, limit, start)
        await send_lb_message(
            ctx,
            f"{rex_player.player_name} Top {min(limit, len(rarests))}",
            rarests,
            lambda x: f"{"" if not isinstance(var := x.get_variant(), RExVariant) else (var.variant_name + " ")}{"NotInIndex" if not isinstance(ore := x.get_ore(), RExOre) else ore.ore_name} (1 in {get_rarity(x, adjusted):,})"
        )

    @leaderboard.command(name="global", description="Get the rarest finds from all players registered to the bot")
    async def global_lb(self, ctx: commands.Context, adjusted: typing.Optional[bool] = False, limit: typing.Optional[int] = 10, start: typing.Optional[int] = 0):
        rarests = track_query("TRACKS", None)
        await send_lb_message(
            ctx,
            f"Global Top {min(limit, len(rarests))}",
            list(filter(lambda x: isinstance(RExPlayerManager().get_one(lambda j: j.player_name == x.player_name, None), RExPlayer), rarests)),
            lambda x: f"{x.player_name} - {"" if not isinstance(var := x.get_variant(), RExVariant) else (var.variant_name + " ")}{"NotInIndex" if not isinstance(ore := x.get_ore(), RExOre) else ore.ore_name} (1 in {get_rarity(x, adjusted):,})"
        )