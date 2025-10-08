import os
import re
import traceback
from asyncio import LifoQueue

from core.discord.scraper.runner import JsonRunner
from core.types.manager import NotInIndex
from core.types.managers.cave import RExCaveManager, RExCave
from core.types.managers.equipment import RExEquipment, RExEquipmentManager
from core.types.managers.event import RExEventManager, RExEvent
from core.types.managers.ore import RExOreManager, RExOre
from core.types.managers.track import RExTrack, save_track
from core.types.managers.tracker import RExTrackerManager
from core.types.managers.variant import RExVariantManager, RExVariant
from core.types.managers.world import RExWorldManager, RExWorld


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
    variant = None if variant_text is None else RExVariantManager().get_one(lambda x: x.variant_name.lower() == variant_text.lower(), variant_text)

    ore_text = title_groups.group(3)
    ore = RExOreManager().get_one(lambda x: x.ore_name.lower() == ore_text.lower(), ore_text)

    cave_text = title_groups.group(4)
    cave = None if cave_text is None else RExCaveManager().get_one(lambda x: x.cave_name.lower() == cave_text.lower(), cave_text)

    world_text = event.get("description", "None")
    world = RExWorldManager().get_one(lambda x: x.world_name.lower() == world_text.lower(), world_text)

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
                curr_event = RExEventManager().get_one(lambda x: x.ore_id.lower() == curr_event_ore.ore_id.lower(), curr_event_ore.ore_id)
        elif field.get("name") == "Loadout" and field.get("value"):
            for i in field.get("value").split(", "):
                if isinstance(equip := RExEquipmentManager().get_one(lambda x: x.equip_name.lower() == i.lower(), i), RExEquipment):
                    equipment.append(equip)

    return RExTrack(
        player_name,
        variant if not isinstance(variant, RExVariant) else variant.variant_id,
        ore if not isinstance(ore, RExOre) else ore.ore_id,
        cave if not isinstance(cave, RExCave) else cave.cave_id,
        world if not isinstance(world, RExWorld) else world.world_id,
        blocks_mined,
        curr_event if not isinstance(curr_event, RExEvent) else curr_event.ore_id,
        [i if not isinstance(i, RExEquipment) else i.equip_id for i in equipment]
    )


class RExTrackerScraper(JsonRunner):

    queue: LifoQueue[RExTrack]

    def __init__(self):
        super().__init__()
        self.queue = LifoQueue()

    def pre_start(self) -> None:

        # Send the initial heartbeat to get the expected per-heartbeat time
        token = os.environ.get("SCRAPER_TOKEN")
        payload = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                }
            }
        }
        self.send_json_request(payload)

    async def loop(self) -> None:

        event: dict | None = None
        try:
            event = self.receive_json_response()
        except Exception as e:
            # TODO: Get better exception list
            print("Error in getting track list")
            print(type(e), traceback.format_exc())

        # Get the author ID of the message, and discard any non-message events
        if event is None:
            return
        if event.get('t') != "MESSAGE_CREATE":
            return
        data: dict | None = event.get("d")
        if data is None:
            return
        author = data.get("author")
        if author is None:
            return
        author_id = author.get("id")
        if author_id is None:
            return

        # Check if the author is one of the official trackers
        if not RExTrackerManager().exists(lambda x: x.tracker_id == int(author_id)):
            return

        # Parse and send the find in the respective channels
        try:
            for embed in data.get("embeds", []):
                await self.handle_event(embed)
                pass
        except Exception as e:
            # TODO: Get better Exception list
            print("Could not handle track event!")
            print(type(e), traceback.format_exc())

    async def handle_event(self, event: dict) -> None:
        """Handle a valid event, parsing and sending it to the correct channels

        Args:
            event (dict): The event object sent by Discord
        """
        track = parse_event(event)
        if track:
            try:
                save_track(track)
            except Exception:
                print(vars(track))
            await self.queue.put(track)