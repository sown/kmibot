from __future__ import annotations

import math
import random
from logging import getLogger
from typing import TYPE_CHECKING, Any, Optional, Union

import discord
from discord.app_commands import Group, command, describe
import httpx

from kmibot.config import BotConfig
from kmibot.modules.ferry.views import RatifyAccusationView

from .modals import AccuseModal

LOGGER = getLogger(__name__)

if TYPE_CHECKING:
    from . import FerryModule

FERRY = "⛴️"
TRAIN = "🚂"

FRONT_OF_TRAIN = [":bullettrain_front:", ":bullettrain_side:", ":steam_locomotive:", ":light_rail:"]
TRAIN_PARTS = [":train:", ":railway_car:"]


def ferrify(count: int, seed: Optional[Any] = None) -> str:
    if count == 0:
        return ""

    ra = random.Random(x=seed)
    train = [ra.choice(FRONT_OF_TRAIN)] + ra.choices(TRAIN_PARTS, k=count - 1)
    return "".join(train)


class FerryCommand(Group):
    def __init__(self, config: BotConfig, module: FerryModule) -> None:
        super().__init__(name="ferry", description="Interact with ferries.")
        self.config = config
        self.ferry_module = module

    async def publish_leaderboard(self) -> None:
        people = await self.ferry_module.api_client.get_leaderboard()  # type: ignore[has-type]
        content = [
            f"{person.get_display_for_message()} {ferrify(math.ceil(person.current_score), person.id)}"
            for person in people
        ]

        await self.ferry_module.channel.send("\n".join(["Bad people:"] + content))

    async def publish_accusation(
        self,
        criminal: Union[discord.User, discord.Member],
        accuser: Union[discord.User, discord.ClientUser, discord.Member],
        quote: str,
    ) -> None:
        try:
            person_criminal = await self.ferry_module.api_client.get_person_for_discord_member(  # type: ignore[has-type]
                criminal
            )
            person_accuser = await self.ferry_module.api_client.get_person_for_discord_member(  # type: ignore[has-type]
                accuser
            )
        except httpx.HTTPStatusError as exc:
            LOGGER.exception(exc)
            return

        accusation = await self.ferry_module.api_client.create_accusation(  # type: ignore[has-type]
            created_by=person_accuser.id,
            suspect=person_criminal.id,
            quote=quote,
        )
        lines = [
            f"{criminal.mention} has been accused of a heinous crime by {accuser.mention}",
        ]
        if quote:
            lines.extend(["", f"> {quote}"])

        lines.extend(
            ["", f"Please vote on whether {criminal.mention} is guilty using the emojis below."]
        )

        view = RatifyAccusationView(self.ferry_module, accusation)

        # Publish the accusation
        await self.ferry_module.channel.send("\n".join(lines), view=view)

    @command(description="Accuse somebody of ferrying.")  # type: ignore[arg-type]
    @describe(member="The criminal you are accusing.")
    async def accuse(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        LOGGER.info(f"{interaction.user} used /ferry accuse")

        if interaction.user == member:
            await interaction.response.send_message("Who watches the watchman?", ephemeral=True)
            return

        await interaction.response.send_modal(AccuseModal(self.ferry_module, criminal=member))
