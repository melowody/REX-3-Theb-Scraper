from typing import Callable, Any, Coroutine, TypeVar

import discord
from discord import app_commands

from core.types.manager import NotInIndex

T = TypeVar("T")

def get_items(items: list[T], get_id: Callable[[Any], str], get_name: Callable[[Any], str], predicate: Callable[[discord.Interaction, T], bool] = lambda _, __: True) -> Callable[[discord.Interaction, str], Coroutine[None, None, list[app_commands.Choice[str]]]]:
    async def out(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=get_name(i), value=get_id(i))
            for i in items if predicate(interaction, i) and current.lower() in get_name(i).lower()
        ][:25]
    return out

def get_string(x: Any, to_str: Callable[[Any], str]) -> str:
    if isinstance(x, NotInIndex):
        return str(x)
    return to_str(x)