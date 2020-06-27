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
import sys

import aiohttp
import discord
from discord.ext import commands

import utils
from core import context


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         **kwargs,
                         command_prefix=self.get_config_prefix,
                         max_messages=None,
                         fetch_offline_members=False,
                         guild_subscriptions=False,
                         allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        self._before_invoke = self.before_invoke

    def get_config_prefix(self, bot, message: discord.Message):
        return self.config['discord']['prefix']

    # -- Properties -- #

    @property
    def cache(self) -> utils.TimedCache:
        return self._cache

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    @property
    def log_webhook(self) -> discord.Webhook:
        return self._log_webhook

    @property
    def config(self) -> dict:
        return self._config

    @config.setter
    def config(self, new_config: dict) -> None:
        self._config = new_config

    # -- Start / Stop -- #

    async def connect(self, *, reconnect: bool = True):
        """Used as an async alternative init"""
        self._session = aiohttp.ClientSession()
        self._cache = utils.TimedCache(timeout=datetime.timedelta(hours=24))
        self._log_webhook = discord.Webhook.from_url(self.config['discord']['logger_url'],
                                                     adapter=discord.AsyncWebhookAdapter(self.session))
        self.dispatch('startup')
        return await super().connect(reconnect=reconnect)

    async def on_startup(self):
        await self.wait_until_ready()

        embed = (utils.Embed(title="Logged in as {0.user} ({0.user.id})".format(self),
                             color=discord.Color.green(),
                             default_inline=False)

                 .add_field(name='Platform', value=utils.codeblock(sys.platform))
                 .add_field(name='Python version', value=utils.codeblock(sys.version))
                 .add_field(name='Discordpy version', value=utils.codeblock(discord.__version__)))

        await self.log_webhook.send(content=f"<@{self.owner_id}>", embed=embed)

        for ext in ('jishaku', 'cogs.owner.__init__'):
            self.load_extension(ext)

    async def close(self):
        await self.session.close()
        return await super().close()

    # -- Error handling -- #

    # event error

    async def on_error(self, event_method: str, *args, **kwargs):
        """Logs errors that were raised in events"""
        tb = utils.format_exception(*sys.exc_info())

        embed = utils.Embed(title=event_method + ' error',
                            description=utils.codeblock(tb, lang='py'),
                            color=discord.Color.red())

        coro = getattr(self, event_method)
        parameters = inspect.signature(coro).parameters.keys()

        for param, arg in zip(parameters, args):
            embed.add_field(name='arg - ' + param, value=utils.format_arg(arg), inline=False)

        for key, value in kwargs.items():
            embed.add_field(name='kwarg - ' + key, value=utils.format_arg(value), inline=False)

        await self.log_webhook.send(embed=embed)

    # command error

    def format_command_error(self, ctx: context.Context, exception: Exception, limit: int = None) -> utils.Embed:
        """A helper function that formats exceptions"""
        tb = utils.format_exception(*utils.exc_info(exception), limit)  # cannot sys.exc_info can't recover it for some reason

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

        exception = getattr(exception, 'original', exception)

        await ctx.send(embed=self.format_command_error(ctx, exception, limit=1))
        await self.log_webhook.send(embed=self.format_command_error(ctx, exception))

    # -- Misc -- #

    async def get_context(self, message: discord.Message, *, cls: commands.Context = context.Context):
        """Uses our custom context"""
        return await super().get_context(message, cls=cls)

    async def before_invoke(self, ctx: context.Context):
        """Typing animation before invoking anything"""
        await ctx.trigger_typing()
