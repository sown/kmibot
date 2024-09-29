import logging
from typing import TYPE_CHECKING

import discord
from discord import EventStatus

from kmibot.api import FerryAPI

from ..module import Module
from .commands import PubCommand
from .utils import event_is_pub, get_formatted_pub_name, get_pub_buttons_view

if TYPE_CHECKING:
    from kmibot.client import DiscordClient


LOGGER = logging.getLogger(__name__)


class PubModule(Module):
    def __init__(self, client: "DiscordClient", api_client: FerryAPI) -> None:
        self.client = client
        self.api_client = api_client
        client.tree.add_command(PubCommand(client.config, api_client), guild=client.guild)

    async def on_scheduled_event_update(
        self,
        client: "DiscordClient",
        old_event: discord.ScheduledEvent,
        new_event: discord.ScheduledEvent,
    ) -> None:
        if event_is_pub(new_event):
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

            pub_event = await self.api_client.get_pub_event_by_discord_id(new_event.id)
            pub = await self.api_client.get_pub(pub_event.pub)

            formatted_pub_name = get_formatted_pub_name(pub, self.client.config)
            await self.pub_channel.send(
                "\n".join(
                    [
                        "**Pub-O-Clock**",
                        f"We are at {formatted_pub_name}",
                        "",
                        "Please let others know the table by using /pub table",
                    ],
                ),
                view=get_pub_buttons_view(pub),
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
