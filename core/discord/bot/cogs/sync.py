from discord import app_commands
from discord.ext import commands


class RExDiscordSyncCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="sync", description="Sync the bot's commands")  # type: ignore
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        await ctx.bot.tree.sync()
        await ctx.reply("Synced!", ephemeral=True)