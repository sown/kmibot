import logging
from typing import TYPE_CHECKING

import discord
from discord import EventStatus

from ..module import Module
from .commands import PubCommand
from .utils import get_pub_buttons_view

if TYPE_CHECKING:
    from kmibot.client import DiscordClient


LOGGER = logging.getLogger(__name__)


class PubModule(Module):
    def __init__(self, client: "DiscordClient") -> None:
        client.tree.add_command(PubCommand(client.config), guild=client.guild)

    async def on_scheduled_event_update(
        self,
        client: "DiscordClient",
        old_event: discord.ScheduledEvent,
        new_event: discord.ScheduledEvent,
    ) -> None:
        if "Pub" in new_event.name:
            await self.handle_pub_event_change(client, old_event, new_event)

    async def handle_pub_event_change(
        self,
        client: "DiscordClient",
        old_event: discord.ScheduledEvent,
        new_event: discord.ScheduledEvent,
    ) -> None:
        self.pub_channel = client.get_channel(client.config.pub.channel_id)
        assert isinstance(self.pub_channel, discord.TextChannel)

        if old_event.status is not EventStatus.active and new_event.status is EventStatus.active:
            # The Pub has started.
            LOGGER.info("A pub event has started.")
            pub = client.config.pub.get_pub_by_name(new_event.location or "")
            if pub:
                await self.pub_channel.send(
                    "\n".join(
                        [
                            "**Pub-O-Clock**",
                            f"We are at {pub.emoji} **{pub.name}** {pub.emoji}",
                        ],
                    ),
                    view=get_pub_buttons_view(pub),
                )
            else:
                LOGGER.warning(
                    f"A pub event started, but the name was not a known pub: {new_event.location}"
                )

        if (
            old_event.status is not EventStatus.completed
            and new_event.status is EventStatus.completed
        ):
            # The Pub has ended.
            LOGGER.info("A pub event has ended.")
            await self.pub_channel.send(
                "The pub is over. You are still not allowed to say that word.",
            )
