"""
Implementation for handling Heartbeats to Discord.
"""

import json
import os
import random
from datetime import datetime
from typing import Callable, TypeVar

from core.discord.bot.util import get_string
from core.types.manager import NotInIndex
from core.types.managers.cave import RExCave
from core.types.managers.channel import RExTrackerType, RExChannelManager, RExChannel
from core.types.managers.equipment import RExEquipment
from core.types.managers.event import RExEvent
from core.types.managers.guild import RExGuild
from core.types.managers.ore import RExOre
from core.types.managers.player import RExPlayer
from core.types.managers.spawn import RExSpawn
from core.types.managers.tier import RExTier
from core.types.managers.track import RExTrack, save_track
from core.types.managers.variant import RExVariant
from main import ROOT_DIR

T = TypeVar("T")


def get_track_message() -> str:
    """
    Gets the tracker's message's format string for today

    Returns:
        str: The message format
    """
    date = datetime.today()
    with open(os.path.join(ROOT_DIR, "data", "holiday.json"), "r", encoding="utf8") as f:
        data = json.load(f)
        for i in data["holidays"]:
            if date.day == i["day"] and date.month == i["month"]:
                return '\n'.join(random.choice(i["messages"]))
        return '\n'.join(data["default"])


class RExDiscordTrackMessage:
    """
    A class outlining a tracker message
    """
    orig_track: RExTrack

    player: RExPlayer | str
    variant: RExVariant | NotInIndex | None
    ore: RExOre | NotInIndex
    cave: RExCave | NotInIndex | None
    loadout: list[RExEquipment | NotInIndex]
    event: RExEvent | NotInIndex | None
    blocks_mined: int

    tier: RExTier | NotInIndex
    spawn: RExSpawn | NotInIndex
    base_rarity: int | NotInIndex
    adjusted_rarity: int | NotInIndex
    event_ore: RExOre | NotInIndex | None

    pinged: bool = False

    def __init__(self, bot, track: RExTrack):
        self.bot = bot
        self.track = track
        self.parse_info(track)

    def get_ping_num(self) -> int:
        """
        Gets the current "rarity value" to check if it should ping everyone

        Returns:
            int: The "rarity value"
        """
        return (0 if isinstance(self.variant, NotInIndex) or self.variant is None else self.variant.variant_num) \
            + (0 if isinstance(self.tier, NotInIndex) else self.tier.tier_num)

    def parse_info(self, track: RExTrack) -> None:
        """
        Parses a track into the local variables to be used in the message function

        Args:
            track (RExTrack): The track to parse
        """

        player = track.get_player()
        if isinstance(player, NotInIndex):
            self.player = track.player_name
        else:
            self.player = player
        self.variant = track.get_variant()
        self.ore = track.get_ore()
        self.cave = track.get_cave()
        self.loadout = track.get_equipment()
        self.event = track.get_event()
        self.blocks_mined = track.blocks_mined

        self.tier = track.get_tier()
        self.spawn = track.get_spawn()
        self.base_rarity = track.get_base_rarity()
        self.adjusted_rarity = track.get_adjusted_rarity()
        self.event_ore = track.get_event_ore()

    async def send_messages(self) -> None:
        """
        Sends this track to the respective channels
        """
        if isinstance(self.player, RExPlayer):
            await self._send_player_messages()
        if self.blocks_mined < 10_000:
            await self._send_beginner_messages()
        if self.get_ping_num() >= 11:
            await self._send_global_messages()

    async def _send_player_messages(self) -> None:

        if not isinstance(self.player, RExPlayer):
            return

        channels = []
        for guild in self.player.get_guilds():
            channels += [i for i in guild.get_channels() if i.type == RExTrackerType.PLAYER]

        await self._send_track_messages(
            channels,
            11,
            lambda g, p=self.player: "" if g.guild_id != p.guild_id else f" <@{p.user_id}>"
            # type: ignore[union-attr]
        )

    async def _send_beginner_messages(self) -> None:

        await self._send_track_messages(
            RExChannelManager().get(lambda x: x.type == RExTrackerType.BEGINNER),
            11,
            lambda _: ""
        )

    async def _send_global_messages(self) -> None:

        await self._send_track_messages(
            RExChannelManager().get(lambda x: x.type == RExTrackerType.GLOBAL),
            13,
            lambda _: ""
        )

    async def _send_track_messages(self, channels: list[RExChannel], ping_threshold: int,
                                   player_ping: Callable[[RExGuild], str]) -> None:

        try:
            save_track(self.track)
        except Exception as e:
            print(vars(self.track))
            print("Could not save track!")
            print(e)

        to_ping = self.get_ping_num() >= ping_threshold

        for channel in channels:

            guild = channel.get_guild()
            if isinstance(guild, NotInIndex):
                continue

            ping_msg = "@everyone"
            if role := channel.get_ping_role():
                ping_msg = f"<@&{role.id}>"

            text_channel = channel.get_discord_channel()
            if text_channel is None:
                continue

            player = self.player
            if isinstance(player, RExPlayer):
                player = player.player_name

            await text_channel.send(get_track_message().format(
                guild=guild.guild_name.upper(),
                player=player,
                player_ping=player_ping(guild),
                variant=get_string(self.variant, lambda x: "" if x is None else f"{x.variant_name} "),
                ore=get_string(self.ore, lambda x: x.ore_name),
                cave=get_string(self.cave, lambda x: "" if x is None else f" ({x.cave_name})"),
                tier=get_string(self.tier, lambda x: x.tier_name),
                tier_variant=get_string(self.variant, lambda x: "" if x is None else f" ({x.variant_name})"),
                ping="" if not to_ping or self.pinged else f" {ping_msg}",
                base_rarity=get_string(self.base_rarity, lambda x: f"{x:,}"),
                adjusted_rarity=get_string(self.adjusted_rarity,
                                           lambda x: "" if x == self.base_rarity else f"\nAdjusted Rarity: 1 in {x:,}"),
                blocks=f"{self.blocks_mined:,}",
                loadout=", ".join([get_string(i, lambda x: x.equip_name) for i in self.loadout]),
                event=get_string(self.event_ore, lambda x: "None" if x is None else x.ore_name)
            ))

        self.pinged = to_ping or self.pinged
