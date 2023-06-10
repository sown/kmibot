from datetime import datetime
from typing import NamedTuple, Union

import discord


class Accusation(NamedTuple):

    timestamp: datetime
    criminal: Union[discord.Member, discord.User]
    accusor: Union[discord.Member, discord.User]
    # quote: Optional[str]
