from datetime import datetime, timedelta
from logging import getLogger

import discord
from discord.app_commands import Group, command, describe

from kmibot.config import BotConfig

from .utils import event_is_pub, get_pub_buttons_view
from .views import PubView
from kmibot.api import FerryAPI, PubSchema

LOGGER = getLogger(__name__)


class PubCommand(Group):
    def __init__(self, config: BotConfig, api_client: FerryAPI) -> None:
        self.config = config
        self.api_client = api_client
        super().__init__(name="pub", description="Manage the pub event")

    async def _choose_pub(
        self,
        interaction: discord.Interaction,
        prompt: str,
    ) -> PubSchema:
        view = PubView(await self.api_client.get_pubs(), prompt)
        await interaction.response.send_message(
            prompt,
            view=view,
            ephemeral=True,
        )
        pub = await view.wait_until_complete()
        LOGGER.info(f"{interaction.user} chose {pub.name}")
        return pub

    def _get_next_pub_time(self) -> datetime:
        now = datetime.now(tz=self.config.timezone)

        today = now.date()
        if today.weekday() < self.config.pub.weekday or (
            today.weekday() == self.config.pub.weekday
            and (now.hour, now.minute) < (self.config.pub.hour, self.config.pub.minute)  # noqa: E501,W503
        ):
            # The pub has not yet happened
            monday = today - timedelta(days=today.weekday())
        else:
            # The pub has already started or happened, look at next week
            monday = today + timedelta(days=7 - today.weekday())
        pubday = monday + timedelta(days=self.config.pub.weekday)

        return datetime(
            pubday.year,
            pubday.month,
            pubday.day,
            self.config.pub.hour,
            self.config.pub.minute,
            tzinfo=self.config.timezone,
        )

    def _get_next_event(
        self, guild: discord.Guild, *, ignore_time: bool = False
    ) -> discord.ScheduledEvent | None:
        pub_time = self._get_next_pub_time()
        for event in sorted(guild.scheduled_events, key=lambda se: se.start_time):
            if (
                event_is_pub(event)
                and (ignore_time or event.start_time == pub_time)
                and event.status in {discord.EventStatus.scheduled, discord.EventStatus.active}
            ):
                return event
        return None

    async def _create_pub_event(
        self,
        guild: discord.Guild,
        pub: PubSchema,
        start_time: datetime,
        *,
        user: discord.User | discord.Member,
        title: str = "Pub",
    ) -> discord.ScheduledEvent:
        LOGGER.info(f"Creating scheduled event at {start_time}")
        scheduled_event = await guild.create_scheduled_event(
            name=f"{pub.emoji} {title} {self.config.pub.supplemental_emoji}",
            start_time=start_time,
            end_time=start_time + timedelta(hours=3),
            entity_type=discord.EntityType.external,
            privacy_level=discord.PrivacyLevel.guild_only,
            location=pub.name,
            description=self.config.pub.description,
            reason=f"{user} used the /pub next command",
        )
        person = await self.api_client.get_person_for_discord_member(user)
        await self.api_client.create_pub_event(
            timestamp=start_time,
            pub_id=pub.id,
            created_by=person.id,
            scheduled_event_id=scheduled_event.id,
        )
        return scheduled_event

    @command(description="Select the pub for next week.")  # type: ignore[arg-type]
    async def next(self, interaction: discord.Interaction) -> None:  # noqa: A003
        LOGGER.info(f"{interaction.user} used /pub next")
        assert interaction.guild is not None

        if self._get_next_event(interaction.guild):
            LOGGER.info("A pub event already exists.")
            await interaction.response.send_message(
                "A pub event already exists.",
                ephemeral=True,
            )
            return

        pub_time = self._get_next_pub_time()

        pub = await self._choose_pub(
            interaction,
            f"Please choose the pub for {pub_time}",
        )

        pub_channel = interaction.guild.get_channel(self.config.pub.channel_id)
        assert isinstance(pub_channel, discord.TextChannel)

        await self._create_pub_event(
            interaction.guild,
            pub,
            pub_time,
            user=interaction.user,
        )

        pub_channel = interaction.guild.get_channel(self.config.pub.channel_id)
        assert isinstance(pub_channel, discord.TextChannel)

        LOGGER.info(f"Posting pub info in {pub_channel}")
        formatted_pub_name = f"{pub.emoji} **{pub.name}** {self.config.pub.supplemental_emoji}"
        await pub_channel.send(
            "\n".join(
                [
                    "**Pub Next Week**",
                    f"The next pub will be <t:{int(pub_time.timestamp())}:R>",
                    f"It will be held at {formatted_pub_name}",
                    "",
                    "If you are coming, please mark 🔔 interest on the event!",
                ],
            ),
            view=get_pub_buttons_view(pub),
        )

    @command(description="Announce a spontaneous pub event.")  # type: ignore[arg-type]
    async def now(self, interaction: discord.Interaction) -> None:
        LOGGER.info(f"{interaction.user} used /pub now")
        pub = await self._choose_pub(
            interaction,
            "Please choose the spontaneous pub",
        )
        now = datetime.now(tz=self.config.timezone)
        pub_time = now + timedelta(seconds=1)
        assert interaction.guild is not None

        pub_channel = interaction.guild.get_channel(self.config.pub.channel_id)
        assert isinstance(pub_channel, discord.TextChannel)

        await self._create_pub_event(
            interaction.guild,
            pub,
            pub_time,
            user=interaction.user,
            title="Spontaneous Pub",
        )

        # A message is posted in the channel by the scheduled event handler

    @command(description="Update the table number for the current pub event")
    @describe(
        table_number="The table number",
    )
    async def table(self, interaction: discord.Interaction, table_number: int) -> None:
        assert interaction.guild
        if table_number <= 0:
            await interaction.response.send_message(
                "Sorry, the table number must exist in this dimension.",
                ephemeral=True,
            )
            return

        event = self._get_next_event(interaction.guild, ignore_time=True)
        if event is None:
            LOGGER.info("No pub exists.")
            await interaction.response.send_message(
                "There doesn't appear to be a pub at this time.",
                ephemeral=True,
            )
            return

        pub_event = await self.api_client.get_pub_event_by_discord_id(event.id)
        pub = await self.api_client.get_pub(pub_event.pub)
        await self.api_client.update_table_for_pub_event(pub_event.id, table_number)

        await interaction.response.send_message(
            f"Set table number to {table_number}, thanks.",
            ephemeral=True,
        )

        await event.edit(location=f"{pub.name} - Table {table_number}")

        pub_channel = interaction.guild.get_channel(self.config.pub.channel_id)
        assert isinstance(pub_channel, discord.TextChannel)

        LOGGER.info(f"Posting pub table info in {pub_channel}")
        formatted_pub_name = f"{pub.emoji} **{pub.name}** {self.config.pub.supplemental_emoji}"
        await pub_channel.send(
            "\n".join(
                [
                    "**Pub Table**",
                    f"We are at table {table_number} in {formatted_pub_name}",
                ],
            ),
            view=get_pub_buttons_view(pub),
        )
