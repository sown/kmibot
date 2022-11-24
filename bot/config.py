from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo

import tomli
from pydantic import (BaseModel, BaseSettings, HttpUrl, ValidationError,
                      parse_obj_as, validator)


class ConfigException(Exception):
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

    pubs: List[PubInfo]
    channel_id: int
    description: str
    weekday: int
    hour: int
    minute: int = 0


class FerryConfig(BaseModel):

    channel_id: int
    banned_word: str
    emoji_reacts: str


class BotConfig(BaseSettings):

    timezone: ZoneInfo
    discord: DiscordConfig
    ferry: FerryConfig
    pub: PubConfig

    @validator("timezone", pre=True)
    def parse_timezone(cls, val: str) -> ZoneInfo:
        return ZoneInfo(val)

    @classmethod
    def load_from_file(cls, path: Path) -> "BotConfig":
        try:
            with path.open("rb") as fh:
                data = tomli.load(fh)
        except FileNotFoundError:
            raise ConfigException("Unable to find config file")
        except IOError:
            raise ConfigException("Unable to read config file.")
        except tomli.TOMLDecodeError as e:
            raise ConfigException(f"Unable to parse TOML: {e}")

        try:
            return parse_obj_as(cls, data)
        except ValidationError as e:
            raise ConfigException(f"Config file did not match schema: {e}")
