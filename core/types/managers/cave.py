"""
Implementation for REx's Caves.
"""

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.world import RExWorld
    from core.types.managers.spawn import RExSpawn
    from core.types.managers.ore import RExOre


@dataclass
class RExCave:
    """A dataclass for information about REx's Caves"""
    cave_id: str
    """The ID of the cave in the local DB"""
    ore_id: str
    """The ID of the Ore this cave's walls are made of"""
    cave_name: str
    """The name of the cave in-game"""
    world_id: str
    """The internal ID of the World this Cave is in"""
    cave_rarity: int
    """The rarity of the cave when a cave is generated in-game"""

    def get_world(self) -> "RExWorld | NotInIndex":
        """Get the world this Cave is in"""
        from core.types.managers.world import RExWorldManager
        return RExWorldManager().get_by(self.world_id)

    def get_spawns(self) -> "list[RExSpawn]":
        """Get the Spawns in this Cave"""
        from core.types.managers.spawn import RExSpawnManager
        return RExSpawnManager().get(lambda x: x.cave_id == self.cave_id)

    def get_ore(self) -> "RExOre | NotInIndex":
        """Get the Ore this Cave is made of"""
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get_by(self.ore_id)

    def __eq__(self, other):
        return isinstance(other, RExCave) and self.cave_id == other.cave_id


class RExCaveManager(RExManager[RExCave, str]):

    def _get_by_impl(self, value: str) -> RExCave | NotInIndex:
        return self.get_one(lambda x: x.cave_id == value, value)

    def get_delete_keys(self, item: RExCave) -> dict[str, Any]:
        return {
            "CAVE_ID": item.cave_id
        }

    @property
    def table_name(self) -> str:
        return "CAVES"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "CAVE_ID", "ORE_ID", "CAVE_NAME", "WORLD_ID", "CAVE_RARITY"

    @property
    def primary_key(self) -> str:
        return "CAVE_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExCave:
        return RExCave(*result)

    def prepare_db_entry(self, item: RExCave) -> dict[str, Any]:
        return {
            "CAVE_ID": item.cave_id,
            "ORE_ID": item.ore_id,
            "CAVE_NAME": item.cave_name,
            "WORLD_ID": item.world_id,
            "CAVE_RARITY": item.cave_rarity
        }
