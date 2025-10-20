"""
Implementation for the scraper client.
"""

import asyncio
import json
import os
from threading import Thread
from typing import Any, Callable, Awaitable, Concatenate, ParamSpec
from abc import ABC, abstractmethod
from asyncio import LifoQueue

import aiohttp
from websockets import ClientConnection
from websockets.asyncio.client import connect
from core.types.managers.track import RExTrack
from core.types.managers.tracker import RExTrackerManager
from core.types.meta import SingletonMeta


class JsonSender(ABC):
    """
    This class implements handling for different opcodes or events received by Discord.
    """

    @abstractmethod
    def should_handle(self, event: dict) -> bool:
        """
        Checks whether this JsonSender should be handling this event.

        Args:
            event (dict): The event sent by Discord.

        Returns:
            bool: Whether to handle the event or not.
        """

    @abstractmethod
    async def handle_event(self, event: dict, client: "DiscordClient"):
        """
        Handles the Discord event.

        Args:
            event (dict): The event sent by Discord.
            client (DiscordClient): The client handling the event.
        """


async def log_exceptions(awaitable) -> Any | None:
    """
    Prints any exceptions from coroutines so they don't get lost to space and time.

    Args:
        awaitable (_type_): The coroutine to await.

    Returns:
        Any | None: Whatever the coroutine returns.
    """
    try:
        return await awaitable
    except Exception as e:  # pylint: disable=broad-except
        print(e)


async def _get_player_tracks(callback: Callable[[list[RExTrack]], Awaitable[Any]], player_name: str):
    """
    Gets a player's tracks from the REx Discord and sends them to the callback.

    Args:
        callback (Callable[[list[RExTrack]], Awaitable[Any]]): The callback to send the tracks to.
        player_name (str): The player name to scrape the tracks by.
    """
    from core.discord.scraper.senders.scraper import parse_event
    search_fmt = "https://discord.com/api/v9/guilds/708116714256072715/messages/search?{webhooks}&content={username}&sort_by=timestamp&sort_order=desc&offset={offset}"

    trackers = RExTrackerManager().get_all()

    index = 0
    token = os.environ.get("SCRAPER_TOKEN")
    if not token:
        return
    headers = {"Authorization": token}
    out = []

    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            search_url = search_fmt.format(webhooks="&" \
                .join(f"webhook_id={i.tracker_id}" for i in trackers),
                username=player_name, offset=index)

            async with session.get(search_url) as search_req:
                if search_req.status == 429:
                    remaining = search_req.headers["Retry-After"]
                    await asyncio.sleep(float(remaining) * 2)
                    continue
                search_req.raise_for_status()
                search_req = await search_req.json()

            search_results = search_req.get("messages", [])
            if not search_results:
                break
            messages = search_results

            for message in messages:
                for sub_message in message:
                    for embed in sub_message.get("embeds", []):
                        track = parse_event(embed)
                        out.append(track)

            index += len(messages)
            if index >= search_req.get("total_results", 0):
                break

            await asyncio.sleep(1)

    await callback(out)

P = ParamSpec("P")


class DiscordClient(metaclass=SingletonMeta):
    """
    The main Discord Client for scraping tracks.
    """
    socket: ClientConnection
    loop: asyncio.AbstractEventLoop
    thread = Thread
    tasks: set[asyncio.Task] = set()

    read_queue: LifoQueue[dict]
    send_queue: LifoQueue[dict]

    senders: list[JsonSender]

    def __init__(self):
        from core.discord.scraper.senders.heartbeat import Heartbeat
        from core.discord.scraper.senders.scraper import RExScraper
        from core.discord.scraper.senders.reconnect import Reconnect
        self.senders = [
            Heartbeat(),
            RExScraper(),
            Reconnect()
        ]

    def start(self):
        """
        Starts the scraping loops.
        """
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._start_impl, daemon=True)
        self.thread.start()

    def _start_impl(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.connect_and_loop())
        self.loop.run_forever()

    def _run_async_func(self,
                        async_func: Callable[Concatenate[Callable[..., Awaitable[Any]], P], Awaitable[Any]],
                        callback: Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
        coro = log_exceptions(async_func(callback, *args, **kwargs))
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def get_player_tracks(self, player_name: str, callback: Callable[..., Awaitable[Any]]):
        """
        Get a player's tracks on a different thread and send them to the callback.

        Args:
            player_name (str): The player's name.
            callback (Callable[..., Awaitable[Any]]): The callback to send the tracks to.
        """
        self._run_async_func(_get_player_tracks, callback, player_name)

    async def connect_and_loop(self):
        """
        Connects to Discord's websocket and starts the three loops.
        """
        self.socket = await connect("wss://gateway.discord.gg/?v=10&encoding=json")
        self.read_queue = LifoQueue()
        self.send_queue = LifoQueue()

        read_task = self.loop.create_task(log_exceptions(self.read_loop()))
        process_task = self.loop.create_task(
            log_exceptions(self.process_loop()))
        send_task = self.loop.create_task(log_exceptions(self.send_loop()))

        self.tasks.add(read_task)
        self.tasks.add(process_task)
        self.tasks.add(send_task)

        await asyncio.wait([read_task, process_task, send_task])

        self.tasks.clear()

    async def read_loop(self):
        """
        Reads events from Discord to be processed by process_loop.
        """
        while True:
            event = json.loads(await self.socket.recv())
            await self.read_queue.put(event)

    async def process_loop(self):
        """
        Processes Discord events and puts any events to send back in the send_queue.
        """
        while True:
            message = await self.read_queue.get()
            if message is None:
                continue
            for sender in self.senders:
                if sender.should_handle(message):
                    self.loop.create_task(log_exceptions(
                        sender.handle_event(message, self)))

    async def send_loop(self):
        """
        Reads the send_queue and sends any events received to Discord.
        """
        while True:
            event = await self.send_queue.get()
            await self.socket.send(json.dumps(event))
