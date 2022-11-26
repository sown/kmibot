from abc import ABCMeta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kmibot.client import DiscordClient


class Module(metaclass=ABCMeta):
    def __init__(self, client: "DiscordClient") -> None:
        pass

    async def on_ready(self, client: "DiscordClient") -> None:
        pass
