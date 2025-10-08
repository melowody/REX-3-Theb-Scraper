from discord.ext import commands
from discord.ext.commands import Context

from core.types.managers.guild import RExGuildManager, RExGuild


class RExDiscordSetupCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setup", description="Set up the server for tracking") # type: ignore[arg-type]
    async def setup(self, ctx: Context, server_name: str):
        if (guild := ctx.guild) is None:
            await ctx.reply("You must set this up in a server!", ephemeral=True)
            return
        manager = RExGuildManager()
        manager.add(RExGuild(guild.id, server_name))
        manager.write_to_db()
        await ctx.reply("Server successfully setup!", ephemeral=True)