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

import typing as tp

from discord.ext import commands

import core


def raise_badarg(arg: str) -> None:
    raise commands.BadArgument(message=f"Sorry ! I Couldn't find a command named \"{arg}\" ")


class CommandConverter(commands.Converter):
    async def convert(self, ctx: core.Context, arg: str) -> tp.Union[commands.Command, None]:
        return ctx.bot.get_command(arg) or raise_badarg(arg)


def setup(bot: core.Bot):
    pass
