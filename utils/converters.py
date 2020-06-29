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

import contextlib
from discord.ext import commands

DAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')


def dayconverter(arg: str):
    """Tries to convert a string into a valid day"""
    arg = arg.lower()

    if arg in DAYS:
        return arg

    for day in DAYS:
        if day.startswith(arg):
            return day

    if arg.isdigit():
        with contextlib.suppress(IndexError):
            return DAYS[int(arg) + 1]

    raise commands.BadArgument(message=f"Sorry ! I wasn't able to convert \"{arg}\" into a valid weekday")
