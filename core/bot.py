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

import datetime
import inspect
import re
import sys
import textwrap
import traceback

import aiohttp
import discord
from discord.ext import commands

import utils
from core import context


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         **kwargs,
                         max_messages=None,
                         fetch_offline_members=False,
                         guild_subscriptions=False,
                         allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    # We don't want to accidentally modify those

    @property
    def cache(self):
        return self._cache

    @property
    def session(self):
        return self._session

    @property
    def log_webhook(self):
        return self._log_webhook

    # Start / stop

    async def connect(self, *, reconnect: bool = True):
        """Used as an async alternative init"""
        self._session = aiohttp.ClientSession()
        self._cache = utils.TimedCache(timeout=datetime.timedelta(hours=24))
        self._log_webhook = discord.Webhook.from_url(self.config['discord']['logger_url'],
                                                     adapter=discord.AsyncWebhookAdapter(self.session))

        for ext in ('jishaku', 'cogs.owner.__init__'):
            self.load_extension(ext)

        return await super().connect(reconnect=reconnect)

    async def close(self):
        await self.session.close()
        return await super().close()

    # Custom context

    async def get_context(self, message: discord.Message, *, cls: commands.Context = context.Context):
        return await super().get_context(message, cls=cls)

    # Error handling

    @staticmethod
    def format_tb_line(line: str) -> str:
        """Formats lines in traceback to cleanup filenames"""
        return re.sub(r"File (\".+\")", "File \"...\"", textwrap.dedent(line))

    async def on_error(self, event_method: str, *args, **kwargs):
        """Logs errors that were raised in events"""
        tb = '\n'.join(map(self.format_tb_line, traceback.format_exception(*sys.exc_info())))

        embed = utils.Embed(title=event_method + ' error',
                            description=utils.codeblock(tb, lang='py'),
                            color=discord.Color.red())

        coro = getattr(self, event_method)
        parameters = inspect.signature(coro).parameters.keys()

        for param, arg in zip(parameters, args):
            embed.add_field(name='arg - ' + param, value=repr(arg), inline=False)

        for key, value in kwargs.items():
            embed.add_field(name='kwarg - ' + key, value=repr(value), inline=False)

        await self.log_webhook.send(embed=embed)

    def format_command_error(self, ctx: context.Context, exception: Exception, limit: int = None) -> utils.Embed:
        lines = traceback.format_exception(exception.__class__, exception, exception.__traceback__, limit=limit)
        tb = '\n'.join(map(self.format_tb_line, lines))

        embed = utils.Embed(title=f"{ctx.qname} - {ctx.guild.name} / {ctx.channel.name} / {ctx.author}",
                            description=utils.codeblock(tb, lang='py'),
                            color=discord.Color.red())

        for arg_name, arg in zip(ctx.command.clean_params.keys(), ctx.all_args):
            embed.add_field(name=arg_name, value=arg, inline=False)

        return embed

    async def on_command_error(self, ctx: context.Context, exception: Exception):
        """Logs errors that were raised in commands"""
        if self.extra_events.get('on_command_error', None):
            return

        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog and commands.Cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        await ctx.send(embed=self.format_command_error(ctx, exception, limit=1))
        await self.log_webhook.send(embed=self.format_command_error(ctx, exception))
