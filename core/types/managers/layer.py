from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.world import RExWorld
    from core.types.managers.spawn import RExSpawn
    from core.types.managers.ore import RExOre


@dataclass
class RExLayer:
    """A dataclass for information about REx's Layers"""
    layer_id: str
    """The internal ID of the Layer in the local DB"""
    ore_id: str
    """The ID of the Ore this cave's walls are made of"""
    layer_name: str
    """The in-game name of the Layer"""
    world_id: str
    """The internal ID of the World this Layer is in"""
    min_depth: int
    """The depth the Layer starts at"""
    max_depth: int
    """The depth the Layer ends at"""

    def get_ore(self) -> "RExOre | NotInIndex":
        """Get the Ore this Layer's made of"""
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get_one(lambda x: x.ore_id == self.ore_id, self.ore_id)

    def get_world(self) -> "RExWorld | NotInIndex":
        """Get the World this Layer is in"""
        from core.types.managers.world import RExWorldManager
        return RExWorldManager().get_one(lambda x: x.world_id == self.world_id, self.world_id)

    def get_spawns(self) -> "list[RExSpawn]":
        """Get all the Spawns in this Layer"""
        from core.types.managers.spawn import RExSpawnManager
        return RExSpawnManager().get(lambda x: x.layer_id == self.layer_id)

    def __eq__(self, other):
        return other is RExLayer and self.layer_id == other.layer_id


class RExLayerManager(RExManager[RExLayer]):

    @property
    def table_name(self) -> str:
        return "LAYERS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "LAYER_ID", "ORE_ID", "LAYER_NAME", "WORLD_ID", "MIN_DEPTH", "MAX_DEPTH"

    @property
    def primary_key(self) -> str:
        return "LAYER_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExLayer:
        return RExLayer(*result)

    def prepare_db_entry(self, item: RExLayer) -> dict[str, Any]:
        return {
            "LAYER_ID": item.layer_id.lower(),
            "ORE_ID": item.ore_id.lower(),
            "LAYER_NAME": item.layer_name,
            "WORLD_ID": item.world_id.lower(),
            "MIN_DEPTH": item.min_depth,
            "MAX_DEPTH": item.max_depth
        }
