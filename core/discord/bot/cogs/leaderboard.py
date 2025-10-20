import math
import typing

import discord
from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import Pagination, U, get_items
from core.types.manager import NotInIndex
from core.types.managers.cave import RExCave
from core.types.managers.guild import RExGuildManager
from core.types.managers.player import RExPlayer, RExPlayerManager
from core.types.managers.track import RExTrack, get_player_rarest


class LeaderboardPaginator(Pagination[RExTrack]):

    def __init__(self, items: list[RExTrack], context: commands.Context, name: str, adjusted: bool = False):
        super().__init__(items, context)
        self.name = name
        self.adjusted = adjusted

    def to_page(self, item: RExTrack) -> tuple[discord.Embed, typing.Optional[discord.File]]:
        embed = discord.Embed(title=f"{self.name} Rarest Finds ({10 * self.index + 1} - {min(10 * (self.index + 1), len(self.items) - 1)}/{len(self.items) - 1})")
        base_ore = self.items[0].get_ore()
        if not isinstance(base_ore, NotInIndex):
            tier = base_ore.get_tier()
            if not isinstance(tier, NotInIndex):
                embed.colour = tier.color
        desc = []
        for j, i in enumerate(self.items[10 * self.index:10 * (self.index + 1)]):
            variant = i.get_variant()
            if isinstance(variant, NotInIndex):
                continue
            ore = i.get_ore()
            if isinstance(ore, NotInIndex):
                continue
            rarity = i.get_base_rarity() if not self.adjusted else i.get_adjusted_rarity()
            if isinstance(rarity, NotInIndex):
                continue
            prefix = ""
            if self.adjusted:
                cave = i.get_cave()
                if isinstance(cave, RExCave):
                    prefix = f"({cave.cave_name}) "
            desc.append(
                f"{j + self.index * 10}. **{i.player_name}** - {prefix}{f"{variant.variant_name} " if variant else ""}{ore.ore_name} (1 in {rarity:,})")
        embed.description = "\n".join(desc)
        return embed, None

    def set_button_properties(self):
        self.start.disabled = self.index == 0
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index == math.ceil(self.total_pages / 10) - 1
        self.end.disabled = self.index == math.ceil(self.total_pages / 10) - 1

    @discord.ui.button(label="Start")  # type: ignore
    async def start(self, interaction: discord.Interaction, _: discord.Button):
        self.index = 0
        await self.update(interaction)

    @discord.ui.button(label="Prev")  # type: ignore
    async def previous(self, interaction: discord.Interaction, _: discord.Button):
        self.index = max(0, self.index - 1)
        await self.update(interaction)

    @discord.ui.button(label="Next")  # type: ignore
    async def next(self, interaction: discord.Interaction, _: discord.Button):
        self.index = min(self.index + 1, math.ceil(self.total_pages / 10) - 1)
        await self.update(interaction)

    @discord.ui.button(label="End")  # type: ignore
    async def end(self, interaction: discord.Interaction, _: discord.Button):
        self.index = math.ceil(self.total_pages / 10) - 1
        await self.update(interaction)


def get_player_rarests(players: list[RExPlayer], adjusted: bool, count: int | None = 10, start: int = 0) -> list[
    RExTrack]:
    out: list[RExTrack] = []
    for player in players:
        rarests = get_player_rarest(player, count)
        out += [i for i in rarests if not isinstance(i.get_adjusted_rarity() if adjusted else i.get_base_rarity(), NotInIndex)]

    out = sorted(out, key=lambda x: x.get_adjusted_rarity() if adjusted else x.get_base_rarity(), reverse=True)[start:start + (count if count else len(out))]
    return out

def check_mutual_guilds(interaction: discord.Interaction, player: RExPlayer) -> bool:
    user_id = interaction.user.id
    for guild in player.get_discord_guilds():
        if not guild.get_member(user_id):
            return False
    return True

class RExDiscordLeaderboardCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="leaderboard",  # type: ignore
                           description="Look at the rarest finds of people, guilds, or across the bot!")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def leaderboard(self, ctx: commands.Context):
        return

    @leaderboard.command(name="guild")  # type: ignore
    @app_commands.autocomplete(
        guild=get_items(RExGuildManager().get_all(), lambda x: str(x.guild_id), lambda x: x.guild_name,
                        predicate=lambda interaction, guild: any(
                            [i.user_id == interaction.user.id for i in guild.get_players()]))
    )
    async def guild(self, ctx: commands.Context, guild: typing.Optional[str], adjusted: typing.Optional[bool] = False):
        if guild:
            rex_guild = RExGuildManager().get_by(int(guild))
        else:
            msg_guild = ctx.guild
            if msg_guild:
                rex_guild = RExGuildManager().get_by(msg_guild.id)
            else:
                await ctx.reply("You must run this from a Guild or specify the Guild with the `guild` option!",
                                ephemeral=True)
                return
        if isinstance(rex_guild, NotInIndex):
            await ctx.reply("This guild is not set up! Tell an admin to use /setup", ephemeral=True)
            return

        rarests = get_player_rarests(rex_guild.get_players(), adjusted, count=None)
        await LeaderboardPaginator(rarests, ctx, rex_guild.guild_name, adjusted).open()

    @leaderboard.command(name="global")
    async def lb_global(self, ctx: commands.Context, adjusted: typing.Optional[bool] = False):
        rarests = get_player_rarests(RExPlayerManager().get_all(), adjusted, count=None)
        await LeaderboardPaginator(rarests, ctx, "Global", adjusted).open()

    @leaderboard.command(name="player")
    @app_commands.autocomplete(
        player=get_items(RExPlayerManager().get_all(), lambda x: str(x.user_id), lambda x: x.player_name, predicate=check_mutual_guilds)
    )
    async def player(self, ctx: commands.Context, player: str, adjusted: typing.Optional[bool] = False):
        rex_player = RExPlayerManager().get_by(int(player))
        if isinstance(rex_player, NotInIndex):
            await ctx.reply("You must enter a Player who's signed up for tracking!", ephemeral=True)
        rarests = get_player_rarests([rex_player], adjusted, count=None)
        await LeaderboardPaginator(rarests, ctx, f"{rex_player.player_name}'s", adjusted).open()