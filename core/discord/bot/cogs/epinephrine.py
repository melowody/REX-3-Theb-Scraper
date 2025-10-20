import random

from discord import app_commands
from discord.ext import commands

from core.types.manager import NotInIndex
from core.types.managers.player import RExPlayerManager


async def dm_owners(bot: commands.Bot, msg: str) -> None:
    if bot.owner_ids is None:
        return
    for i in bot.owner_ids:
        owner = bot.get_user(i)
        if owner is None:
            continue
        await owner.send(msg)


class RExDiscordEpinephrineCommand(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="epinephrine", description="Roll for Epinephrine!")  # type: ignore
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def epinephrine(self, ctx: commands.Context):

        if isinstance(player := RExPlayerManager().get_by(ctx.author.id),
                      NotInIndex):
            await ctx.reply("You need to register for the bot! Use /register", ephemeral=True)
            return

        roll = random.randrange(1, 1_000_000_000)

        min_epi, max_epi = None, None
        players = RExPlayerManager().get(lambda x: x.max_epi is not None)
        if len(players) > 0:
            min_epi = sorted(players, key=lambda p: p.min_epi)[0].min_epi  # type: ignore[arg-type, return-value]
            max_epi = sorted(players, key=lambda p: p.max_epi)[-1].max_epi  # type: ignore[arg-type, return-value]

        player.max_epi = max(0 if (mx := player.max_epi) is None else mx, roll)  # type: ignore[type-var]
        player.min_epi = min(1_000_000_000 if (mn := player.min_epi) is None else mn, roll)  # type: ignore[type-var]
        RExPlayerManager().write_to_db()

        # Handle all the custom messages
        match roll:
            case 999_999_999:
                await dm_owners(self.bot,
                                f"EPINEPHRINE!!!\nFound by <@{ctx.message.author.id}> ({ctx.message.author.name})")
                await ctx.reply(f"YOU GOT EPINEPHRINE! @everyone\n(rolled 999,999,999)")
            case 1:
                await dm_owners(self.bot,
                                f"1 ON EPINEPHRINE!!!\nFound by <@{ctx.message.author.id}> ({ctx.message.author.name})")
                await ctx.reply(f"YOU GOT...as far away from Epinephrine as possible! @everyone\n(rolled 1)")
            case s if min_epi and s < min_epi:
                await dm_owners(self.bot,
                                f"NEW LOWEST!!! ({s:,})\nFound by <@{ctx.message.author.id}> ({ctx.message.author.name})")
                await ctx.reply(
                    f"You didn't get Epinephrine :c\n(got {roll:,} but needed 999,999,999)\n# NEW LOWEST ROLL!")
            case s if max_epi and s > max_epi:
                await dm_owners(self.bot,
                                f"NEW HIGHEST!!! ({s:,})\nFound by <@{ctx.message.author.id}> ({ctx.message.author.name})")
                await ctx.reply(
                    f"You didn't get Epinephrine :c\n(got {roll:,} but needed 999,999,999)\n# NEW HIGHEST ROLL!")
            case _:
                await ctx.reply(f"You didn't get Epinephrine :c\n(got {roll:,} but needed 999,999,999)")
