import datetime
import pathlib

import aiohttp
import discord
from discord.ext import commands
import logging

import utils


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         **kwargs,
                         max_messages=None,
                         fetch_offline_members=False,
                         allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        self._cache = utils.TimedCache(timeout=datetime.timedelta(hours=24))

        self._logger = logging.getLogger('discord')

        for file in pathlib.Path('./cogs').glob('**/*.py'):
            try:
                self.load_extension('.'.join(file.parts[:-1]) + '.' + file.stem)
            except Exception as e:
                self._logger.error(e)

        self.load_extension('jishaku')

    async def connect(self, *, reconnect=True):
        self._session = aiohttp.ClientSession()
        return await super().connect(reconnect=reconnect)

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

    async def close(self):
        await self.session.close()
        return await super().close()
