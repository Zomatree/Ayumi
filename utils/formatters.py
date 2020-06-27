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

import re
import textwrap
import traceback
import types
import typing as tp

import discord
from discord.ext import menus, commands

# Format tracebacks

TB_PATTERN = re.compile(r"File (\".+\")")
SLASH_PATTERN = re.compile(r"/|\\")
START_LINE_WHITESPACE = re.compile(r"^\s+")


def exc_info(exception: Exception) -> tp.Tuple[type, Exception, types.TracebackType]:
    """An equivalent of sys.exc_info() that uses an exception"""
    return exception.__class__, exception, exception.__traceback__


def format_match(match: re.Match) -> str:
    return "File \"" + '/'.join(re.split(SLASH_PATTERN, match[0])[-2:])


def format_tb_line(line: str) -> str:
    """Formats lines in traceback to cleanup filenames"""
    return re.sub(TB_PATTERN, format_match, textwrap.dedent(line))


def format_exception(*args, **kwargs) -> str:
    """Fully formats the exception"""
    return '\n'.join(map(format_tb_line, traceback.format_exception(*args, **kwargs)))


def format_arg(arg: object) -> str:
    """Returns the object's type along with it's module"""
    cls = arg.__class__
    return cls.__name__ + " from module: " + cls.__module__


# Others


def codeblock(text: str, *, lang: str = None) -> str:
    """Returns a codeblock version of the string"""
    return f"```{lang or ''}\n{text}\n```"

# Mini paginator, NOTE: importing core causes circular imports


class OnePage(menus.Menu):
    def __init__(self, msg: tp.Union[str, discord.Embed, dict], **kwargs):
        super().__init__(**kwargs)
        self.msg = msg

    async def send_initial_message(self, ctx: commands.Context, channel: discord.abc.Messageable):
        msg = self.msg

        if isinstance(msg, discord.Embed):
            return await channel.send(embed=msg)
        elif isinstance(msg, str):
            return await channel.send(msg)
        elif isinstance(msg, dict):
            return await channel.send(**msg)
        else:
            raise TypeError("Expected Embed, str or dict, got " + msg.__class__.__name__)

    @menus.button('\U0001f512')
    async def on_close(self, payload: discord.RawReactionActionEvent):
        await self.message.delete()
        self.stop()
