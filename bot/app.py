import argparse
import asyncio
from logging import getLogger
from pathlib import Path

import discord

from .client import DiscordClient
from .config import BotConfig, ConfigException

LOGGER = getLogger(__name__)


async def run(client: DiscordClient, token: str) -> None:
    async with client:
        await client.login(token)
        await client.connect()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', "--config", type=str, default="config.toml")
    return parser.parse_args()


def app() -> None:
    discord.utils.setup_logging()

    args = parse_args()

    try:
        config = BotConfig.load_from_file(Path(args.config))
    except ConfigException as e:
        LOGGER.error("The config file was not valid")
        LOGGER.error(str(e))
        return

    client = DiscordClient(config)

    try:
        asyncio.run(run(client, config.discord.token))
    except KeyboardInterrupt:
        pass
