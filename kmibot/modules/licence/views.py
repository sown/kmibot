import asyncio
from typing import Optional

import discord

from kmibot.config import LicenceConfig, LicenceType


class LicenceSelector(discord.ui.Select):
    def __init__(self, licence_config: LicenceConfig, prompt: str) -> None:
        self._licence_config = licence_config
        self.prompt = prompt

        self.selected = asyncio.Event()
        self.pub: Optional[LicenceType] = None

        options = [
            discord.SelectOption(label=licence.name, emoji=licence.emoji)
            for licence in licence_config.licence_types
        ]

        super().__init__(
            placeholder="Select your HAM Radio Licence...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.licence = discord.utils.find(
            lambda p: p.name == self.values[0], self._licence_config.licence_types,
        )
        if self.licence:
            await interaction.response.edit_message(
                content=f"{self.prompt}\n {self.licence.emoji} {self.licence.name} has been selected",  # noqa: E501
                view=None,
            )
        self.selected.set()


class LicenceView(discord.ui.View):
    def __init__(self, licence_config: LicenceConfig, prompt: str) -> None:
        super().__init__()

        self.licence_selector = LicenceSelector(licence_config, prompt)
        self.add_item(self.licence_selector)

    async def wait_until_complete(self) -> LicenceType:
        await self.licence_selector.selected.wait()
        if self.licence_selector.licence is not None:
            return self.licence_selector.licence
        else:
            raise RuntimeError("No licence was selected.")
