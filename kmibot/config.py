from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import discord
import tomli
from pydantic import BaseModel, BaseSettings, HttpUrl, ValidationError, parse_obj_as, validator


class ConfigError(Exception):
    """There was a problem with the config file."""


class DiscordConfig(BaseModel):

    token: str
    guild_id: int


class PubInfo(BaseModel):

    name: str
    emoji: str
    menu_url: Optional[HttpUrl] = None
    map_url: HttpUrl


class PubConfig(BaseModel):

    pubs: list[PubInfo]
    channel_id: int
    description: str
    weekday: int
    hour: int
    minute: int = 0

    def get_pub_by_name(self, name: str) -> Optional[PubInfo]:
        return discord.utils.find(
            lambda p: p.name == name, self.pubs,
        )

class FerryConfig(BaseModel):

    channel_id: int
    banned_word: str
    emoji_reacts: str


class RoleInfo(BaseModel):

    name: str
    colour: str


class LicenceType(BaseModel):

    name: str
    emoji: str
    role: Optional[RoleInfo] = None


class LicenceConfig(BaseModel):

    licence_types: list[LicenceType]


class BotConfig(BaseSettings):

    timezone: ZoneInfo
    discord: DiscordConfig
    ferry: FerryConfig
    licence: LicenceConfig
    pub: PubConfig

    class Config:
        env_nested_delimiter = '__'

    @validator("timezone", pre=True)
    def parse_timezone(cls, val: str) -> ZoneInfo:  # noqa: N805
        return ZoneInfo(val)

    @classmethod
    def load_from_file(cls, path: Path) -> "BotConfig":  # noqa: ANN102
        try:
            with path.open("rb") as fh:
                data = tomli.load(fh)
        except FileNotFoundError as e:
            raise ConfigError("Unable to find config file") from e
        except OSError as e:
            raise ConfigError("Unable to read config file.") from e
        except tomli.TOMLDecodeError as e:
            raise ConfigError(f"Unable to parse TOML: {e}") from e

        try:
            return parse_obj_as(cls, data)
        except ValidationError as e:
            raise ConfigError(f"Config file did not match schema: {e}") from e

