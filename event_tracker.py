import websocket
import socket_based
import item_manager
import threading
import os
import sys
import re
import queue
from enum import Enum
from functools import total_ordering


class SpecialType(Enum):
    NONE = 0
    IONIZED = 1
    SPECTRAL = 2


class EventType(Enum):
    THEB = item_manager.get_channel("THEB_CHANNEL")
    GLOBAL = item_manager.get_channel("GLOBAL_CHANNEL")
    BEGINNER = item_manager.get_channel("BEGINNER_CHANNEL")
    ZETEX_SERVER = item_manager.get_channel("ZETEXSERVER")
    TEST = item_manager.get_channel("TEST_CHANNEL")
    SCOVILLE = item_manager.get_channel("SCOVILLE_CHANNEL")
    MOMSONGAMING = item_manager.get_channel("MOMSONGAMING")


@total_ordering
class Rarity(Enum):
    RARE = 1
    MASTER = 2
    SURREAL = 3
    MYTHIC = 4
    EXOTIC = 5
    TRANSCENDENT = 6
    ENIGMATIC = 7
    UNFATHOMABLE = 8
    ZENITH = 9
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    

class OreEvent:
    
    def __init__(self, event):
        self.print_username = {}
        self.event = None
        self.pickaxe = None
        self.blocks = None
        self.special = None
        self.rarity = None
        self.ore = None
        self.base_rarity = None
        self.username = None
        self.__embed = event['d']['embeds'][0]
        self.get_bases()
    
    def get_bases(self):
        title_groups = re.search(r"^\*\*(.+)\*\* has found(?: an? )?((?:spectral|ionized)?)\*\* (.+)\*\*", self.__embed['title'])
        
        self.username = title_groups.group(1)
        ore = f"{title_groups.group(2)} {title_groups.group(3)}"
        ore = ore.strip()
        if 'ionized' in ore or 'spectral' in ore:
            self.ore = ore[0].upper() + ore[1:]
        else:
            self.ore = ore
        
        self.rarity = None
        color_names = item_manager.get_color_names()
        rarity_name = color_names[str(self.__embed['color'])]
        self.rarity = Rarity[rarity_name.upper()]
            
        match (title_groups.group(2)):
            case "ionized":
                self.special = SpecialType.IONIZED
            case "spectral":
                self.special = SpecialType.SPECTRAL
            case _:
                self.special = SpecialType.NONE
        
        self.base_rarity = int(self.__embed["fields"][0]["value"].replace('1/', '').replace(',', ''))
        
        self.blocks = int(self.__embed["fields"][1]["value"].replace(',', ''))
        
        self.pickaxe = self.__embed["fields"][2]["value"]
        
        self.event = self.__embed["fields"][3]["value"]  
    
    def get_username(self):
        return self.username
    
    def get_ore(self):
        return self.ore
    
    def get_tier(self):
        return f"**{self.rarity.name.title()}** {('(' + self.special.name.title() + ')') if self.special != SpecialType.NONE else ''} {'@everyone' if self.should_ping_everyone() else ''}"

    def should_ping_everyone(self):
        return self.rarity.value + self.special.value >= 8

    def get_base_rarity(self):
        return "1 in " + '{:,}'.format(self.base_rarity)

    def get_blocks(self):
        return '{:,}'.format(self.blocks)
        
    def get_pickaxe(self):
        return self.pickaxe
        
    def get_event(self):
        return self.event
    
    def get_event_types(self) -> list[EventType]:
        out = []
        if item_manager.is_testing():
            out.append(EventType.TEST)
        if self.blocks < 100000:
            self.print_username[EventType.BEGINNER] = self.username
            print("Beginner: " + self.username)
            out.append(EventType.BEGINNER)
        if self.should_ping_everyone():
            self.print_username[EventType.GLOBAL] = self.username
            out.append(EventType.GLOBAL)
        if self.username in ' MomSonGaming ':
            self.print_username[EventType.MOMSONGAMING] = self.username + " (<@&1078460377920180276>)"
            print("MOMSONGAMING: " + self.username)
            out.append(EventType.MOMSONGAMING)
        if self.username in ' Lettyon26s ':
            self.print_username[EventType.MOMSONGAMING] = self.username + " (Mother of <@&1078460377920180276>)"
            print("MOMSONGAMING: " + self.username)
            out.append(EventType.MOMSONGAMING)
        if self.username in item_manager.get_zetex_dict().keys():
            print("ZETEXSERVER: " + self.username)
            name = item_manager.get_username(self.username, 0)
            self.print_username[EventType.ZETEX_SERVER] = f"{self.username} {'(' + name + ')' if name is not None else ''}"
            out.append(EventType.ZETEX_SERVER)
        if self.username in item_manager.get_theb_dict().keys():
            print("THEB: " + self.username)
            name = item_manager.get_username(self.username, 1)
            self.print_username[EventType.THEB] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
            out.append(EventType.THEB)
        if self.username in item_manager.get_scoville_dict().keys():
            print("SCOVILLE: " + self.username)
            name = item_manager.get_username(self.username, 2)
            self.print_username[EventType.SCOVILLE] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
            out.append(EventType.SCOVILLE)
        return out
    
    def format(self, event_type: EventType):
        try:
            username = self.print_username[event_type]
            ore = self.get_ore()
            tier = self.get_tier()
            rarity = self.get_base_rarity()
            blocks = self.get_blocks()
            pickaxe = self.get_pickaxe()
            event = self.get_event()

            adjusted_found = False
            event_found = False
            with open('adjusted.txt', 'r') as adjustedRarities:
                for num, line in enumerate(adjustedRarities):
                    if ore in line and not (' ' + ore) in line and not adjusted_found:
                        rarity += "\nAdjusted Rarity: 1 in " + line.split()[-1]
                        adjusted_found = True
            if event in ore or 'Protoflare' in ore:
                with open('events.txt', 'r') as eventRarities:
                    for num, line in enumerate(eventRarities):
                        if ore in line and not (' ' + ore) in line and not event_found:
                            rarity += "\nEvent Rarity: 1 in " + line.split()[-1]
                            event_found = True
            if 'Hyperheated Quasar' in ore:
                if '57' in pickaxe:
                    if 'Ionized' in ore:
                        rarity += "\nAdjusted Rarity: 1 in 3,471,984,000"
                    elif 'Spectral' in ore:
                        rarity += "\nAdjusted Rarity: 1 in 52,079,760,000"
                    else:
                        rarity += "\nAdjusted Rarity: 1 in 86,799,600"
                else:
                    if 'Ionized' in ore:
                        rarity += "\nAdjusted Rarity: 1 in 347,198,400,000"
                    elif 'Spectral' in ore:
                        rarity += "\nAdjusted Rarity: 1 in 5,207,976,000,000"
                    else:
                        rarity += "\nAdjusted Rarity: 1 in 8,679,960,000"
            
            tracker_name = ""
            match event_type:
                case EventType.MOMSONGAMING:
                    tracker_name = "MOMSONGAMING"
                case EventType.THEB:
                    tracker_name = "THEB"
                case EventType.GLOBAL:
                    tracker_name = "GLOBAL"
                    if 'Spectral' in tier and 'Unfathomable' in tier:
                        print("OH SHIT")
                    else:
                        tier = tier.replace("@everyone", "")
                case EventType.BEGINNER:
                    tracker_name = ":beginner:"
                case EventType.ZETEX_SERVER:
                    tracker_name = "ZETEX REALM"
                    tier = tier.replace("@everyone", "")
                case EventType.TEST:
                    tracker_name = "TEST"
                case EventType.SCOVILLE:
                    tracker_name = "SCOVILLE"
            return f"---------------------------------------------\n**[{tracker_name} TRACKER]**\n**{username}** has found **{ore}**\nTier: {tier}\nBase Rarity: {rarity}\nBlocks: {blocks}\nPickaxe: {pickaxe}\nEvent: {event}\n---------------------------------------------"
        except Exception as e:
            print(f"format error: {e}")
        
        
class EventTracker(socket_based.SocketBased):
    
    def __init__(self, socket: websocket.WebSocket):
        super().__init__(socket)
        self.main_thread = None
        self.queue = queue.LifoQueue()
        self.tracks = 0
    
    def start(self):
        token = item_manager.get_auth_token()
        payload = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": 'pc'
                }
            }
        }
        self.send_json_request(payload)
        
        self.main_thread = threading.Thread(target=EventTracker.loop, args=(self,))
        self.main_thread.start()
    
    def loop(self):
        while True:
            try:
                event = self.receive_json_response()
            except Exception as err:
                # SHITTY FIX ALERT
                print(f"et loop error 1: {err}")
                os.execl(sys.executable, 'python', "main.py")
                return
            try:
                if 'd' in event.keys() and 'author' in event['d'].keys() and int(event['d']['author']['id']) in item_manager.get_tracker_bots():
                    self.handle_event(event)
                op_code = event['op']
                if op_code == 11:
                    print('heartbeat received')
            except Exception as e:
                print(f"et loop error 2: {e}")
                pass

    def handle_event(self, event_data):
        self.queue.put(OreEvent(event_data))
