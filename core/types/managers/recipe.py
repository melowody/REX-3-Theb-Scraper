from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.equipment import RExEquipment
    from core.types.managers.ore import RExOre

@dataclass
class RExRecipeStep:
    """Information about a specific step in an Equipment's Recipe"""
    equip_id: str
    """The internal ID of the Equipment"""
    ore_id: str
    """The internal ID of the Ore"""
    count: int
    """The number of the Ore required"""

    def get_equipment(self) -> "RExEquipment | NotInIndex":
        """Get the Equipment this Recipe is for"""
        from core.types.managers.equipment import RExEquipmentManager
        return RExEquipmentManager().get_one(lambda x: x.equip_id == self.equip_id, self.equip_id)

    def get_ore(self) -> "RExOre | NotInIndex":
        """Get the Ore this Recipe uses"""
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get_one(lambda x: x.ore_id == self.ore_id, self.ore_id)

    def __eq__(self, other):
        return isinstance(other, RExRecipeStep) and self.equip_id == other.equip_id and self.ore_id == other.ore_id

class RExRecipeManager(RExManager[RExRecipeStep]):
    @property
    def table_name(self) -> str:
        return "RECIPES"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "EQUIP_ID", "ORE_ID", "COUNT"

    @property
    def primary_key(self) -> str:
        return "RECIPE_STEP"

    def is_unique_index(self) -> bool:
        return True

    def parse_db_result(self, result: tuple[Any, ...]) -> RExRecipeStep:
        return RExRecipeStep(*result)

    def prepare_db_entry(self, item: RExRecipeStep) -> dict[str, Any]:
        return {
            "equip_id": item.equip_id,
            "ore_id": item.ore_id,
            "count": item.count
        }