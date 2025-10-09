from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from discord import User, Guild

from core.types.manager import RExManager

if TYPE_CHECKING:
    from core.types.managers.guild import RExGuild


@dataclass
class RExPlayer:
    """A dataclass for information about Discord Users who have registered for the bot"""
    user_id: int
    """The Discord ID of the Player"""
    player_name: str
    """The in-game username of the Player"""
    guild_id: int | None
    """The ID of the Guild the Player wants to be pinged in for rare finds"""
    max_epi: int | None
    """The maximum epinephrine role this Player has gotten"""
    min_epi: int | None
    """The minimum epinephrine role this Player has gotten"""

    def get_discord_user(self) -> User | None:
        """Returns the User associated with this Player"""
        from core.discord.bot.bot import RExDiscordBot
        return RExDiscordBot().get_user(self.user_id)

    def get_ping_guild(self) -> Guild | None:
        """Returns the Guild this Player wishes to be pinged in for rare finds"""
        from core.discord.bot.bot import RExDiscordBot
        return RExDiscordBot().get_guild(self.guild_id)

    def get_discord_guilds(self) -> list[Guild]:
        """Returns the Discord Guilds this Player is in"""
        from core.types.managers.guild import RExGuildManager
        user = self.get_discord_user()
        if user is None:
            return []
        return [i for i in user.mutual_guilds if RExGuildManager().exists(lambda x: x.guild_id == i.id)]

    def get_guilds(self) -> "list[RExGuild]":
        """Returns the RExGuilds this Player is in"""
        from core.types.managers.guild import RExGuildManager
        guilds = [i.id for i in self.get_discord_guilds()]
        return RExGuildManager().get(lambda x: x.guild_id in guilds)

    def __eq__(self, other):
        return isinstance(other, RExPlayer) and self.user_id == other.user_id

class RExPlayerManager(RExManager[RExPlayer]):

    @property
    def table_name(self) -> str:
        return "PLAYERS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "USER_ID", "PLAYER_NAME", "GUILD_ID", "MAX_EPI", "MIN_EPI"

    @property
    def primary_key(self) -> str:
        return "USER_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExPlayer:
        return RExPlayer(*result)

    def prepare_db_entry(self, item: RExPlayer) -> dict[str, Any]:
        return {
            "USER_ID": item.user_id,
            "PLAYER_NAME": item.player_name,
            "GUILD_ID": item.guild_id,
            "MAX_EPI": item.max_epi,
            "MIN_EPI": item.min_epi
        }