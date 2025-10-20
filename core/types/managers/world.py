"""
Definitions for REx Worlds
"""

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.cave import RExCave
    from core.types.managers.layer import RExLayer
    from core.types.managers.spawn import RExSpawn


@dataclass
class RExWorld:
    """A dataclass for information about REx's Worlds"""
    world_id: str
    """The ID of the World in the local DB"""
    world_name: str
    """The in-game name of the World"""
    world_desc: str
    """The in-game description of the World"""

    def get_caves(self) -> "list[RExCave]":
        """Get all Caves in this World"""
        from core.types.managers.cave import RExCaveManager
        return RExCaveManager().get(lambda x: x.world_id == self.world_id)

    def get_layers(self) -> "list[RExLayer]":
        """Get all Layers in this World"""
        from core.types.managers.layer import RExLayerManager
        return RExLayerManager().get(lambda x: x.world_id == self.world_id)

    def get_spawns(self) -> "list[RExSpawn]":
        """Get all Spawns in this World"""
        from core.types.managers.spawn import RExSpawnManager
        layers = [i.layer_id for i in self.get_layers()]
        return RExSpawnManager().get(lambda x: x.layer_id in layers)

    def __eq__(self, other):
        return isinstance(other, RExWorld) and self.world_id == other.world_id


class RExWorldManager(RExManager[RExWorld, str]):
    def _get_by_impl(self, value: str) -> RExWorld | NotInIndex:
        return self.get_one(lambda x: x.world_id == value, value)

    def get_delete_keys(self, item: RExWorld) -> dict[str, Any]:
        return {
            "WORLD_ID": item.world_id
        }

    @property
    def table_name(self) -> str:
        return "WORLDS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "WORLD_ID", "WORLD_NAME", "WORLD_DESC"

    @property
    def primary_key(self) -> str:
        return "WORLD_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExWorld:
        return RExWorld(*result)

    def prepare_db_entry(self, item: RExWorld) -> dict[str, Any]:
        return {
            "WORLD_ID": item.world_id,
            "WORLD_NAME": item.world_name,
            "WORLD_DESC": item.world_desc
        }
