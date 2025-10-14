from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from core.types.manager import NotInIndex
from core.types.manager import RExManager

if TYPE_CHECKING:
    from core.types.managers.tier import RExTier
    from core.types.managers.multiplier import RExMultiplier


@dataclass
class RExVariant:
    """A dataclass for information about REx's Ore Variants"""
    variant_id: str
    """The internal ID of the Variant"""
    variant_name: str
    """The in-game name of the Variant"""
    variant_num: int
    """The index of the Variant from most to least common"""

    def get_multiplier(self, tier: "RExTier") -> "RExMultiplier | NotInIndex":
        """Gets the Multiplier based off a given Tier"""
        from core.types.managers.multiplier import RExMultiplierManager
        return RExMultiplierManager().get_one(lambda x: x.variant_id == self.variant_id and x.tier_id == tier.tier_id,
                                              f"{self.variant_num} + {tier.tier_id}")

    def __eq__(self, other):
        return isinstance(other, RExVariant) and self.variant_id == other.variant_id


class RExVariantManager(RExManager[RExVariant]):
    @property
    def table_name(self) -> str:
        return "VARIANTS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "VARIANT_ID", "VARIANT_NAME", "VARIANT_NUM"

    @property
    def primary_key(self) -> str:
        return "VARIANT_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExVariant:
        return RExVariant(*result)

    def prepare_db_entry(self, item: RExVariant) -> dict[str, Any]:
        return {
            "VARIANT_ID": item.variant_id,
            "VARIANT_NAME": item.variant_name,
            "VARIANT_NUM": item.variant_num
        }
