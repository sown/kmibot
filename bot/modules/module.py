from abc import ABCMeta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.client import DiscordClient


class Module(metaclass=ABCMeta):
    def __init__(self, client: "DiscordClient") -> None:
        pass
