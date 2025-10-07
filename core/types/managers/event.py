from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from core.types.manager import RExManager, NotInIndex

if TYPE_CHECKING:
    from core.types.managers.ore import RExOre
    from core.types.managers.world import RExWorld


@dataclass
class RExEvent:
    """Information about the in-game Events"""
    ore_id: str
    """The ID of the Ore this event is tied to"""
    world_id: str
    """The ID of the World this event is in"""
    event_text: str
    """The in-game message displayed with the Ore"""
    event_desc: str
    """A description of what the event does"""
    ore_rarity: int
    """The nerfed rarity of the primary Ore"""
    event_duration: int
    """The duration of the event, in seconds"""
    event_chance: int
    """The weighted chance of the Event every second no event is active"""

    def get_ore(self) -> "RExOre | NotInIndex":
        """Get the primary Ore associated with this Event"""
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get_one(lambda x: x.ore_id == self.ore_id, self.ore_id)

    def get_world(self) -> "RExWorld | NotInIndex":
        """Get the world this Event is in"""
        from core.types.managers.world import RExWorldManager
        return RExWorldManager().get_one(lambda x: x.world_id == self.world_id, self.world_id)

    def __eq__(self, other):
        return isinstance(other, RExEvent) and self.ore_id == other.ore_id

class RExEventManager(RExManager[RExEvent]):
    @property
    def table_name(self) -> str:
        return "EVENTS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "ORE_ID", "WORLD_ID", "EVENT_TEXT", "EVENT_DESC", "ORE_RARITY", "EVENT_DURATION", "EVENT_CHANCE"

    @property
    def primary_key(self) -> str:
        return "ORE_ID"

    def parse_db_result(self, result: tuple[Any, ...]) -> RExEvent:
        return RExEvent(*result)

    def prepare_db_entry(self, item: RExEvent) -> dict[str, Any]:
        return {
            "ORE_ID": item.ore_id,
            "WORLD_ID": item.world_id,
            "EVENT_TEXT": item.event_text,
            "EVENT_DESC": item.event_desc,
            "ORE_RARITY": item.ore_rarity,
            "EVENT_DURATION": item.event_duration,
            "EVENT_CHANCE": item.event_chance
        }