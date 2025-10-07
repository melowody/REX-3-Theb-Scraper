import asyncio
import json
from abc import ABC, abstractmethod
from threading import Thread
from typing import Any

from websocket import WebSocket

from core.types.meta import SingletonABCMeta


class JsonRunner(ABC, metaclass=SingletonABCMeta):
    """An abstract class for json-based threaded objects
    that run for the duration of the program"""

    _socket: WebSocket
    _thread: Thread

    def ensure_socket(self, socket: WebSocket):
        self._socket = socket

    @abstractmethod
    async def loop(self) -> None:
        """The main loop of the program, ran in a while True
        automatically, so do not put it in your implementation!"""
        pass

    @abstractmethod
    def pre_start(self) -> None:
        """Anything that needs to be done prior to the object starting the loop"""
        pass

    async def _loop_impl(self) -> None:
        """The private implementation of the loop"""
        while True:
            await self.loop()

    def start(self):
        """Starts the threaded loop"""
        self.pre_start()

        def create_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.create_task(self._loop_impl())
            loop.run_forever()

        self._thread = Thread(target=create_loop, daemon=True)
        self._thread.start()

    def send_json_request(self, request: Any) -> None:
        """Sends a JSON request with the encoded package via the websocket

        Args:
            request (Any): The object to encode with JSON and send"""
        self._socket.send(json.dumps(request))

    def receive_json_response(self) -> Any | None:
        """Receives a JSON response from the websocket

        Returns:
            Any | None: The response from the websocket, decoded from JSON"""
        response = self._socket.recv()
        if response:
            return json.loads(response)
        return None