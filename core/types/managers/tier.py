"""
Implementation for Ore tiers.
"""

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

import discord

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.ore import RExOre
    from core.types.managers.variant import RExVariant
    from core.types.managers.multiplier import RExMultiplier


@dataclass
class RExTier:
    """A dataclass for information about REx's Pickaxe Tiers"""
    tier_id: str
    """The internal ID of the Tier"""
    tier_name: str
    """The in-game name of the Tier"""
    tier_num: int
    """The index of the Tier from most common to rarest"""
    min_rarity: int
    """The minimum rarity of the Tier"""
    max_rarity: int
    """The maximum rarity of the Tier"""
    color: discord.Color
    """The color of the Tier"""

    def get_multiplier(self, variant: "RExVariant") -> "RExMultiplier | NotInIndex":
        """Gets the Multiplier based off a given Variant"""
        from core.types.managers.multiplier import RExMultiplierManager
        return RExMultiplierManager().get_one(
            lambda x: x.variant_id == variant.variant_id and x.tier_id == self.tier_id,
            f"{variant.variant_id} + {self.tier_id}")

    def get_ores(self) -> "list[RExOre]":
        """Get all Ores in this Tier"""
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get(lambda x: x.tier_id == self.tier_id)

    def __eq__(self, other):
        return isinstance(other, RExTier) and other.tier_id == self.tier_id


class RExTierManager(RExManager[RExTier, str]):
    def _get_by_impl(self, value: str) -> RExTier | NotInIndex:
        return self.get_one(lambda x: x.tier_id == value, value)

    def get_delete_keys(self, item: RExTier) -> dict[str, Any]:
        return {
            "TIER_ID": item.tier_id
        }

    @property
    def table_name(self) -> str:
        return "TIERS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "TIER_ID", "TIER_NAME", "TIER_NUM", "MIN_RARITY", "MAX_RARITY", "COLOR"

    @property
    def primary_key(self) -> str:
        return "TIER_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExTier:
        return RExTier(*result[:-1], color=discord.Color.from_str(result[-1]))

    def prepare_db_entry(self, item: RExTier) -> dict[str, Any]:
        return {
            "tier_id": item.tier_id,
            "tier_name": item.tier_name,
            "tier_num": item.tier_num,
            "min_rarity": item.min_rarity,
            "max_rarity": item.max_rarity,
            "color": str(item.color)
        }
