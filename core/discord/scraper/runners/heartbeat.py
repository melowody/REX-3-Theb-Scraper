import time
import datetime
from random import random

from core.discord.scraper.runner import JsonRunner


class Heartbeat(JsonRunner):
    """The JsonRunner meant for keeping the scraping bot online via Discord's heartbeat system"""

    interval: float
    """The interval between heartbeats Discord asks for"""

    def pre_start(self):
        # Connect to the discord websocket server, and request the desired heartbeat interval
        self._socket.connect("wss://gateway.discord.gg/?v=10&encoding=json")
        event = self.receive_json_response()
        self.interval = event['d']['heartbeat_interval'] / 1000
        print(f"Interval: {self.interval}")

    async def loop(self) -> None:
        # Add a bit of jitter to the heartbeats to not be too direct
        jitter = random()
        print(f"Current Time: {datetime.datetime.now(datetime.UTC).strftime('%H:%M:%S.%f')} | Waiting {self.interval * jitter + .1} seconds until next heartbeat!")
        time.sleep(self.interval * jitter + .1)
        heartbeat_json = {
            "op": 1,
            "d": "null"
        }

        # Send the heartbeat to Discord
        try:
            self.send_json_request(heartbeat_json)
        except Exception as e:
            print("Could not keep heartbeat up!")
            print(type(e), e)
            # TODO: Restart program instead and get better except catchers
            exit()
