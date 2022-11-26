from logging import getLogger
from typing import TYPE_CHECKING

from discord import Colour

from ..module import Module
from .commands import LicenceCommand

if TYPE_CHECKING:
    from kmibot.client import DiscordClient

LOGGER = getLogger(__name__)


class LicenceModule(Module):
    def __init__(self, client: "DiscordClient") -> None:
        client.tree.add_command(LicenceCommand(client.config), guild=client.guild)
        pass

    async def on_ready(self, client: "DiscordClient") -> None:
        guild = client.get_guild(client.guild.id)
        assert guild is not None

        LOGGER.info("Setting up licence roles.")
        roles = {role.name: role for role in guild.roles}
        for licence in client.config.licence.licence_types:
            if licence.role is not None and licence.role.name not in roles:
                LOGGER.info(f"Setting up {licence.name} licence role")
                await guild.create_role(
                    name=licence.role.name,
                    colour=Colour.from_str(licence.role.colour),
                    reason="Added missing HAM Radio Licence Role",
                )
