from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from core.types.manager import RExManager, NotInIndex


if TYPE_CHECKING:
    from core.types.managers.equipment import RExEquipment

@dataclass
class RExAbility:
    """Information about an Equipment's Ability"""
    ability_id: str
    """The internal ID of the Ability"""
    equip_id: str
    """The ID of the Equipment this Ability belongs to"""
    ability_name: str
    """The name of the Ability"""
    ability_desc: str
    """The in-game description of the Ability"""
    ability_rate: int
    """The rate at which the Ability procs"""
    ability_luck: str | None
    """The luck boost of the Ability"""
    ability_lifespan: str | None
    """The lifespan of the Ability"""
    ability_area: str | None
    """The area the Ability affects"""
    ability_amount: str | None
    """The amount of Ability effects"""
    ability_pinned_luck: str | None
    """The luck boost on pinned Ores"""

    def get_equipment(self) -> "RExEquipment | NotInIndex":
        """Get the associated Equipment"""
        from core.types.managers.equipment import RExEquipmentManager
        return RExEquipmentManager().get_one(lambda x: x.equip_id == self.equip_id, self.equip_id)

    def __eq__(self, other):
        return isinstance(other, RExAbility) and self.ability_name == other.ability_name

class RExAbilityManager(RExManager[RExAbility]):
    @property
    def table_name(self) -> str:
        return "ABILITIES"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "ABILITY_ID", "EQUIP_ID", "ABILITY_NAME", "ABILITY_DESC", "ABILITY_RATE", "ABILITY_LUCK", "ABILITY_LIFESPAN", "ABILITY_AREA", "ABILITY_AMOUNT", "ABILITY_PINNED_LUCK"

    @property
    def primary_key(self) -> str:
        return "ABILITY_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExAbility:
        return RExAbility(*result)

    def prepare_db_entry(self, item: RExAbility) -> dict[str, Any]:
        return {
            "ABILITY_ID": item.ability_id,
            "EQUIP_ID": item.equip_id,
            "ABILITY_NAME": item.ability_name,
            "ABILITY_DESC": item.ability_desc,
            "ABILITY_RATE": item.ability_rate,
            "ABILITY_LUCK": item.ability_luck,
            "ABILITY_LIFESPAN": item.ability_lifespan,
            "ABILITY_AREA": item.ability_area,
            "ABILITY_AMOUNT": item.ability_amount,
            "ABILITY_PINNED_LUCK": item.ability_pinned_luck
        }