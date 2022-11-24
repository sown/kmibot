from typing import TYPE_CHECKING

from ..module import Module
from .commands import PubCommand

if TYPE_CHECKING:
    from bot.client import DiscordClient


class PubModule(Module):
    def __init__(self, client: "DiscordClient") -> None:
        client.tree.add_command(PubCommand(client.config), guild=client.guild)
