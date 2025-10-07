from discord.ext import commands


class RExDiscordSyncCommand(commands.Cog):
    """A simple command to sync any new command updates with Discord"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="sync", description="Sync slash commands with Discord")
    @commands.is_owner()
    async def sync(self, ctx):
        await ctx.bot.tree.sync()
        await ctx.reply("Synced!", ephemeral=True)