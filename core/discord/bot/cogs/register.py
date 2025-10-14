import typing

from discord import app_commands
from discord.ext import commands

from core.discord.bot.util import get_items
from core.types.managers.guild import RExGuildManager
from core.types.managers.player import RExPlayerManager, RExPlayer


class RExDiscordRegisterCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="register", description="Register for tracking!")  # type: ignore[arg-type]
    @app_commands.autocomplete(
        ping_guild_id=get_items(RExGuildManager().get_all(), lambda x: str(x.guild_id), lambda x: x.guild_name,
                                predicate=lambda interaction, guild: any(
                                    [i.user_id == interaction.user.id for i in guild.get_players()]))
    )
    async def register(self, ctx: commands.Context, username: str, ping_guild_id: typing.Optional[str]):
        if ping_guild_id:
            ping_guild = int(ping_guild_id)
        else:
            ping_guild = None
        manager = RExPlayerManager()
        manager.upsert(RExPlayer(ctx.author.id, username, ping_guild, None, None))
        manager.write_to_db()
        await ctx.reply(f"Successfully registered as **{username}**")
