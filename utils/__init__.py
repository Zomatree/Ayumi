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

import asyncio
import contextlib
import functools
import json
import random
import re
import textwrap
import traceback
import types
import typing as tp

import discord
from discord.ext import commands, menus

# Format

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
    """Formats an exception with traceback.format_exception, cleans up filenames and dedent it"""
    return textwrap.dedent('\n'.join(map(format_tb_line, traceback.format_exception(*args, **kwargs))))


def format_arg(arg: object) -> str:
    """Returns the object's type along with it's module"""
    cls = arg.__class__
    return cls.__name__ + " from module: " + cls.__module__


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


MISSING_FIELD = '⚠️ **__MISSING FIELD__**'


class Embed(discord.Embed):
    def __init__(self, **options):
        super().__init__(**options)
        self.default_inline = options.get('default_inline', True)

        if isinstance(self.colour, discord.embeds._EmptyEmbed):
            self.colour = discord.Color.from_hsv(random.random(), random.uniform(0.75, 0.95), 1)

    def add_field(self, *, name: tp.Any, value: tp.Any, inline: tp.Optional[bool] = None):
        return super().add_field(name=str(name) or MISSING_FIELD,
                                 value=str(value) or MISSING_FIELD,
                                 inline=self.default_inline if inline is None else inline)


# decos

def multiple_cooldowns(*cooldowns: tp.Tuple[commands.CooldownMapping]):
    """A decorators that allows a command to have multiple cooldowns at once"""
    def wrapper(func: types.FunctionType):

        new_cds = list(cooldowns)

        if curr_cds := getattr(func, '__multiple_cooldowns__'):  # support to slap multiple decos
            curr_cds.extend(new_cds)

        else:
            func.__multiple_cooldowns__ = new_cds

        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            ctx = args[1] if isinstance(args[0], commands.Cog) else args[0]

            for cd in func.__multiple_cooldowns__:
                if retry_after := cd.get_bucket(ctx.message).update_rate_limit():
                    raise commands.CommandOnCooldown(cd, retry_after)

            return await func(*args, **kwargs)

        return wrapped

    return wrapper


# converters


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


# json lib but it runs in an executor

async def executor_json_loads(s: str):
    """Loads a json from string in an executor"""  # wasn't too sure if it was blocking so ...
    return await asyncio.get_event_loop().run_in_executor(None, json.loads, s)


async def executor_json_dumps(d: dict):
    """Formats to json in an executor"""
    return await asyncio.get_event_loop().run_in_executor(None, json.dumps, d)