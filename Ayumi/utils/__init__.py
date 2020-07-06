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
import types
import random
import inspect
import textwrap
import functools
import itertools
import traceback
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
 
    tb_lines = traceback.format_exception(*args, **kwargs)

    formatted_lines = '\n'.join(map(format_tb_line, tb_lines))

    return textwrap.dedent(formatted_lines)


def format_arg(arg: object) -> str:
    """Returns the object's type along with it's module"""
    cls = arg.__class__
 
    return cls.__name__ + " from module: " + cls.__module__


def codeblock(text: str, *, lang: str = '') -> str:
    """Returns a codeblock version of the string"""
    return f"```{lang}\n{text}\n```"


class OnePage(menus.Menu):
    def __init__(self, msg: tp.Union[str, discord.Embed, dict], **kwargs):
        super().__init__(timeout=60, delete_message_after=True)
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
        self.stop()


MISSING_FIELD = '⚠️ **__MISSING FIELD__**'


class Embed(discord.Embed):
    def __init__(self, **options):
        super().__init__(**options)
 
        self.default_inline = options.get('default_inline', True)

        if isinstance(self.colour, discord.Embed.Empty.__class__):
            self.colour = discord.Color.from_hsv(random.random(), random.uniform(0.75, 0.95), 1)

    @staticmethod
    def check_empty_string(value: tp.Any):
        """A helper functions that highlights empty / missing fields"""
        return str(value) or MISSING_FIELD

    def add_field(self, *, name: tp.Any, value: tp.Any, inline: tp.Optional[bool] = None):
        return super().add_field(name=self.check_empty_string(name),
 
                                 value=self.check_empty_string(value),
 
                                 inline=self.default_inline if inline is None else inline)


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


class ListPageSource(menus.ListPageSource):
    """A subclass of MenuPages that always shows buttons"""
    def __init__(self, entries, *, per_page: int):
        if len(entries) == 1:
            entries *= 2

        super().__init__(entries, per_page=per_page)

    def get_max_pages(self):
        first, second = self.entries

        if first == second:
            return 1

        return super().get_max_pages()

# Some subclassed stuff

class AyumiCommand(commands.Command):
    """
    A class that provides some new things for commands :

    only_sends_help : A flag value used to format the help command

    example_args : a list of tuples representing possible arguments for a command


    @utils.command(example_args=[('hello', 'good morning')])
    async def greet(ctx, greeting):
        await ctx.send(greeting)

    greet.get_example(ctx)
    >>> s-greet hello
    >>> s-greet good morning

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        params_amount = len(self.clean_params)

        self.example_args = kwargs.get('example_args', None)

        self.only_sends_help = kwargs.get('only_sends_help', False)

    def get_example(self, ctx: commands.Context) -> str:
        """Returns an example invocation of the command"""

        base_invocation = ctx.prefix + self.qualified_name

        if self.example_args is None:
            return f"{base_invocation} {self.signature}"

        args = [random.choice(ex) for ex in self.example_args]

        args_str = map(str, args)

        formatted_args = ' '.join(args_str)

        return f"{base_invocation} {formatted_args}"

def command(name=None, cls=None, **attrs):
    """
    Copypaste of the commands.command to use our subclass
    without having to explicitely pass cls everywhere
    """
    if cls is None:
        cls = AyumiCommand

    def decorator(func):
        if isinstance(func, commands.Command):  # in case we forgot something
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)

    return decorator

class Group(AyumiCommand, commands.Group):
    """Copypaste of the superclass to use our subclassed stuff"""
    def group(self, *args, **kwargs):

        def decorator(func):

            kwargs.setdefault('parent', self)

            result = group(*args, **kwargs)(func)

            self.add_command(result)

            return result

        return decorator

    def command(self, *args, **kwargs):

        def decorator(func):

            kwargs.setdefault('parent', self)

            result = command(*args, **kwargs)(func)

            self.add_command(result)

            return result

        return decorator


def group(name=None, **attrs):
    """
    Copypaste of the commands.group to use our superclass
    without having to explicitely pass cls everywhere
    """
    attrs.setdefault('cls', Group)
    return command(name=name, **attrs)

# converters

class LiteralConverter:
    """
    A converter that tries to match a literal set of values

    @bot.command()
    async def some_command(ctx, arg: LiteralConveter['one', 'two', 'three', 'four']):
        pass

    This is also possible:

    VALUES = ['one', 'two', 'three', 'four']

    @bot.command()
    async def some_command(ctx, arg: LiteralConveter[VALUES]):
        pass
    """

    def __class_getitem__(cls, values: tp.Union[list, tuple]):
        def actual_converter(arg: str):
            arg = arg.lower()

            if arg in values:
                return arg

            for v in values:
                if v.startswith(arg):
                    return arg

            try:
                return values[int(arg) - 1]

            except (IndexError, ValueError):
                pass

            raise commands.BadArgument(f"Sorry ! I failed to match {arg} with an item in {values}")

        return actual_converter


class CommandConverter(commands.Converter):

    async def convert(self, ctx: commands.Bot, arg: str):
        if co := ctx.bot.get_command(arg.lower()):
            return co

        else:
            raise commands.BadArgument(f"Sorry ! I couldn't find the command named \"{arg}\"")

# some consts used by the anime cog

DAYS = 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'

SEASONS = {
    (80, 172): 'spring',
    (172, 264): 'summer',
    (264, 355): 'fall',
    (356, 79): 'winter',
}


# misc


def coalesce(*fns, ignored_exc=Exception, default=None):
    """Tries to run all functions, ignoring a given exceptioon and returns the default if not found"""
    for fn in fns:
        try:
            return fn()

        except ignored_exc:
            pass

    return default
