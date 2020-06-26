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
import logging

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
                         allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        self._cache = utils.TimedCache(timeout=datetime.timedelta(hours=24))

        self._logger = logging.getLogger('discord')

        for ext in ('jishaku', 'cogs.owner.__init__'):
            self.load_extension(ext)

    # We don't want to accidentally modify those

    @property
    def cache(self):
        return self._cache

    @property
    def session(self):
        return self._session

    @property
    def logger(self):
        return self._logger

    # Not called by us

    async def get_context(self, message: discord.Message, *, cls: commands.Context = context.Context):
        return await super().get_context(message, cls=cls)

    async def connect(self, *, reconnect=True):
        self._session = aiohttp.ClientSession()
        return await super().connect(reconnect=reconnect)

    async def close(self):
        await self.session.close()
        return await super().close()
