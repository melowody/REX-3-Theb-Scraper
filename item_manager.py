import json
import os

def get_bot_token():
    print(type(os.getenv("BOT_TOKEN")))
    return os.getenv("BOT_TOKEN")

def get_auth_token():
    print(type(os.getenv("ZETEX_TOKEN")))
    return os.getenv("ZETEX_TOKEN")

def get_tracker_bots():
    with open("info.json", "r") as f:
        return json.load(f)['TRACKER_BOTS']

def get_color_names():
    with open("color_names.json", "r") as f:
        return json.load(f)

def get_theb_dict():
    with open("theb_names.json", "r") as f:
        return json.load(f)

def get_scoville_dict():
    with open("scoville_names.json", "r") as f:
        return json.load(f)
    
def get_gooberville_dict():
    with open("gooberville.json", "r") as f:
        return json.load(f)

def get_endless_dict():
    with open("endless.json", "r") as f:
        return json.load(f)

def get_refuge_dict():
    with open("refuge.json", "r") as f:
        return json.load(f)


def get_username(old_name, channel_id):
    if channel_id == 1:
        data = get_theb_dict()
    elif channel_id == 2:
        data = get_gooberville_dict()
    elif channel_id == 3:
        data = get_endless_dict()
    elif channel_id == 4:
        data = get_refuge_dict()
    else:
        data = get_scoville_dict()
    if old_name in data:
        return data[old_name]
    return old_name


def get_channel(channel):
    with open("info.json", "r") as f:
        return json.load(f)[channel]


def is_testing():
    with open("info.json", "r") as f:
        return json.load(f)['TESTING']
