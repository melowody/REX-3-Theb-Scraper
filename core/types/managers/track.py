"""
Implementation for tracks of players finding items.
"""

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from psycopg2 import sql

from core.types.manager import DBHolder, NotInIndex, delete
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

TRACK_ORDER = ("PLAYER_NAME", "VARIANT_ID", "ORE_ID", "CAVE_ID", 
               "WORLD_ID", "BLOCKS_MINED", "EVENT_ID", "EQUIP_IDS")


@dataclass
class RExTrack:
    """Information about an individual Track"""
    player_name: str
    """The name of the player who found the track 
    (Not using user_id as players not registered with the bot would break it)"""
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
        return RExPlayerManager().get_by(self.player_name)

    def get_variant(self) -> "RExVariant | NotInIndex | None":
        """Get the Ore Variant in this Track"""
        if self.variant_id is None:
            return None
        elif isinstance(self.variant_id, NotInIndex):
            return self.variant_id
        from core.types.managers.variant import RExVariantManager
        return RExVariantManager().get_by(self.variant_id)

    def get_ore(self) -> "RExOre | NotInIndex":
        """Get the Ore found in this Track"""
        if isinstance(self.ore_id, NotInIndex):
            return self.ore_id
        from core.types.managers.ore import RExOreManager
        return RExOreManager().get_by(self.ore_id)

    def get_cave(self) -> "RExCave | NotInIndex | None":
        """Get the Cave this Track was found in"""
        if self.cave_id is None:
            return None
        elif isinstance(self.cave_id, NotInIndex):
            return self.cave_id
        from core.types.managers.cave import RExCaveManager
        return RExCaveManager().get_by(self.cave_id)

    def get_world(self) -> "RExWorld | NotInIndex":
        """Get the World this Track was found in"""
        if isinstance(self.world_id, NotInIndex):
            return self.world_id
        from core.types.managers.world import RExWorldManager
        return RExWorldManager().get_by(self.world_id)

    def get_event(self) -> "RExEvent | NotInIndex | None":
        """Get the running Event during this Track"""
        if self.event_id is None:
            return None
        elif isinstance(self.event_id, NotInIndex):
            return self.event_id
        from core.types.managers.event import RExEventManager
        return RExEventManager().get_by(self.event_id)

    def get_equipment(self) -> "list[RExEquipment | NotInIndex]":
        """Get the Equipment this Track was found with"""
        from core.types.managers.equipment import RExEquipmentManager
        manager = RExEquipmentManager()
        out: list[RExEquipment | NotInIndex] = []
        for i in self.equip_ids:
            if isinstance(i, NotInIndex):
                out.append(i)
            else:
                out.append(manager.get_one(lambda x, eid=i: x.equip_id == eid, i))
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
            return layer_spawns[0]
        if isinstance(self.cave_id, NotInIndex):
            return self.cave_id

        cave_spawns = [i for i in spawns if i.cave_id == self.cave_id]
        if self.cave_id.startswith("gilded") and len(cave_spawns) == 0:
            if isinstance(self.ore_id, NotInIndex):
                return self.ore_id
            if isinstance(self.cave_id, NotInIndex):
                return self.cave_id
            if len(layer_spawns) == 0:
                return NotInIndex(f"{self.ore_id} (Layer)", RExSpawn)
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
        ore = self.get_ore()
        if isinstance(ore, NotInIndex):
            return ore
        print([vars(i) for i in ore.get_spawns()])
        if any(i.layer_id for i in ore.get_spawns()):
            rarity = spawn.rarity
        else:
            rarity = spawn.adjusted_rarity
        multiplier = self.get_multiplier()
        if isinstance(multiplier, NotInIndex):
            return multiplier
        if multiplier is None:
            return rarity
        if isinstance(rarity, NotInIndex):
            return rarity

        return rarity * multiplier.multiplier

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
        spawn = self.get_spawn()
        if isinstance(spawn, NotInIndex):
            return spawn
        rarity = spawn.adjusted_rarity
        if isinstance(rarity, NotInIndex):
            return rarity
        if isinstance(self.cave_id, NotInIndex):
            return self.cave_id
        if self.cave_id and self.cave_id.startswith("gilded") and ("57_leaf_clover" in self.equip_ids or "ambrosia_salad" in self.equip_ids):
            rarity /= 100
        multiplier = self.get_multiplier()
        if isinstance(multiplier, NotInIndex):
            return multiplier
        elif multiplier is None:
            return round(rarity)
        return round(rarity * multiplier.multiplier)

    def get_event_ore(self) -> "RExOre | NotInIndex | None":
        """Get the Ore associated with this Track's Event"""
        event = self.get_event()
        if event is None:
            return None
        if isinstance(event, NotInIndex):
            return event
        return event.get_ore()

    def __eq__(self, other):
        return isinstance(other,
                          RExTrack) and self.player_name == other.player_name and self.blocks_mined == other.blocks_mined


def parse_result(result: tuple[Any, ...]) -> RExTrack:
    """
    Parses a DB result into a RExTrack.

    Args:
        result (tuple[Any, ...]): The result from the DB.

    Returns:
        RExTrack: The parsed RExTrack.
    """
    return RExTrack(*result)


def prepare_track(track: RExTrack) -> dict[str, Any]:
    """
    Prepares a track to be sent to the DB

    Args:
        track (RExTrack): The track to prepare.

    Returns:
        dict[str, Any]: The key-value dictionary to send to the DB.
    """
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

def delete_track(player_name: str, blocks_mined: int):
    """
    Deletes a track based on the Player name and blocks mined.

    Args:
        player_name (str): The Player name.
        blocks_mined (int): The amount of Blocks mined.
    """
    delete("TRACKS", Selector("PLAYER_NAME", player_name, Comparator.EQUAL), Selector("BLOCKS_MINED", blocks_mined, Comparator.EQUAL))

class TrackHolder(DBHolder[RExTrack]):
    """Holder for Tracks"""

    @property
    def table_name(self) -> str:
        return "TRACKS"

    @property
    def key_order(self) -> tuple[str, ...]:
        return "PLAYER_NAME", "VARIANT_ID", "ORE_ID", "CAVE_ID", \
        "WORLD_ID", "BLOCKS_MINED", "EVENT_ID", "EQUIP_IDS"

    @property
    def primary_key(self) -> str:
        return "TRACK_KEY"

    @property
    def is_unique_index(self) -> bool:
        return True

    def parse_db_result(self, result: tuple[Any, ...]) -> RExTrack:
        return parse_result(result)

    def prepare_db_entry(self, item: RExTrack) -> dict[str, Any]:
        return prepare_track(item)

    def get_delete_keys(self, item: RExTrack) -> dict[str, Any]:
        return {
            "PLAYER_NAME": item.player_name,
            "BLOCKS_MINED": item.blocks_mined
        }

def save_track(track: RExTrack) -> None:
    """
    Save a track to the DB.

    Args:
        track (RExTrack): The track to save.
    """
    try:
        upsert([track], TrackHolder())
    except Exception as e: #pylint: disable=broad-except
        print(vars(track))
        print("Could not save Track!")
        print(e)


def track_query(limit: int | None, *selectors: Selector | sql.SQL) -> list[RExTrack]:
    """
    Get tracks from the DB

    Args:
        limit (int | None): The amount of tracks to limit the search to.
        *selectors (Selector | sql.SQL): The selectors to confine the search with.

    Returns:
        list[RExTrack]: The tracks retrieved from the query.
    """
    out: list[RExTrack] = []
    for track in query("TRACKS", TRACK_ORDER, list(selectors), limit=limit):
        out.append(parse_result(track))
    return out


def get_player_rarest(player: "RExPlayer", limit: int | None = 10) -> list[RExTrack]:
    return track_query(limit, Selector("PLAYER_NAME", player.player_name, Comparator.EQUAL))
