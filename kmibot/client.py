import asyncio
import logging

import discord
from discord import app_commands

from .config import BotConfig
from .modules import MODULES, Module

LOGGER = logging.getLogger(__name__)


class DiscordClient(discord.Client):
    def __init__(self, config: BotConfig) -> None:
        super().__init__(intents=self.intents)

        self.config = config
        self.guild = discord.Object(config.discord.guild_id)
        self.tree = app_commands.CommandTree(self)

        self._modules: list[Module] = [module_cls(self) for module_cls in MODULES]
        LOGGER.info(f"Set up {len(self._modules)} modules")

    @property
    def intents(self) -> discord.Intents:
        intents = discord.Intents.default()
        intents.message_content = True
        return intents

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        LOGGER.info("Synchronising app commands")
        commands = await self.tree.sync(guild=self.guild)
        for command in commands:
            LOGGER.info(f"Registered /{command.name}")

    async def on_ready(self) -> None:
        LOGGER.info(f"Logged on as {self.user}!")

        if len(guilds := [guild async for guild in self.fetch_guilds()]) != 1:
            raise RuntimeError(
                f"Expected to connect to exactly 1 guild, found {len(guilds)}",
            )
        guild = guilds[0]
        LOGGER.info(f"Guild: {guild.name}")

        for module in self._modules:
            asyncio.create_task(module.on_ready(self))

    async def on_scheduled_event_update(
        self,
        old_event: discord.ScheduledEvent,
        new_event: discord.ScheduledEvent,
    ) -> None:
        LOGGER.info(f"Received update for scheduled event: {old_event.name}")
        for module in self._modules:
            asyncio.create_task(module.on_scheduled_event_update(self, old_event, new_event))
