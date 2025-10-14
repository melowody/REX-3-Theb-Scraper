from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

import discord
from discord import TextChannel, Guild, Role

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.guild import RExGuild


class RExTrackerType(Enum):
    PLAYER = "player"
    GLOBAL = "global"
    BEGINNER = "beginner"


@dataclass
class RExChannel:
    """A dataclass for information about the Discord channels registered for track broadcasts"""
    channel_id: int
    """The Discord ID of the Guild the Channel is in"""
    type: RExTrackerType
    """The type of tracks for the Channel to broadcast"""
    ping_role: int | None
    """The ID of the Discord Role to ping for the rarest finds"""

    def get_discord_channel(self) -> TextChannel | None:
        """Get the Discord Channel this RExChannel corresponds to"""
        from core.discord.bot.bot import RExDiscordBot
        if isinstance(channel := RExDiscordBot().get_channel(self.channel_id), TextChannel):
            return channel
        return None

    def get_discord_guild(self) -> Guild | None:
        """Get the Discord Guild this RExChannel is in"""
        return None if (channel := self.get_discord_channel()) is None else channel.guild

    def get_guild(self) -> "RExGuild | NotInIndex":
        """Get the RExGuild this RExChannel is in"""
        from core.types.managers.guild import RExGuildManager
        guild = self.get_discord_guild()
        if guild is None:
            return NotInIndex(self.channel_id, discord.Guild)
        return RExGuildManager().get_one(lambda x: x.guild_id == guild.id, guild.id)

    def get_ping_role(self) -> Role | None:
        """Get the Discord Role to ping for the rarest finds"""
        if self.ping_role is None or (guild := self.get_discord_guild()) is None:
            return None
        return guild.get_role(self.ping_role)

    def __eq__(self, other):
        return self.channel_id == other.channel_id


class RExChannelManager(RExManager[RExChannel]):
    @property
    def table_name(self) -> str:
        return "CHANNELS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "CHANNEL_ID", "CHANNEL_TYPE", "PING_ROLE"

    @property
    def primary_key(self) -> str:
        return "CHANNEL_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExChannel:
        return RExChannel(result[0], RExTrackerType(result[1]), result[2])

    def prepare_db_entry(self, item: RExChannel) -> dict[str, Any]:
        return {
            "CHANNEL_ID": item.channel_id,
            "CHANNEL_TYPE": item.type.value,
            "PING_ROLE": item.ping_role
        }
