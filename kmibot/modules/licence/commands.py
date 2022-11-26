from logging import getLogger
from typing import Optional

import discord
from discord.app_commands import Group, command

from kmibot.config import BotConfig, LicenceType

LOGGER = getLogger(__name__)


class LicenceCommand(Group):

    def __init__(self, config: BotConfig) -> None:
        super().__init__(name="licence", description="Manage your HAM radio licence")
        self.config = config

    def _get_licence(self, member: discord.Member) -> Optional[LicenceType]:
        roles = {role.name: role for role in member.roles}
        for licence in self.config.licence.licence_types:
            if licence.role and licence.role.name in roles:
                return licence
        return None

    @command(description="Get information about your HAM radio licence.")
    async def info(self, interaction: discord.Interaction):
        LOGGER.info(f"{interaction.user} used /licence info")
        assert isinstance(interaction.user, discord.Member)

        if licence := self._get_licence(interaction.user):
            await interaction.response.send_message(
                f"You have a {licence.emoji} {licence.name} {licence.emoji} licence.\n"
                "If this is wrong, you can change it using /licence set",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "You do not have a HAM Radio Licence set.\n"
                "Use /licence set to set it.",
                ephemeral=True,
            )
