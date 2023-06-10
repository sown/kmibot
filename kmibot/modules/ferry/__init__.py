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
        self.command_group = FerryCommand(client.config, self)
        client.tree.add_command(self.command_group, guild=client.guild)

        if hasattr(client, "on_message"):
            raise RuntimeError(
                "Only one module can have on_message at the moment.",
            )
        else:
            client.on_message = self.on_message  # type: ignore[attr-defined]

        if hasattr(client, "on_reaction_add"):
            raise RuntimeError(
                "Only one module can have on_reaction_add at the moment.",
            )
        else:
            client.on_reaction_add = self.on_reaction_add  # type: ignore[attr-defined]

    @property
    def announce_channel(self) -> discord.TextChannel:
        announce_channel = self.client.get_channel(self.client.config.ferry.announcement_channel_id)
        assert isinstance(announce_channel, discord.TextChannel)
        return announce_channel

    @property
    def accuse_channel(self) -> discord.TextChannel:
        accuse_channel = self.client.get_channel(self.client.config.ferry.accusation_channel_id)
        assert isinstance(accuse_channel, discord.TextChannel)
        return accuse_channel

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        await self.command_group.handle_emoji(reaction, user)

    async def on_message(self, message: discord.Message) -> None:
        if message.author != self.client.user and self.client.config.ferry.banned_word in message.content:
            LOGGER.info(f"{message.author.display_name} ferried in #{message.channel}")
            for emoji in self.client.config.ferry.emoji_reacts:
                asyncio.create_task(message.add_reaction(emoji))

            await self.announce_channel.send(
                f"<@{message.author.id}> ferried in <#{message.channel.id}>!",
            )
