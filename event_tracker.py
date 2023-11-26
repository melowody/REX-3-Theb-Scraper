import json
import logging

import zetex_jr

import random
import websocket
import socket_based
import item_manager
import threading
import os
import sys
import re
import queue
import traceback
import asyncio
from enum import Enum
from functools import total_ordering

class SpecialType(Enum):
    NONE = 0
    IONIZED = 1
    SPECTRAL = 2


class EventType(Enum):
    THEB = item_manager.get_channel("THEB_CHANNEL")
    GLOBAL = item_manager.get_channel("GLOBAL_CHANNEL")
    GLOBAL2 = item_manager.get_channel("GLOBAL2_CHANNEL")
    GLOBAL3 = item_manager.get_channel("GLOBAL3_CHANNEL")
    BEGINNER = item_manager.get_channel("BEGINNER_CHANNEL")
    BEGINNER2 = item_manager.get_channel("BEGINNER2_CHANNEL")
    TEST = item_manager.get_channel("TEST_CHANNEL")
    SCOVILLE = item_manager.get_channel("SCOVILLE_CHANNEL")
    MOMSONGAMING = item_manager.get_channel("MOMSONGAMING")
    GOOBERVILLE = item_manager.get_channel("GOOBERVILLE")
    ENDLESS = item_manager.get_channel("ENDLESS")
    REFUGE = item_manager.get_channel("REFUGE")
    THEMAGICMEDAL = item_manager.get_channel("THEMAGICMEDAL")
    REFUGEGLOBAL = item_manager.get_channel("REFUGEGLOBAL")


@total_ordering
class Rarity(Enum):
    UNKNOWN = 0
    RARE = 1
    MASTER = 2
    SURREAL = 3
    MYTHIC = 4
    EXOTIC = 5
    EXQUISITE = 6
    TRANSCENDENT = 7
    ENIGMATIC = 8
    UNFATHOMABLE = 9
    OTHERWORLDLY = 10
    ZENITH = 11
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    

class OreEvent:
    
    def __init__(self, event={}):
        self.print_username = {}
        self.event = None
        self.pickaxe = None
        self.blocks = None
        self.special = None
        self.rarity = None
        self.ore = None
        self.base_rarity = None
        self.username = None
        if event != {}:
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
        self.ore = self.ore.replace("*","")

        print("\nEVENT_TRACKER.PY\nTracking: " + self.username + " / " + self.ore)
        
        if "(" in self.__embed['title']:
            cave_type = self.__embed['title'][self.__embed['title'].index("("):].replace("*", "").replace("_","")
            self.ore += " " + cave_type
        
        color_names = item_manager.get_color_names()
        try:
            rarity_name = color_names[str(self.__embed['color'])]
            self.rarity = Rarity[rarity_name.upper()]
            print("Color: " + str(self.__embed['color']))
            print("Tier: " + rarity_name.upper())
        except Exception as err:
            self.rarity = Rarity.UNKNOWN
            zetex_jr.send_error("Color not listed in color_names.json: " + str(self.__embed['color']) + "\n" + traceback.format_exc())

        match (title_groups.group(2)):
            case "ionized":
                self.special = SpecialType.IONIZED
                print("Variant: Ionized")
            case "spectral":
                self.special = SpecialType.SPECTRAL
                print("Variant: Spectral")
            case _:
                self.special = SpecialType.NONE
                print("Variant: Normal")
        
        self.base_rarity = self.__embed["fields"][0]["value"].replace('1/', '')
        
        self.blocks = int(self.__embed["fields"][1]["value"].replace(',',''))
        
        self.pickaxe = self.__embed["fields"][2]["value"]
        
        self.event = self.__embed["fields"][3]["value"]
    
    def get_username(self):
        return self.username
    
    def get_ore(self):
        return self.ore
    
    def get_tier(self):
        return f"**{self.rarity.name.title()}** {('(' + self.special.name.title() + ')') if self.special != SpecialType.NONE else ''} {'@everyone' if self.should_ping_everyone() else ''}"

    def should_ping_everyone(self):
        return self.rarity.value + self.special.value >= 9

    def get_base_rarity(self):
        return "1 in " + self.base_rarity

    def get_blocks(self):
        return '{:,}'.format(self.blocks)
        
    def get_pickaxe(self):
        return self.pickaxe
        
    def get_event(self):
        return self.event
    
    def get_event_types(self) -> list[EventType]:
        out = []
        if item_manager.is_testing():
            self.print_username[EventType.TEST] = self.username
            out.append(EventType.TEST)
        if self.blocks < 100000:
            self.print_username[EventType.BEGINNER] = self.username
            self.print_username[EventType.BEGINNER2] = self.username
            print("Beginner (" + str(self.blocks) + " blocks)")
            out.append(EventType.BEGINNER)
            out.append(EventType.BEGINNER2)
        if self.should_ping_everyone():
            self.print_username[EventType.GLOBAL] = self.username
            out.append(EventType.GLOBAL)
            self.print_username[EventType.GLOBAL2] = self.username
            out.append(EventType.GLOBAL2)
            self.print_username[EventType.GLOBAL3] = self.username
            out.append(EventType.GLOBAL3)
        if self.username == 'MomSonGaming':
            self.print_username[EventType.MOMSONGAMING] = self.username + " (<@&1078460377920180276>)"
            print("is this still even used lol: " + self.username)
            out.append(EventType.MOMSONGAMING)
        if self.username == 'Lettyon26s':
            self.print_username[EventType.MOMSONGAMING] = self.username + " (Mother of <@&1078460377920180276>)"
            print("hi kenny mom: " + self.username)
            out.append(EventType.MOMSONGAMING)
        if self.username in item_manager.get_theb_dict().keys():
            print("Player is a Thebian: " + self.username)
            name = item_manager.get_username(self.username, 1)
            self.print_username[EventType.THEB] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
            out.append(EventType.THEB)
        if self.username in item_manager.get_gooberville_dict().keys():
            print("Player is a Goober: " + self.username)
            name = item_manager.get_username(self.username, 2)
            self.print_username[EventType.GOOBERVILLE] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
            out.append(EventType.GOOBERVILLE)
        if self.username in item_manager.get_refuge_dict().keys():
            print("Player is a Refugee: " + self.username)
            name = item_manager.get_username(self.username, 4)
            self.print_username[EventType.REFUGE] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
            out.append(EventType.REFUGE)
            if self.should_ping_everyone():
                self.print_username[EventType.REFUGEGLOBAL] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
                out.append(EventType.REFUGEGLOBAL)
        if self.username in item_manager.get_endless_dict().keys():
            print("Player is in Endless: " + self.username)
            name = item_manager.get_username(self.username, 3)
            self.print_username[EventType.ENDLESS] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
            out.append(EventType.ENDLESS)
        if self.username in item_manager.get_scoville_dict().keys():
            print("Player is a Scovillager: " + self.username)
            name = item_manager.get_username(self.username, 0)
            if self.username == "zetexfake" and self.rarity.value + self.special.value < 6:
                return out
            self.print_username[EventType.SCOVILLE] = f"{self.username}{' (' + name + ')' if name is not None else ''}"
            out.append(EventType.SCOVILLE)
        if self.username == "TheMagicMedal":
            self.print_username[EventType.THEMAGICMEDAL] = self.username
            out.append(EventType.THEMAGICMEDAL)
        return out
    
    def format(self, event_type: EventType):
        print("Formatting...")

        try:
            username = self.print_username[event_type]
            ore = self.get_ore()
            tier = self.get_tier()
            rarity = self.get_base_rarity()
            blocks = self.get_blocks()
            pickaxe = self.get_pickaxe()
            event = self.get_event()

            if "Ionized" in tier and not "Ionized" in ore:
                ore = "Ionized " + ore
            elif "Spectral" in tier and not "Spectral" in ore:
                ore = "Spectral " + ore

            adjusted_found = False
            event_found = False
            is_exclusive = False
            if "(" in ore and not "Gilded Cave" in ore:
                with open('adjusted.txt', 'r') as adjustedRarities:
                    cave_name = ore[ore.index("("):]
                    cave_name = cave_name.replace("(","").replace(" Cave)", "")
                    for num, line in enumerate(adjustedRarities):
                        if cave_name in line and not adjusted_found:
                            adjusted_found = True
                            if not "Caves" in rarity:
                                rarity += " in " + cave_name + " Caves"
                            cave_rarity = int(line.split()[-1])
                            print(cave_name + " Cave, 1 in " + str(cave_rarity))
                            rarity_num = rarity.replace("1 in ", "")
                            rarity_num = int(re.sub("[^0-9]", "", rarity_num))
                            adjusted_rarity = str('{:,}'.format(int(rarity_num * cave_rarity * 1.88)))
                            print("Adjusted rarity calculated: " + adjusted_rarity)
                            rarity += "\nAdjusted Rarity: 1 in " + adjusted_rarity
            elif 'Gilded Cave' in ore:
                adjusted_found = True
                gilded_adjust = rarity.replace("1 in ", "")
                gilded_adjust = re.sub("[^0-9]", "", gilded_adjust)
                if not "57 Leaf Clover" in pickaxe:
                    gilded_adjust += "00"
                    print("Gilded Cave, 1 in 5,700")
                else:
                    print("Gilded Cave, 1 in 57")
                gilded_adjust = int(gilded_adjust) * 1.88 * 57
                gilded_adjust = str('{:,}'.format(int(gilded_adjust)))
                print("Adjusted rarity calculated: " + gilded_adjust)
                if not "Caves" in rarity:
                    rarity += " in Gilded Caves"
                rarity += "\nAdjusted Rarity: 1 in " + gilded_adjust
            else:
                print("No adjustment for ore")

            if adjusted_found:
                with open('exclusive.txt', 'r') as exclusiveOres:
                    for num, line in enumerate(exclusiveOres):
                        if ore in line and not ' ' + ore in line and not is_exclusive:
                            is_exclusive = True
                            ore = ore.replace(")", " Exclusive)")

            if (event in ore or 'Protoflare' in ore) and not adjusted_found:
                with open('events.txt', 'r') as eventRarities:
                    for num, line in enumerate(eventRarities):
                        if ore in line and not (' ' + ore) in line and not event_found:
                            rarity += "\nEvent Rarity: 1 in " + line.split()[-1]
                            print("Event rarity added: 1 in " + line.split()[-1])
                            event_found = True
            else:
                print("No event for ore")

            tracker_name = ""
            match event_type:
                case EventType.MOMSONGAMING:
                    tracker_name = "MOMSONGAMING"
                case EventType.THEB:
                    tracker_name = "THEB"
                    if 'Hyperheated Quasar' in ore and '@everyone' not in tier and '57 Leaf Clover' not in pickaxe:
                        tier = tier + " @everyone"
                case EventType.GLOBAL:
                    tracker_name = "GLOBAL"
                    if 'Spectral' in tier and 'Unfathomable' in tier:
                        print("OH SHIT")
                    elif 'Spectral' in tier and 'Otherworldly' in tier:
                        print("OH REALLY SHIT")
                    elif 'Spectral' in tier and 'Zenith' in tier:
                        print("OH EXTREMELY SHIT")
                    else:
                        tier = tier.replace("@everyone", "")
                case EventType.GLOBAL2:
                    tracker_name = "GLOBAL"
                    if 'Spectral' in tier and 'Unfathomable' in tier:
                        print("OH SHIT")
                    elif 'Spectral' in tier and 'Otherworldly' in tier:
                        print("OH REALLY SHIT")
                    elif 'Spectral' in tier and 'Zenith' in tier:
                        print("OH EXTREMELY SHIT")
                    else:
                        tier = tier.replace("@everyone", "")
                    if random.randrange(1, 2) == 1:
                        ore = ore.replace("Inclemetite", "𝔞 𝔪𝔞𝔤𝔦𝔠 𝔴𝔞𝔫𝔡")
                    else:
                        ore = ore.replace("Inclemetite", "The Magic Medal")
                case EventType.GLOBAL3:
                    tracker_name = "GLOBAL"
                    tier = tier.replace("@everyone", "")
                case EventType.BEGINNER:
                    tracker_name = ":beginner:"
                    tier = tier.replace("@everyone", "<@&1090797544939999343>")
                case EventType.BEGINNER2:
                    tracker_name = ":beginner:"
                    tier = tier.replace("@everyone", "<@&1176823409364185139>")
                case EventType.GOOBERVILLE:
                    tracker_name = "GOOBERVILLE"
                    if random.randrange(1, 2) == 1:
                        ore = ore.replace("Inclemetite", "𝔞 𝔪𝔞𝔤𝔦𝔠 𝔴𝔞𝔫𝔡")
                    else:
                        ore = ore.replace("Inclemetite", "The Magic Medal")
                    ore = ore.replace("Ionized Acceleratium", "Sea Urchin Crystal")
                case EventType.TEST:
                    tracker_name = "TEST"
                    tier = tier.replace("@everyone", "Nuh Uh")
                case EventType.SCOVILLE:
                    tracker_name = "SCOVILLE"
                case EventType.THEMAGICMEDAL:
                    tracker_name = "THEMAGICMEDAL"
                case EventType.ENDLESS:
                    tracker_name = "ENDLESS"
                    tier = tier.replace("@everyone", "<@&1149541153465696320>")
                case EventType.REFUGE:
                    tracker_name = "REFUGE"
                    tier = tier.replace("@everyone", "")
                case EventType.REFUGEGLOBAL:
                    tracker_name = "REFUGE GLOBAL"
                    tier = tier.replace("@everyone", "<@&1165729194995626054>")
            print("Returning tracker message")
            return f"---------------------------------------------\n**[{tracker_name} TRACKER]**\n**{username}** has found **{ore}**\nTier: {tier}\nBase Rarity: {rarity}\nBlocks: {blocks}\nPickaxe: {pickaxe}\nEvent: {event}\n---------------------------------------------"
        except Exception as err:
            zetex_jr.send_error("Error in event_tracker.py with formatting!\n" + traceback.format_exc())
            return ("error occurred with formatting lmfao, if you're reading this someone probably fucked up doing /manual. if someone didn't, go scream at zetex to read this traceback: ```" + traceback.format_exc() + "```")
        
        
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
            except Exception:
                logging.info(json.dumps(event))
                zetex_jr.send_error("event_tracker.py loop error 1: " + traceback.format_exc())
                return
            try:
                if 'd' in event.keys() and type(event['d']) == dict and 'author' in event['d'].keys() and int(event['d']['author']['id']) in item_manager.get_tracker_bots() and 't' in event.keys() and event['t'] == 'MESSAGE_CREATE':
                    self.handle_event(event)
                op_code = event['op']
                if op_code == 11:
                    print('heartbeat received')
            except Exception:
                zetex_jr.send_error("event_tracker.py loop error 2: " + traceback.format_exc())
                pass

    def handle_event(self, event_data):
        self.queue.put(OreEvent(event_data))
