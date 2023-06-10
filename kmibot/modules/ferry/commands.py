from logging import getLogger
from typing import Optional

import discord
from discord.app_commands import Group, command, describe

from kmibot.config import BotConfig

LOGGER = getLogger(__name__)

def parse_emoji_message(emoji_message):
    emoji_lines = emoji_message.content.split("\n")[1:]
    emoji_lines_counts = [int(l.count(":") / 2) for l in emoji_lines]
    ferry_counts = {user: count for user, count in zip(emoji_message.mentions, emoji_lines_counts)}
    return ferry_counts

def ferrify(count):
    if count == 0:
        return ""
    return ":bullettrain_front:" + ":train:"*(count-1)

def build_emoji_message(ferry_counts):
    return [f"{user.mention} {ferrify(ferry_count)}" for user, ferry_count in ferry_counts.items()]

class FerryCommand(Group):

    def __init__(self, config: BotConfig) -> None:
        super().__init__(name="ferry", description="Interact with ferries.")
        self.config = config

    @command(description="Accuse somebody of ferrying.")  # type: ignore[arg-type]
    @describe(member="The criminal you are accusing.", quote="A quote as evidence of the crime.")
    async def accuse(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        quote: Optional[str] = None,
    ) -> None:
        LOGGER.info(f"{interaction.user} used /ferry accuse")
        last_message_id = interaction.channel.last_message_id
        ferry_counts = {}
        if last_message_id:
            last_message = await interaction.channel.fetch_message(last_message_id)
            if last_message.content.startswith("Bad people:"):
                ferry_counts = parse_emoji_message(last_message)
        if member in ferry_counts:
            ferry_counts[member] += 1
        else:
            ferry_counts[member] = 1
        lines = [
            f"{member.mention} has been accused by {interaction.user.mention}",
        ]
        if quote:
            lines.extend(["", f"> {quote}"])
        await interaction.response.send_message("\n".join(lines))
        new_message = await interaction.channel.send("\n".join(["Bad people:"] + build_emoji_message(ferry_counts)))
