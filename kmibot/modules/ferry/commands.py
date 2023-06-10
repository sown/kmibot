from logging import getLogger
from typing import Optional

import discord
from discord.app_commands import Group, command, describe

from kmibot.config import BotConfig

LOGGER = getLogger(__name__)


class FerryCommand(Group):

    def __init__(self, config: BotConfig) -> None:
        super().__init__(name="ferry", description="Interact with ferries.")
        self.config = config

    @command(description="Accuse somebody of ferrying.")  # type: ignore[arg-type]
    @describe(member="The criminal you are accusing.", quote="A quote as evidence of the crime.")
    async def accuse(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        quote: Optional[str] = None,
    ) -> None:
        LOGGER.info(f"{interaction.user} used /ferry accuse")
        lines = [
            f"{member.mention} has been accused by {interaction.user.mention}",
        ]
        if quote:
            lines.extend(["", f"> {quote}"])
        await interaction.response.send_message("\n".join(lines))
