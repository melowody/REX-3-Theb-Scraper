from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.world import RExWorld
    from core.types.managers.ability import RExAbility
    from core.types.managers.recipe import RExRecipeStep

class RExEquipmentType(Enum):
    PICKAXE = "pickaxe"
    LEFT_HAND = "lhand"
    RIGHT_HAND = "rhand"
    MANUAL = "manual"
    ARTIFACT = "artifact"

@dataclass
class RExEquipment:
    """Information about Equipment items in REx"""
    equip_id: str
    """The internal ID of the Equipment"""
    equip_name: str
    """The in-game name of the Equipment"""
    equip_desc: str
    """The description of the Equipment"""
    equip_tier: int
    """The tier of the Equipment out of 10"""
    equip_type: RExEquipmentType
    """The type of the Equipment"""
    world_id: str | None
    """The internal ID of the world this Equipment is found int"""

    def get_world(self) -> "RExWorld | NotInIndex":
        """Get the World this Equipment is found in"""
        from core.types.managers.world import RExWorldManager
        return RExWorldManager().get_one(lambda x: x.world_id == self.world_id, self.world_id)

    def get_abilities(self) -> "list[RExAbility]":
        """Get the Abilities tied to this Equipment"""
        from core.types.managers.ability import RExAbilityManager
        return RExAbilityManager().get(lambda x: x.equip_id == self.equip_id)

    def get_recipe(self) -> "list[RExRecipeStep]":
        """Get the Recipe for this Equipment"""
        from core.types.managers.recipe import RExRecipeManager
        return RExRecipeManager().get(lambda x: x.equip_id == self.equip_id)

    def __eq__(self, other):
        return isinstance(other, RExEquipment) and self.equip_id == other.equip_id

class RExEquipmentManager(RExManager[RExEquipment]):
    @property
    def table_name(self) -> str:
        return "EQUIPMENT"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "EQUIP_ID", "EQUIP_NAME", "EQUIP_DESC", "EQUIP_TIER", "EQUIP_TYPE", "WORLD_ID"

    @property
    def primary_key(self) -> str:
        return "EQUIP_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExEquipment:
        return RExEquipment(result[0], result[1], result[2], result[3], RExEquipmentType(result[4]), result[5])

    def prepare_db_entry(self, item: RExEquipment) -> dict[str, Any]:
        return {
            "EQUIP_ID": item.equip_id,
            "EQUIP_NAME": item.equip_name,
            "EQUIP_DESC": item.equip_desc,
            "EQUIP_TIER": item.equip_tier,
            "EQUIP_TYPE": item.equip_type.value,
            "WORLD_ID": item.world_id
        }