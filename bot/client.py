import logging

import discord
from discord import app_commands

from .config import BotConfig
from .modules import MODULES

LOGGER = logging.getLogger(__name__)


class DiscordClient(discord.Client):

    def __init__(self, config: BotConfig) -> None:
        super().__init__(intents=self.intents)

        self.config = config
        self.guild = discord.Object(config.discord.guild_id)
        self.tree = app_commands.CommandTree(self)

        self._modules = [module_cls(self) for module_cls in MODULES]

    @property
    def intents(self) -> discord.Intents:
        intents = discord.Intents.default()
        intents.message_content = True
        return intents

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        await self.tree.sync(guild=self.guild)

    async def on_ready(self):
        LOGGER.info(f"Logged on as {self.user}!")

        if len(guilds := [guild async for guild in self.fetch_guilds()]) != 1:
            LOGGER.error(
                f"Expected to connect to exactly 1 guild, found {len(guilds)}",
            )
