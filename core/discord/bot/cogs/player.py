import io
import typing

import discord
from discord import DMChannel, TextChannel, app_commands
from discord.ext import commands
from psycopg2 import sql

from core.discord.bot.util import get_items, Pagination, get_avatar
from core.discord.scraper.client import DiscordClient
from core.types.manager import NotInIndex, Selector, Comparator
from core.types.managers.guild import RExGuildManager
from core.types.managers.ore import RExOreManager
from core.types.managers.player import RExPlayerManager, RExPlayer
from core.types.managers.track import track_query, save_track, RExTrack
from core.types.managers.variant import RExVariantManager


class PlayerPaginator(Pagination[RExPlayer]):

    def __init__(self, items: list[RExPlayer], context: commands.Context):
        super().__init__(items, context)
        self.pfps: dict[int, io.BytesIO] = {}

    def to_page(self, item: RExPlayer) -> tuple[discord.Embed, typing.Optional[discord.File]]:
        avatar = self.pfps.setdefault(item.user_id, get_avatar(item))
        avatar.seek(0)
        file_name = f"{item.player_name}.png".replace(" ", "_")
        file = discord.File(avatar, file_name)
        embed = discord.Embed(
            title = item.player_name
        )
        embed.set_image(url=f"attachment://{file_name}")
        return embed, file

    def set_button_properties(self):
        self.previous.disabled = self.index == 0
        self.next.disabled = self.index == self.total_pages - 1

    @discord.ui.button(label="Prev")  # type: ignore
    async def previous(self, interaction: discord.Interaction, _: discord.Button):
        self.index = max(0, self.index - 1)
        await self.update(interaction)

    @discord.ui.button(label="Next")  # type: ignore
    async def next(self, interaction: discord.Interaction, _: discord.Button):
        self.index = min(self.index + 1, self.total_pages - 1)
        await self.update(interaction)


class RExDiscordPlayerCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="player", description="Get information about the indexed Player(s)")  # type: ignore
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def player(self, ctx):
        return

    @player.command(name="search", description="Search for Player(s)")  # type: ignore
    @app_commands.autocomplete(
        ore=get_items(RExOreManager().get_all(), lambda x: x.ore_id, lambda x: x.ore_name),
        variant=get_items(RExVariantManager().get_all(), lambda x: x.variant_id, lambda x: x.variant_name)
    )
    async def search(self, ctx: commands.Context,
                     ore: str,
                     variant: typing.Optional[str] = None
                     ):
        rex_ore, rex_variant = RExOreManager().get_one(lambda x: x.ore_id == ore, None), RExVariantManager().get_one(lambda x: x.variant_id == variant, None) if variant else None
        if isinstance(rex_ore, NotInIndex):
            await ctx.reply("You must enter a valid Ore!", ephemeral=True)
            return
        if isinstance(rex_variant, NotInIndex):
            await ctx.reply("You must enter a valid Variant!", ephemeral=True)
            return

        threshold = (0 if (not rex_ore or isinstance(tier := rex_ore.get_tier(), NotInIndex)) else tier.tier_num) + \
                    (0 if not rex_variant else rex_variant.variant_num) >= 9
        if not threshold:
            await ctx.reply("That Ore can't be tracked by the bot, so you cannot look it up.", ephemeral=True)
            return

        selectors: list[Selector | sql.SQL] = [Selector("ORE_ID", ore, Comparator.EQUAL), sql.SQL("EXISTS (SELECT 1 FROM PLAYERS WHERE PLAYERS.PLAYER_NAME = tbl.PLAYER_NAME)")]
        if variant:
            selectors.append(Selector("VARIANT_ID", variant, Comparator.EQUAL))
        tracks = track_query(None, *selectors)
        players = RExPlayerManager().get(lambda x: any([i.player_name == x.player_name for i in tracks]))

        await PlayerPaginator(players, ctx).open()

    @player.command(name="register", description="Register yourself for tracking!")
    @app_commands.autocomplete(
        ping_guild=get_items(RExGuildManager().get_all(), lambda x: str(x.guild_id), lambda x: x.guild_name, predicate=lambda interaction, guild: interaction.user.id in [i.user_id for i in guild.get_players()])
    )
    async def register(self, ctx: commands.Context, player_name: str, ping_guild: typing.Optional[str]):
        manager = RExPlayerManager()
        manager.upsert(RExPlayer(
            ctx.author.id,
            player_name,
            int(ping_guild) if ping_guild else None,
            None,
            None
        ))
        manager.write_to_db()
        await ctx.reply("Registered!", ephemeral=True)

    @player.command(name="sync", description="Sync a player's tracks with the bot")
    @commands.is_owner()
    @app_commands.autocomplete(
        player=get_items(RExPlayerManager().get_all(), lambda x: str(x.user_id), lambda x: x.player_name)
    )
    async def sync(self, ctx: commands.Context, player: str):
        from core.discord.bot.bot import RExDiscordBot
        await ctx.reply("Syncing! Check back in a bit!", ephemeral=True)
        rex_player = RExPlayerManager().get_by(int(player))
        if isinstance(rex_player, NotInIndex):
            await ctx.reply("You must enter a valid Player!", ephemeral=True)
            return
        async def save_tracks(tracks: list[RExTrack]):
            for track in tracks:
                save_track(track)
            channel = RExDiscordBot().get_channel(ctx.channel.id)
            if isinstance(channel, DMChannel) or isinstance(channel, TextChannel):
                await channel.send(f"Player {rex_player.player_name} synced successfully!")
        DiscordClient().get_player_tracks(rex_player.player_name, save_tracks)