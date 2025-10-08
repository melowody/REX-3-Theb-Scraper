from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from core.types.manager import NotInIndex
from core.types.manager import RExManager

if TYPE_CHECKING:
    from core.types.managers.variant import RExVariant
    from core.types.managers.tier import RExTier

@dataclass
class RExMultiplier:
    """A dataclass for information about REx's Variant Multipliers"""
    variant_id: str
    """The internal ID of the Variant"""
    tier_id: str
    """The internal ID of the Tier"""
    multiplier: int

    def get_variant(self) -> "RExVariant | NotInIndex":
        """Get the Variant associated with this Multiplier"""
        from core.types.managers.variant import RExVariantManager
        return RExVariantManager().get_one(lambda x: x.variant_id == self.variant_id, self.variant_id)

    def get_tier(self) -> "RExTier | NotInIndex":
        """Get the Tier associated with this Multiplier"""
        from core.types.managers.tier import RExTierManager
        return RExTierManager().get_one(lambda x: x.tier_id == self.tier_id, self.tier_id)

    def __eq__(self, other):
        return isinstance(other, RExMultiplier) and self.variant_id == other.variant_id and self.tier_id == other.tier_id

class RExMultiplierManager(RExManager[RExMultiplier]):
    @property
    def table_name(self) -> str:
        return "MULTIPLIERS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "VARIANT_ID", "TIER_ID", "MULTIPLIER_NUM"

    @property
    def primary_key(self) -> str:
        return "MULTIPLIER"

    @property
    def is_unique_index(self) -> bool:
        return True

    def parse_db_result(self, result: tuple[Any, ...]) -> RExMultiplier:
        return RExMultiplier(*result)

    def prepare_db_entry(self, item: RExMultiplier) -> dict[str, Any]:
        return {
            "VARIANT_ID": item.variant_id,
            "TIER_ID": item.tier_id,
            "MULTIPLIER_NUM": item.multiplier
        }