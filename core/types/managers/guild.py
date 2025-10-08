from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from discord import Guild, TextChannel

from core.types.manager import RExManager

if TYPE_CHECKING:
    from core.types.managers.channel import RExChannel
    from core.types.managers.player import RExPlayer, RExPlayerManager


@dataclass
class RExGuild:
    """A dataclass for information about Discord Guilds that have invited this bot"""
    guild_id: int
    """The Discord ID of the Guild"""
    guild_name: str
    """The name of the Guild for tracker purposes"""

    def get_discord_guild(self) -> Guild | None:
        """Get the Discord Guild this RExGuild is representative of"""
        from core.discord.bot.bot import RExDiscordBot
        return RExDiscordBot().get_guild(self.guild_id)

    def get_channels(self) -> "list[RExChannel]":
        """Get the Channels in this Guild"""
        from core.types.managers.channel import RExChannelManager
        guild = self.get_discord_guild()
        if guild is None:
            return []
        return RExChannelManager().get(lambda x: x.channel_id in [i.id for i in guild.channels])

    def get_discord_channels(self) -> list[TextChannel]:
        """Get the Discord Channels in this Guild"""
        from core.discord.bot.bot import RExDiscordBot
        out: list[TextChannel] = []
        for i in self.get_discord_channels():
            channel = RExDiscordBot().get_channel(i.id)
            if isinstance(channel, TextChannel):
                out.append(channel)
        return out

    def get_players(self) -> "list[RExPlayer]":
        """Get the Players in this Guild"""
        if (guild := self.get_discord_guild()) is None:
            return []
        members = [i.id for i in guild.members]
        return RExPlayerManager().get(lambda x: x.user_id in members)

    def __eq__(self, other):
        return isinstance(other, RExGuild) and self.guild_id == other.guild_id

class RExGuildManager(RExManager[RExGuild]):
    @property
    def table_name(self) -> str:
        return "GUILDS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "GUILD_ID", "GUILD_NAME"

    @property
    def primary_key(self) -> str:
        return "GUILD_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExGuild:
        return RExGuild(*result)

    def prepare_db_entry(self, item: RExGuild) -> dict[str, Any]:
        return {
            "GUILD_ID": item.guild_id,
            "GUILD_NAME": item.guild_name
        }