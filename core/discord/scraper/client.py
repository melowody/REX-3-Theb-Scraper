import asyncio
import json
from threading import Thread
from typing import Any

from mypy.checker_shared import abstractmethod
from websockets import ClientConnection
from websockets.asyncio.client import connect

from abc import ABC

from asyncio import LifoQueue


class JsonSender(ABC):

    @abstractmethod
    def should_handle(self, event: dict) -> bool:
        pass

    @abstractmethod
    async def handle_event(self, event: dict, client: "DiscordClient"):
        pass


async def log_exceptions(awaitable) -> Any | None:
    try:
        return await awaitable
    except Exception as e:
        print(e)


class DiscordClient:
    socket: ClientConnection
    loop: asyncio.AbstractEventLoop
    thread = Thread

    read_queue: LifoQueue[dict]
    send_queue: LifoQueue[dict]

    senders: list[JsonSender]

    def __init__(self):
        from core.discord.scraper.senders.heartbeat import Heartbeat
        from core.discord.scraper.senders.scraper import RExScraper
        self.senders = [
            Heartbeat(),
            RExScraper()
        ]

    def start(self):
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self.start_impl, daemon=True)
        self.thread.start()

    def start_impl(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.connect_and_loop())
        self.loop.run_forever()

    async def connect_and_loop(self):
        self.socket = await connect("wss://gateway.discord.gg/?v=10&encoding=json")
        self.read_queue = LifoQueue()
        self.send_queue = LifoQueue()
        await asyncio.gather(
            log_exceptions(self.read_loop()),
            log_exceptions(self.process_loop()),
            log_exceptions(self.send_loop())
        )

    async def read_loop(self):
        while True:
            event = json.loads(await self.socket.recv())
            await self.read_queue.put(event)

    async def process_loop(self):
        while True:
            message = await self.read_queue.get()
            if message is None:
                continue
            for sender in self.senders:
                if sender.should_handle(message):
                    self.loop.create_task(log_exceptions(sender.handle_event(message, self)))

    async def send_loop(self):
        while True:
            event = await self.send_queue.get()
            await self.socket.send(json.dumps(event))
