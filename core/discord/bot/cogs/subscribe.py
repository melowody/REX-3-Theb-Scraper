import typing

import discord
from discord.ext import commands

from core.types.managers.channel import RExTrackerType, RExChannelManager, RExChannel
from core.types.managers.guild import RExGuildManager, RExGuild


class RExDiscordSubscribeCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="subscribe", description="Sign up a command for tracking!")
    @commands.has_permissions(manage_channels=True)
    async def subscribe(self, ctx: commands.Context, channel_type: RExTrackerType, ping_role: typing.Optional[discord.Role]):

        if (guild := ctx.guild) is None:
            await ctx.reply("You must set this up in a server!", ephemeral=True)
            return

        if not RExGuildManager().exists(lambda x: x.guild_id == guild.id):
            await ctx.reply("This guild has not registered to the bot! Use /setup!")
            return

        manager = RExChannelManager()
        manager.add(RExChannel(ctx.channel.id, channel_type, None if ping_role is None else ping_role.id))
        manager.write_to_db()
        await ctx.reply("Channel subscribed to tracking!")