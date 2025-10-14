from dataclasses import dataclass
from typing import Any

from discord import User

from core.types.manager import RExManager


@dataclass
class RExTracker:
    """A dataclass for information about the official REx trackers"""
    tracker_id: int

    def get_discord_user(self) -> User | None:
        """Get the Discord User associated with this REx Tracker"""
        from core.discord.bot.bot import RExDiscordBot
        return RExDiscordBot().get_user(self.tracker_id)

    def __eq__(self, other):
        return other is RExTracker and self.tracker_id == other.tracker_id


class RExTrackerManager(RExManager[RExTracker]):
    @property
    def table_name(self) -> str:
        return "TRACKERS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "TRACKER_ID",

    @property
    def primary_key(self) -> str:
        return "TRACKER_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExTracker:
        return RExTracker(*result)

    def prepare_db_entry(self, item: RExTracker) -> dict[str, Any]:
        return {
            "tracker_id": item.tracker_id
        }
