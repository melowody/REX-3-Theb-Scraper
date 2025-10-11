import math
import traceback
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

import core.types.manager
from core.types.manager import NotInIndex
from core.types.manager import upsert, query, Selector, Comparator
from core.types.managers.spawn import RExSpawn

if TYPE_CHECKING:
    from core.types.managers.player import RExPlayer
    from core.types.managers.variant import RExVariant
    from core.types.managers.ore import RExOre
    from core.types.managers.cave import RExCave
    from core.types.managers.world import RExWorld
    from core.types.managers.event import RExEvent
    from core.types.managers.equipment import RExEquipment
    from core.types.managers.multiplier import RExMultiplier
    from core.types.managers.tier import RExTier

TRACK_ORDER = ("PLAYER_NAME", "VARIANT_ID", "ORE_ID", "CAVE_ID", "WORLD_ID", "BLOCKS_MINED", "EVENT_ID", "EQUIP_IDS")

@dataclass
class RExTrack:
    """Information about an individual Track"""
    player_name: str
    """The name of the player who found the track (Not using user_id as players not registered with the bot would break it)"""
    variant_id: str | NotInIndex | None
    """The ID of the track's Variant, if there is one"""
    ore_id: str | NotInIndex
    """The ID of the found Ore"""
    cave_id: str | NotInIndex | None
    """The ID of the Cave the Ore was found in, if there is one"""
    world_id: str | NotInIndex
    """The ID of the World the Ore was found in"""
    blocks_mined: int
    """The amount of blocks mined before finding this Ore"""
    event_id: str | NotInIndex | None
    """The ongoing Event when this Ore was found"""
    equip_ids: list[str | NotInIndex]
    """The Equipment the Player had on them when the Ore was found"""

    def get_player(self) -> "RExPlayer | NotInIndex":
        """Get the Player who found this Track"""
        from core.types.managers.player import RExPlayerManager
        return RExPlayerManager().get_one(lambda x: x.player_name == self.player_name, self.player_name)

    def get_variant(self) -> "RExVariant | NotInIndex | None":
        """Get the Ore Variant in this Track"""
        if self.variant_id is None:
            return None
        elif isinstance(self.variant_id, NotInIndex):
            return self.variant_id
        from core.types.managers.variant import RExVariantManager
        return RExVariantManager().get_one(lambda x: x.variant_id == self.variant_id, self.variant_id)

    def get_ore(self) -> "RExOre | NotInIndex":
        """Get the Ore found in this Track"""
        if isinstance(self.ore_id, NotInIndex):
            return self.ore_id
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get_one(lambda x: x.ore_id == self.ore_id, self.ore_id)

    def get_cave(self) -> "RExCave | NotInIndex | None":
        """Get the Cave this Track was found in"""
        if self.cave_id is None:
            return None
        elif isinstance(self.cave_id, NotInIndex):
            return self.cave_id
        from core.types.managers.cave import RExCaveManager
        return RExCaveManager().get_one(lambda x: x.cave_id == self.cave_id, self.cave_id)

    def get_world(self) -> "RExWorld | NotInIndex":
        """Get the World this Track was found in"""
        if isinstance(self.world_id, NotInIndex):
            return self.world_id
        from core.types.managers.world import RExWorldManager
        return RExWorldManager().get_one(lambda x: x.world_id == self.world_id, self.world_id)

    def get_event(self) -> "RExEvent | NotInIndex | None":
        """Get the running Event during this Track"""
        if self.event_id is None:
            return None
        elif isinstance(self.event_id, NotInIndex):
            return self.event_id
        from core.types.managers.event import RExEventManager
        return RExEventManager().get_one(lambda x: x.ore_id == self.event_id, self.event_id)

    def get_equipment(self) -> "list[RExEquipment | NotInIndex]":
        """Get the Equipment this Track was found with"""
        from core.types.managers.equipment import RExEquipmentManager
        manager = RExEquipmentManager()
        out: list[RExEquipment | NotInIndex] = []
        for i in self.equip_ids:
            if isinstance(i, NotInIndex):
                out.append(i)
            else:
                out.append(manager.get_one(lambda x: x.equip_id == i, i))
        return out

    def get_tier(self) -> "RExTier | NotInIndex":
        """Get the tier of ore in this Track"""
        ore = self.get_ore()
        if isinstance(ore, NotInIndex):
            return ore
        return ore.get_tier()

    def get_spawn(self) -> "RExSpawn | NotInIndex":
        """Get the Spawn corresponding to this Track"""
        ore = self.get_ore()
        if isinstance(ore, NotInIndex):
            return ore

        spawns = ore.get_spawns()
        layer_spawns = [i for i in spawns if i.cave_id is None]
        if self.cave_id is None:
            if len(layer_spawns) == 0:
                return NotInIndex(self.ore_id, RExSpawn)
            else:
                return layer_spawns[0]

        cave_spawns = [i for i in spawns if i.cave_id == self.cave_id]
        if self.cave_id == "gilded" and len(cave_spawns) == 0:
            if isinstance(self.ore_id, NotInIndex):
                return self.ore_id
            if isinstance(self.cave_id, NotInIndex):
                return self.cave_id
            if len(layer_spawns) == 0:
                return NotInIndex(f"{self.ore_id} (Layer)", RExSpawn)
            else:
                cave_spawns.append(RExSpawn(
                    self.ore_id,
                    None,
                    self.cave_id,
                    int(layer_spawns[0].rarity * 2.5)
                ))
        if len(cave_spawns) == 0:
            return NotInIndex(self.ore_id, RExSpawn)
        return cave_spawns[0]

    def get_base_rarity(self) -> "int | NotInIndex":
        """Get the base rarity of this Track"""
        spawn = self.get_spawn()
        if isinstance(spawn, NotInIndex):
            return spawn

        rarity = spawn.rarity

        multiplier = self.get_multiplier()
        if isinstance(multiplier, NotInIndex):
            return multiplier
        elif multiplier is None:
            return rarity

        return spawn.rarity * multiplier.multiplier

    def get_multiplier(self) -> "RExMultiplier | NotInIndex | None":
        """Get the multiplier for this Track"""
        variant = self.get_variant()
        if isinstance(variant, NotInIndex):
            return variant
        elif variant is None:
            return None
        tier = self.get_tier()
        if isinstance(tier, NotInIndex):
            return tier
        return variant.get_multiplier(tier)

    def get_adjusted_rarity(self) -> "int | NotInIndex":
        """Get the adjusted rarity of this Track"""
        base_rarity = self.get_base_rarity()
        cave = self.get_cave()
        if isinstance(cave, NotInIndex):
            return cave
        elif cave is None:
            return base_rarity
        return math.ceil(base_rarity * 1.88 * cave.cave_rarity)

    def get_event_ore(self) -> "RExOre | NotInIndex | None":
        """Get the Ore associated with this Track's Event"""
        event = self.get_event()
        if event is None:
            return None
        elif isinstance(event, NotInIndex):
            return event
        return event.get_ore()

    def __eq__(self, other):
        return isinstance(other, RExTrack) and self.player_name == other.player_name and self.blocks_mined == other.blocks_mined

def parse_result(result: tuple[Any, ...]) -> RExTrack:
    return RExTrack(*result)


def prepare_track(track: RExTrack) -> dict[str, Any]:
    return {
        "PLAYER_NAME": track.player_name,
        "VARIANT_ID": track.variant_id,
        "ORE_ID": track.ore_id,
        "CAVE_ID": track.cave_id,
        "WORLD_ID": track.world_id,
        "BLOCKS_MINED": track.blocks_mined,
        "EVENT_ID": track.event_id,
        "EQUIP_IDS": track.equip_ids
    }


def save_track(track: RExTrack) -> None:
    try:
        upsert([track], "TRACKS", "TRACK_KEY", prepare_track, is_unique_index=True)
    except Exception:
        print(vars(track))
        print("Could not save Track!")
        traceback.print_exc()

def track_query(table_name: str, limit: int, *selectors: Selector) -> list[RExTrack]:
    out: list[RExTrack] = []
    for track in query(table_name, TRACK_ORDER, list(selectors), limit=limit):
        out.append(parse_result(track))
    return out

def get_player_rarest(player: "RExPlayer", limit: int = 10) -> list[RExTrack]:
    return track_query("TRACKS", limit, Selector("PLAYER_NAME", player.player_name, Comparator.EQUAL))