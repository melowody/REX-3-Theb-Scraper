"""
Miscellaneous utils for the Discord Bot
"""

import typing
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Callable, Any, Coroutine, TypeVar, Generic

from PIL import Image
import discord
import requests
from discord import app_commands, Interaction
from discord.ext import commands

from core.types.manager import NotInIndex
from core.types.managers.player import RExPlayer

T = TypeVar("T")
U = TypeVar("U")


def get_items(items: list[T], get_id: Callable[[T], str], get_name: Callable[[T], str],
              predicate: Callable[[discord.Interaction, T], bool] = lambda _, __: True,
              secondary: Callable[[T], str] = lambda _: "") -> Callable[
    [discord.Interaction, str], Coroutine[None, None, list[app_commands.Choice[str]]]]:
    """
    Gets a list of items, returning a function that gives the ID and Display String for the items.
    Use this in @app_commands.autocomplete.

    Args:
        items (list[T]): The list of items to parse.
        get_id (Callable[[T], str]): A lambda that gets the internal ID from an object.
        get_name (Callable[[T], str]): A lambda that gets the display name from an object;
        predicate (Callable[[discord.Interaction, T], bool], optional): A predicate to filter the items by.
        secondary (_type_, optional): A secondary display name for searching purposes (i.e. alternate Ore names)

    Returns:
        Callable[ [discord.Interaction, str], Coroutine[None, None, list[app_commands.Choice[str]]]]: The function to run into Discord's autocomplete.
    """
    async def out(interaction: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=get_name(i), value=get_id(i))
            for i in items if predicate(interaction, i) and (current.lower() in get_name(i).lower() or (
                    secondary is not None and current.lower() in secondary(i).lower()))
        ][:25]

    return out


def get_string(x: Any, to_str: Callable[[Any], str]) -> str:
    """
    Gets a string from an item if it's not NotInIndex.

    Args:
        x (Any): The item to stringify.
        to_str (Callable[[Any], str]): The lambda to convert it to a string.

    Returns:
        str: The string!!!
    """
    if isinstance(x, NotInIndex):
        return str(x)
    return to_str(x)


def get_avatar(player: RExPlayer) -> BytesIO:
    """
    Get a roblox player's avatar as a BytesIO string

    Args:
        player (RExPlayer): The RExPlayer

    Returns:
        BytesIO: The image as a BytesIO string.
    """
    id_endpoint = "https://users.roblox.com/v1/usernames/users"
    thumbnail_fmt = "https://thumbnails.roblox.com/v1/users/avatar?userIds={}&size=250x250&format=Png&isCircular=true"

    username = player.player_name

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    player_id_req = requests.post(id_endpoint, headers=headers,
                                  json={"usernames": [username], "excludeBannedUsers": False}, timeout=5)
    player_id = player_id_req.json()['data'][0]['id']

    thumbnail_req = requests.get(thumbnail_fmt.format(player_id), headers=headers, timeout=5)
    image_url = thumbnail_req.json()['data'][0]['imageUrl']

    image_req = requests.get(image_url, timeout=5)
    image = Image.open(BytesIO(image_req.content))

    width, height = image.size
    left, top, right, bottom = width / 4, 0, 3 * width / 4, height / 2
    cropped_image = image.crop((left, top, right, bottom))
    out_buf = BytesIO()
    cropped_image.save(out_buf, format='PNG')
    out_buf.seek(0)
    return out_buf


class Pagination(ABC, Generic[U], discord.ui.View):
    """
    A generic, abstract Pagination for creating page views of any list of items.
    """

    def __init__(self, items: list[U], context: commands.Context | discord.Interaction):
        self.message = None
        self.items = items
        self.index = 0
        self.context = context
        super().__init__(timeout=100)

    @property
    def total_pages(self) -> int:
        """
        Returns the number of pages in this pagination

        Returns:
            int: The number of pages
        """
        return len(self.items)

    @abstractmethod
    def to_page(self, item: U) -> tuple[discord.Embed, typing.Optional[discord.File]]:
        """
        Abstract method to turn a single item into a discord Page

        Args:
            item (U): The item to turn into a page

        Returns:
            tuple[discord.Embed, typing.Optional[discord.File]]: A tuple of the Embed, and a File if needed to send with
        """

    @abstractmethod
    def set_button_properties(self):
        """
        Sets the button's properties every time a page is put into view.
        """

    async def update(self, interaction: discord.Interaction):
        """
        Updates the embed.

        Args:
            interaction (discord.Interaction): The interaction that caused the update.
        """
        self.set_button_properties()
        embed, file = self.to_page(self.items[self.index])
        args: dict[str, Any] = {"embed": embed}
        if file:
            args["attachments"] = [file]
        await interaction.response.edit_message(**args, view=self)

    async def on_timeout(self) -> None:
        if self.message:
            await self.message.edit(view=None) # type: ignore

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        if interaction.user == (
        self.context.user if isinstance(self.context, discord.Interaction) else self.context.author):
            return True
        await interaction.response.send_message("You must be a user to use this command!", ephemeral=True)
        return False

    async def open(self):
        """
        Opens the view for the first time.
        """
        send_func = self.context.response.send_message if isinstance(self.context,
                                                                     discord.Interaction) else self.context.reply
        if len(self.items) < 1:
            await send_func(content="Nothing found with this criteria!", ephemeral=True)
            return

        embed, file = self.to_page(self.items[self.index])
        args: dict[str, Any] = {"embed": embed}
        if file:
            args["file"] = file

        if len(self.items) == 1:
            self.message = await send_func(**args)
        else:
            self.set_button_properties()
            self.message = await send_func(**args, view=self)
