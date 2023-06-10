import asyncio
from logging import getLogger
from typing import TYPE_CHECKING

import discord

from kmibot.modules import Module

from .commands import FerryCommand

if TYPE_CHECKING:
    from kmibot.client import DiscordClient

LOGGER = getLogger(__name__)


class FerryModule(Module):
    def __init__(self, client: "DiscordClient") -> None:
        self.client = client
        client.tree.add_command(FerryCommand(client.config), guild=client.guild)

        if hasattr(client, "on_message"):
            raise RuntimeError(
                "Only one module can have on_message at the moment.",
            )
        else:
            client.on_message = self.on_message  # type: ignore[attr-defined]

    async def on_message(self, message: discord.Message) -> None:
        self.ferry_channel = self.client.get_channel(self.client.config.ferry.channel_id)
        assert isinstance(self.ferry_channel, discord.TextChannel)

        if self.client.config.ferry.banned_word in message.content:
            LOGGER.info(f"{message.author.display_name} ferried in #{message.channel}")
            for emoji in self.client.config.ferry.emoji_reacts:
                asyncio.create_task(message.add_reaction(emoji))

            await self.ferry_channel.send(
                f"<@{message.author.id}> ferried in <#{message.channel.id}>!",
            )
