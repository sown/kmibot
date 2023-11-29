from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from kmibot.client import DiscordClient


class Module:
    def __init__(self, client: "DiscordClient") -> None:
        pass

    async def on_ready(self, client: "DiscordClient") -> None:
        pass

    async def on_scheduled_event_update(
        self,
        client: "DiscordClient",
        old_event: discord.ScheduledEvent,
        new_event: discord.ScheduledEvent,
    ) -> None:
        pass
