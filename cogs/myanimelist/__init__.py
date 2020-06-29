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

import calendar

import discord
import jikanpy
from discord.ext import commands

import core
import utils
import difflib

from datetime import datetime


class Anime(commands.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot
        self.aiojikan = jikanpy.AioJikan(session=bot.session)

    @commands.group()
    async def mal(self, ctx: core.Context):
        """My anime list related commands"""
        await ctx.send_help(ctx.command)

    @mal.command(aliases=['planning'])
    async def schedule(self, ctx: core.Context, day: utils.dayconverter = None):
        """Gets the anime schedule for a day in this week"""
        resp = await self.aiojikan.schedule(day=day)
