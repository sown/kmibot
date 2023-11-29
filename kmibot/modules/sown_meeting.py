from datetime import timedelta
from logging import getLogger
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import dateparser
import discord
from discord import app_commands

from .module import Module

if TYPE_CHECKING:
    from kmibot.client import DiscordClient

LOGGER = getLogger(__name__)


@app_commands.command(  # type: ignore[arg-type]
    name="sown_meeting",
    description="Create and announce a SOWN meeting event",
)
@app_commands.describe(
    meeting_type="Type of SOWN Meeting",
    datetime="Date and Time of Meeting",
    location="Location of the Meeting",
)
@app_commands.choices(
    meeting_type=[
        app_commands.Choice(
            name="Workshop", value="workshop"
        ),  # TODO: Do not hardcode these, use values in config
        app_commands.Choice(name="Meeting", value="meeting"),
        app_commands.Choice(name="Outing", value="outing"),
        app_commands.Choice(name="Social", value="social"),
    ]
)
async def create_sown_meeting_command(
    interaction: discord.Interaction,
    meeting_type: app_commands.Choice[str],
    datetime: str,
    location: str,
) -> None:
    if (dt := dateparser.parse(datetime)) is None:
        await interaction.response.send_message(
            "I don't understand that date format. :(", ephemeral=True
        )
        return

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=ZoneInfo("Europe/London")
        )  # TODO: Do not hardcode this, use the value in config

    LOGGER.info(f"Creating scheduled event at {dt}")
    assert interaction.guild
    await interaction.guild.create_scheduled_event(
        name=f"SOWN {meeting_type.name}",
        start_time=dt,
        end_time=dt + timedelta(hours=3),
        entity_type=discord.EntityType.external,
        privacy_level=discord.PrivacyLevel.guild_only,
        location=location,
        description=f"SOWN {meeting_type.name} at {location}",
        reason=f"{interaction.user} used the /sown_meeting command",
    )
    await interaction.response.send_message("Event created.", ephemeral=True)


class SOWNMeetingModule(Module):
    def __init__(self, client: "DiscordClient") -> None:
        client.tree.add_command(create_sown_meeting_command, guild=client.guild)
