import discord

from kmibot.config import PubInfo


def event_is_pub(event: discord.ScheduledEvent) -> bool:
        return "Pub" in event.name

def get_pub_buttons_view(pub: PubInfo) -> discord.ui.View:
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Map", url=pub.map_url))
    if pub.menu_url:
        view.add_item(discord.ui.Button(label="Menu", url=pub.menu_url))
    return view
