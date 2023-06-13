from typing import TYPE_CHECKING, Union

import discord

if TYPE_CHECKING:
    from . import FerryModule


class AccuseModal(discord.ui.Modal):

    evidence = discord.ui.TextInput(  # type: ignore[var-annotated]
        label='Quote as Evidence of Ferrying',
        style=discord.TextStyle.paragraph,
        placeholder="I like trains",
        required=True,
    )

    def __init__(self, module: "FerryModule", *, criminal: Union[discord.User, discord.Member]) -> None:
        self.module = module
        self.criminal = criminal
        title = f"Accuse {criminal.display_name} of Ferrying"
        super().__init__(title=title)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.module.command_group.publish_accusation(  # type: ignore[has-type]
            self.criminal,
            interaction.user,
            quote=self.evidence,
        )
        await interaction.response.send_message("ok", ephemeral=True)
