from datetime import datetime, timedelta
from logging import getLogger

import discord
from discord.app_commands import Group, command

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

    def _get_next_event(self, guild: discord.Guild) -> discord.ScheduledEvent | None:
        pub_time = self._get_next_pub_time()
        for event in guild.scheduled_events:
            if event_is_pub(event) and event.start_time == pub_time:
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
