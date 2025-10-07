from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from core.types.manager import RExManager, T, NotInIndex, ToLower

if TYPE_CHECKING:
    from core.types.managers.tier import RExTier
    from core.types.managers.spawn import RExSpawn

@dataclass
class RExOre:
    """A dataclass for information about REx's Ores"""
    ore_id: str
    """An internal ID for REx's Ores"""
    ore_name: str
    """The in-game name of the Ore"""
    tier_id: str
    """The internal ID of the Tier of the Ore"""
    alt_name: str
    """The alternate, keyboard-friendly name of the Ore"""

    def get_tier(self) -> "RExTier | NotInIndex":
        """Returns the Tier this Ore belongs to"""
        from core.types.managers.tier import RExTierManager
        return RExTierManager().get_one(lambda x: x.tier_id == self.tier_id, self.tier_id)

    def get_spawns(self) -> "list[RExSpawn]":
        """Returns the Spawns related to this Ore"""
        from core.types.managers.spawn import RExSpawnManager
        return RExSpawnManager().get(lambda x: x.ore_id == self.ore_id)

    def __eq__(self, other):
        return isinstance(other, RExOre) and self.ore_id == other.ore_id

class RExOreManager(RExManager[RExOre]):
    @property
    def table_name(self) -> str:
        return "ORES"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "ORE_ID", "ORE_NAME", "TIER_ID", "ALT_NAME"

    @property
    def primary_key(self) -> str:
        return "ORE_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExOre:
        return RExOre(*result)

    def prepare_db_entry(self, item: RExOre) -> dict[str, Any]:
        return {
            "ORE_ID": ToLower(item.ore_id),
            "ORE_NAME": item.ore_name,
            "TIER_ID": ToLower(item.tier_id),
            "ALT_NAME": item.alt_name
        }