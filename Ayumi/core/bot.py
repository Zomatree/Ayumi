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

import sys
import inspect
import contextlib
import datetime as dt

import aiohttp
import discord
import aioredis
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

    def get_config_prefix(self, bot, message: discord.Message) -> str:
        try:
            return self.config['discord']['prefix']
        except KeyError:
            return 'fallback '  # just in case I accidentally kill the config

    # -- Properties -- #

    @property
    def redis(self) -> aioredis.Redis:
        return self._redis

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

        if not isinstance(new_config, dict):
            raise TypeError("New config must be a dict")

        self._config = new_config  # logging ?

    # -- Start / Stop -- #

    async def connect(self, *, reconnect: bool = True):
        """Used as an async alternative init"""

        self._session = aiohttp.ClientSession()

        self._redis = await aioredis.create_redis_pool('redis://localhost')

        self._before_invoke = self.before_invoke

        self._log_webhook = discord.Webhook.from_url(self.config['discord']['logger_url'],
                                                     adapter=discord.AsyncWebhookAdapter(self.session))

        self.dispatch('startup')

        return await super().connect(reconnect=reconnect)

    async def on_startup(self):

        self.load_extension('jishaku')

        await self.wait_until_ready()

        codeblock = utils.codeblock

        disconfig = self.config['discord']

        embed = (utils.Embed(title="Logged in as {0.user} ({0.user.id})".format(self),

                             color=discord.Color.green(),

                             default_inline=False)

                 .add_field(name='Description', value=codeblock(disconfig['description']))

                 .add_field(name='Platform', value=codeblock(sys.platform))

                 .add_field(name='Python version', value=codeblock(sys.version))

                 .add_field(name='Discord.py version', value=codeblock(discord.__version__))

                 .add_field(name='Default prefix', value=codeblock(disconfig['prefix'])))


        await self.log_webhook.send(content=f"<@{self.owner_id}>", embed=embed)

        self.load_extension('cogs.owner')

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

                            color=discord.Color.red(),

                            default_inline=False)

        coro = getattr(self, event_method)

        parameters = inspect.signature(coro).parameters.keys()

        for param, arg in zip(parameters, args):
            embed.add_field(name='arg - ' + param, value=utils.format_arg(arg))

        for key, value in kwargs.items():
            embed.add_field(name='kwarg - ' + key, value=utils.format_arg(value))

        await self.log_webhook.send(embed=embed)

    # command error

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

        if isinstance(exception, commands.CommandNotFound):
            return

        tb = utils.format_exception(*utils.exc_info(exception))

        embed = utils.Embed(title=f"{ctx.qname} - {ctx.guild.name} / {ctx.channel.name} / {ctx.author}",

                            description=utils.codeblock(tb, lang='py'),

                            color=discord.Color.red(),

                            timestamp=dt.datetime.now(tz=dt.timezone.utc))

        for arg_name, arg in zip(ctx.command.clean_params.keys(), ctx.all_args):
            embed.add_field(name=arg_name, value=arg, inline=False)

        await self.log_webhook.send(embed=embed)

        await ctx.send(embed=utils.Embed(title=exception.__class__.__name__,

                                         description=utils.codeblock(exception),

                                         color=discord.Color.red()))

    # -- Misc -- #

    async def get_context(self, message: discord.Message, *, cls: commands.Context = context.Context):
        """Uses our custom context"""
        return await super().get_context(message, cls=cls)

    async def before_invoke(self, ctx: context.Context):
        """Typing animation before invoking anything"""
        with contextlib.suppress(discord.DiscordException):
            await ctx.trigger_typing()
