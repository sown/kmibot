import asyncio
from typing import Optional

import discord

from kmibot.config import PubConfig, PubInfo


class PubSelector(discord.ui.Select):
    def __init__(self, pub_config: PubConfig, prompt: str) -> None:
        self._pub_config = pub_config
        self.prompt = prompt

        self.selected = asyncio.Event()
        self.pub: Optional[PubInfo] = None

        options = [discord.SelectOption(label=pub.name, emoji=pub.emoji) for pub in pub_config.pubs]

        super().__init__(
            placeholder="Choose a pub...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.pub = self._pub_config.get_pub_by_name(self.values[0])
        if self.pub:
            await interaction.response.edit_message(
                content=f"{self.prompt}\n {self.pub.emoji} {self.pub.name} has been selected",  # noqa: E501
                view=None,
            )
        self.selected.set()


class PubView(discord.ui.View):
    def __init__(self, pub_config: PubConfig, prompt: str) -> None:
        super().__init__()

        self.pub_selector = PubSelector(pub_config, prompt)
        self.add_item(self.pub_selector)

    async def wait_until_complete(self) -> PubInfo:
        await self.pub_selector.selected.wait()
        if self.pub_selector.pub is not None:
            return self.pub_selector.pub
        else:
            raise RuntimeError("No pub was selected.")
