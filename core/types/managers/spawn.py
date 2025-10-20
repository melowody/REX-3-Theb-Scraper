"""
Implementation for where Ores can spawn in REx.
"""

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.ore import RExOre
    from core.types.managers.layer import RExLayer
    from core.types.managers.cave import RExCave


@dataclass
class RExSpawn:
    """A dataclass for information about REx's Spawns"""
    ore_id: str
    """The internal ID of the Ore this Spawn concerns"""
    layer_id: str | None
    """The internal ID of the Layer this Spawn concerns (can be none)"""
    cave_id: str | None
    """The internal ID of the Cave this Spawn concerns (can be none)"""
    rarity: int
    """The rarity of this Spawn in its respective Layer/Cave"""

    def get_ore(self) -> "RExOre | NotInIndex":
        """Get the Ore this Spawn concerns"""
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get_by(self.ore_id)

    def get_location(self) -> "RExLayer | RExCave | NotInIndex | None":
        """Get the location of this Spawn"""
        from core.types.managers.layer import RExLayerManager
        from core.types.managers.cave import RExCaveManager
        if self.layer_id is None:
            return RExCaveManager().get_by(self.cave_id)
        return RExLayerManager().get_by(self.layer_id)

    @property
    def adjusted_rarity(self) -> "int | NotInIndex":
        """The adjusted rarity of this Spawn"""
        from core.types.managers.cave import RExCaveManager
        if not self.cave_id:
            return self.rarity
        cave = RExCaveManager().get_by(self.cave_id)
        if isinstance(cave, NotInIndex):
            return cave
        return round(cave.cave_rarity * 1.88 * self.rarity)

    def __eq__(self, other):
        return isinstance(other,
                          RExSpawn) and self.ore_id == other.ore_id and self.layer_id == other.layer_id and self.cave_id == other.cave_id


class RExSpawnManager(RExManager[RExSpawn, tuple[str, str | None, str | None]]):
    def _get_by_impl(self, value: tuple[str, str | None, str | None]) -> RExSpawn | NotInIndex:
        return self.get_one(lambda x: x.ore_id == value[0] and (not value[1] or x.layer_id == value[1]) and (not value[2] or x.cave_id == value[2]), value)

    def get_delete_keys(self, item: RExSpawn) -> dict[str, Any]:
        return {
            "ORE_ID": item.ore_id,
            "LAYER_ID": item.layer_id,
            "CAVE_ID": item.cave_id
        }

    @property
    def table_name(self) -> str:
        return "SPAWNS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "ORE_ID", "LAYER_ID", "CAVE_ID", "RARITY"

    @property
    def primary_key(self) -> str:
        return "ORE_SPAWN"

    @property
    def is_unique_index(self) -> bool:
        return True

    def parse_db_result(self, result: tuple[Any, ...]) -> RExSpawn:
        return RExSpawn(*result)

    def prepare_db_entry(self, item: RExSpawn) -> dict[str, Any]:
        return {
            "ORE_ID": item.ore_id,
            "LAYER_ID": item.layer_id,
            "CAVE_ID": item.cave_id,
            "RARITY": item.rarity
        }
