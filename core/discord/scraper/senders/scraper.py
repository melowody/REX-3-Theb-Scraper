import re

from core.discord.scraper.client import JsonSender
from asyncio import LifoQueue

from typing import TYPE_CHECKING

from core.types.manager import NotInIndex
from core.types.managers.cave import RExCaveManager, RExCave
from core.types.managers.equipment import RExEquipment, RExEquipmentManager
from core.types.managers.event import RExEvent, RExEventManager
from core.types.managers.ore import RExOreManager, RExOre
from core.types.managers.track import RExTrack
from core.types.managers.tracker import RExTrackerManager
from core.types.managers.variant import RExVariantManager, RExVariant
from core.types.managers.world import RExWorldManager, RExWorld

if TYPE_CHECKING:
    from core.discord.scraper.client import DiscordClient


def parse_event(event: dict) -> RExTrack | None:
    """
    Parse a find's message event into a RExTrack

    Args:
    event (dict): The event object sent by Discord

    Returns:
    RExTrack: The RExTrack parsed from the event
    """

    # Regex group the title of the official embed
    title_groups = re.search(
        r"^\*\*(.+?)\*\* has found (?:an? (spectral|ionized) )?\*\*(.+?)\*\*(?: \(\*(.+?)\*\))?$", event["title"])
    if title_groups is None:
        return None

    # Extract all the constituent parts
    player_name = title_groups.group(1)

    variant_text = title_groups.group(2)
    variant = None if variant_text is None else RExVariantManager().get_one(
        lambda x: x.variant_name.lower() == variant_text.lower(), variant_text)

    ore_text = title_groups.group(3)
    ore = RExOreManager().get_one(lambda x: x.ore_name.lower() == ore_text.lower(), ore_text)

    world_text = event.get("description", "None")
    world = RExWorldManager().get_one(lambda x: x.world_name.lower() == world_text.lower(), world_text)

    cave_text = title_groups.group(4)
    if cave_text == "Gilded Cave":
        match world_text:
            case "Natura":
                cave_text = "Gilded Cave (W1)"
            case "Caverna":
                cave_text = "Gilded Cave (W2)"
            case "Digita":
                cave_text = "Gilded Cave (W0)"
            case "Luna Refuge":
                cave_text = "Gilded Cave (SW1)"
            case "Aesteria":
                cave_text = "Gilded Cave (SW2)"
            case "Lucernia":
                cave_text = "Gilded Cave (SW3)"
    cave = None if cave_text is None else RExCaveManager().get_one(lambda x: x.cave_name.lower() == cave_text.lower(),
                                                                   cave_text)

    blocks_mined: int = -1
    curr_event: RExEvent | NotInIndex | None = None
    equipment: list[RExEquipment] = []
    for field in event.get("fields", []):
        if field.get("name") == "Blocks Mined":
            blocks_mined = int(field.get("value").replace(",", ""))
        elif field.get("name") == "Event" and (value := field.get("value")) != "None":
            curr_event_ore = RExOreManager().get_one(lambda x: x.ore_name.lower() == value.lower(), value)
            if isinstance(curr_event_ore, NotInIndex):
                curr_event = curr_event_ore
            else:
                curr_event = RExEventManager().get_one(lambda x: x.ore_id.lower() == curr_event_ore.ore_id.lower(),
                                                       curr_event_ore.ore_id)
        elif field.get("name") == "Loadout" and field.get("value"):
            for i in field.get("value").split(", "):
                if isinstance(equip := RExEquipmentManager().get_one(lambda x: x.equip_name.lower() == i.lower(), i),
                              RExEquipment):
                    equipment.append(equip)

    out = RExTrack(
        player_name,
        variant if not isinstance(variant, RExVariant) else variant.variant_id,
        ore if not isinstance(ore, RExOre) else ore.ore_id,
        cave if not isinstance(cave, RExCave) else cave.cave_id,
        world if not isinstance(world, RExWorld) else world.world_id,
        blocks_mined,
        curr_event if not isinstance(curr_event, RExEvent) else curr_event.ore_id,
        [i if not isinstance(i, RExEquipment) else i.equip_id for i in equipment]
    )

    print(vars(out))

    return out


class RExScraper(JsonSender):
    track_queue: LifoQueue[RExTrack] = LifoQueue()

    def should_handle(self, event: dict) -> bool:
        if event is None:
            return False
        if event.get('t') != "MESSAGE_CREATE":
            return False
        data: dict | None = event.get("d")
        if data is None:
            return False
        author = data.get("author")
        if author is None:
            return False
        author_id = author.get("id")
        if author_id is None:
            return False
        return RExTrackerManager().exists(lambda x: x.tracker_id == int(author_id))

    async def handle_event(self, event: dict, _: "DiscordClient"):
        for embed in event["d"]["embeds"]:
            await self.track_queue.put(parse_event(embed))
