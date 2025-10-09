import typing

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import hybrid_command, Context

from core.discord.bot.util import get_items
from core.types.managers.guild import RExGuildManager, RExGuild
from core.types.managers.player import RExPlayerManager, RExPlayer


class RExDiscordRegisterCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @hybrid_command(name="register", description="Register for tracking!")
    @app_commands.autocomplete(
        ping_guild_id=get_items(RExGuildManager().get_all(), lambda x: x.guild_id, lambda x: x.guild_name, lambda interaction, guild: (discord_guild := guild.get_discord_guild()) and interaction.message.author.id in [i.id for i in discord_guild.members])
    )
    async def register(self, ctx: Context, username: str, ping_guild_id: typing.Optional[str]):
        ping_guild = int(ping_guild_id)
        manager = RExPlayerManager()
        manager.add(RExPlayer(ctx.author.id, username, ping_guild_id, None, None))
        manager.write_to_db()
        await ctx.reply(f"Successfully registered as **{username}**")