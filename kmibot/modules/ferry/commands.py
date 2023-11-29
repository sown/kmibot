import random
import re
from logging import getLogger
from typing import TYPE_CHECKING, Any, Optional, Union

import discord
from discord.app_commands import Group, command, describe

from kmibot.config import BotConfig

from .types import Accusation

FerryCounts = dict[Union[discord.Member, discord.User], int]

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
    train = [ra.choice(FRONT_OF_TRAIN)] + ra.choices(TRAIN_PARTS, k=count-1)
    return "".join(train)

def build_emoji_message(ferry_counts: FerryCounts) -> list[str]:
    return [f"{user.mention} {ferrify(ferry_count, user.id)}" for user, ferry_count in ferry_counts.items()]


class FerryCommand(Group):

    def __init__(self, config: BotConfig, module: "FerryModule") -> None:
        super().__init__(name="ferry", description="Interact with ferries.")
        self.config = config
        self.ferry_module = module

    def is_message_accusation(self, message: discord.Message) -> bool:
        return all([
            # 0 < len(message.mentions) < 3,  # ??
            "has been accused of a heinous crime by" in message.content,
            message.author == self.ferry_module.client.user,
        ])

    async def parse_emoji_message(self, emoji_message: discord.Message) -> FerryCounts:
        emoji_lines = emoji_message.content.split("\n")[1:]
        emoji_lines_counts = [int(e.count(":") / 2) for e in emoji_lines]
        users_in_message = [
            await self.ferry_module.client.fetch_user(int(uid))
            for uid in re.findall(r"<@(\d+)>", emoji_message.content)
        ]
        ferry_counts: FerryCounts = dict(zip(users_in_message, emoji_lines_counts))
        return ferry_counts


    def parse_message_as_accusation(self, message: discord.Message) -> Optional[Accusation]:
        if not self.is_message_accusation(message):
            return None

        mentions = list(message.mentions)  # It's already a list, but let's copy it.

        if len(mentions) == 1:
            mentions = mentions * 2

        if not mentions:
            return None

        return Accusation(
            timestamp=message.created_at,
            criminal=mentions[0],
            accusor=mentions[1],
        )

    async def get_ferry_counts(self) -> FerryCounts:
        last_message_id = self.ferry_module.accuse_channel.last_message_id
        ferry_counts = {}
        if last_message_id:
            last_message = await self.ferry_module.accuse_channel.fetch_message(last_message_id)
            if last_message.content.startswith("Bad people:"):
                ferry_counts = await self.parse_emoji_message(last_message)
        return ferry_counts

    async def handle_emoji(self, reaction: discord.Reaction, user: discord.User) -> None:
        # Ignore reactions from this bot.
        if user == self.ferry_module.client.user:
            return

        # Ignore reactions that are not an accusations.
        if not self.is_message_accusation(reaction.message):
            return

        # Attempt to parse
        accusation = self.parse_message_as_accusation(reaction.message)
        if accusation is None:
            LOGGER.error("Unable to parse accusation")
            return

        if user == accusation.accusor:
            await user.send("You cannot do that. Nice try though.")
            await user.send("Also, I'm telling on you.")

            await self.record_crime(accusation.criminal)
            return

        LOGGER.info(f"{user} has voted on an accusation.")
        if sum(r.count for r in reaction.message.reactions) == 3:
            #If the user found themselves guilty, remove the react.
            # if user == accusation.criminal:
            #     LOGGER.info("Removing initial reaction from criminal")
            #     await reaction.remove(user)
            #     return

            LOGGER.info("The accusation is ratified.")
            sentence = random.choice(self.ferry_module.client.config.ferry.sentences)  # noqa: S311
            lines = [
                f"The accusation has been ratified by {user.mention}",
                "",
                f"{accusation.criminal.mention} has been sentenced to {sentence}",
            ]
            await reaction.message.channel.send("\n".join(lines), reference=reaction.message)
            await reaction.message.add_reaction("🚨")

            await self.record_crime(accusation.criminal)

    async def record_crime(self, criminal: Union[discord.User, discord.Member]) -> None:
        ferry_counts = await self.get_ferry_counts()

        try:
            ferry_counts[criminal] += 1
        except KeyError:
            ferry_counts[criminal] = 1

        await self.ferry_module.accuse_channel.send("\n".join(["Bad people:"] + build_emoji_message(ferry_counts)))

    async def publish_accusation(
            self,
            criminal: Union[discord.User, discord.Member],
            accuser: Union[discord.User, discord.ClientUser, discord.Member],
            quote: Optional[str],
        ) -> None:
        lines = [
            f"{criminal.mention} has been accused of a heinous crime by {accuser.mention}",
        ]
        if quote:
            lines.extend(["", f"> {quote}"])

        lines.extend(["", f"Please vote on whether {criminal.mention} is guilty using the emojis below."])

        # Publish the accusation
        message = await self.ferry_module.announce_channel.send("\n".join(lines))

        await message.add_reaction(FERRY)
        await message.add_reaction(TRAIN)

    @command(description="Accuse somebody of ferrying.")  # type: ignore[arg-type]
    @describe(member="The criminal you are accusing.", quote="A quote as evidence of the crime.")
    async def accuse(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        quote: Optional[str] = None,
    ) -> None:
        LOGGER.info(f"{interaction.user} used /ferry accuse")

        if interaction.user == member:
            await interaction.response.send_message("Who watches the watchman?", ephemeral=True)
            return

        await interaction.response.send_message("ok", ephemeral=True)
        await self.publish_accusation(member, interaction.user, quote)
