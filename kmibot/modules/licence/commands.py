from logging import getLogger
from typing import Optional

import discord
from discord.app_commands import Group, command

from kmibot.config import BotConfig, LicenceType

from .views import LicenceView

LOGGER = getLogger(__name__)


class LicenceCommand(Group):

    def __init__(self, config: BotConfig) -> None:
        super().__init__(name="licence", description="Manage your HAM radio licence")
        self.config = config

    async def _choose_licence(
        self, interaction: discord.Interaction, prompt: str,
    ) -> LicenceType:
        view = LicenceView(self.config.licence, prompt)
        await interaction.response.send_message(
            prompt,
            view=view,
            ephemeral=True,
        )
        return await view.wait_until_complete()

    def _get_licence(self, member: discord.Member) -> Optional[LicenceType]:
        roles = {role.name: role for role in member.roles}
        for licence in self.config.licence.licence_types:
            if licence.role and licence.role.name in roles:
                return licence
        return None

    async def _set_licence(
        self,
        member: discord.Member,
        licence: Optional[LicenceType],
    ) -> None:
        if self._get_licence(member) is licence:
            LOGGER.info(f"Licence is already set to {licence}")
        else:
            roles = {role.name: role for role in member.guild.roles}
            all_licence_roles = [
                roles[licence.role.name]
                for licence in self.config.licence.licence_types
                if licence.role
            ]
            await member.remove_roles(*all_licence_roles)
            if licence and licence.role:
                await member.add_roles(roles[licence.role.name])

    @command(description="Get information about your HAM radio licence.")  # type: ignore[arg-type]
    async def info(self, interaction: discord.Interaction) -> None:
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

    @command(description="Set your HAM radio licence.")  # type: ignore[arg-type]
    async def set(self, interaction: discord.Interaction) -> None:  # noqa: A003
        LOGGER.info(f"{interaction.user} used /licence set")
        assert isinstance(interaction.user, discord.Member)

        licence = await self._choose_licence(
            interaction,
            "Please select your HAM radio licence.",
        )
        LOGGER.info(f"{licence.name} selected.")
        await self._set_licence(interaction.user, licence)
