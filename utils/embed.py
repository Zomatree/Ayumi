"""
Ayumi - Discord bot
Copyright (C) 2020 - Saphielle Akiyama | saphielle.akiyama@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord.embeds
import random
import typing as tp
import datetime as dt

MISSING_FIELD = '⚠️ **__MISSING FIELD__**'


class Embed(discord.Embed):
    def __init__(self, **options):
        super().__init__(**options)
        self.timestamp = dt.datetime.now(tz=dt.timezone.utc)

        self.default_inline = options.get('default_inline', True)

        if isinstance(self.colour, discord.embeds._EmptyEmbed):
            self.colour = discord.Color.from_hsv(random.random(), random.uniform(0.75, 0.95), 1)

    def add_field(self, *, name: tp.Any, value: tp.Any, inline: tp.Union[bool, None] = None):
        return super().add_field(name=str(name) or MISSING_FIELD,
                                 value=str(value) or MISSING_FIELD,
                                 inline=self.default_inline if inline is None else inline)
