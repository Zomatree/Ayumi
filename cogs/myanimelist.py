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
import datetime as dt
import json
import typing as tp

import jikanpy
from discord.ext import commands, menus

import core
import utils


class JikanAnimeSource(menus.ListPageSource):
    def __init__(self, entries: tp.List[dict], *, is_nsfw: bool):

        # we assume that it is nsfw if the api didn't provide a rating
        if not is_nsfw:
            entries = [e for e in entries if not e.get('r18', True)]

        super().__init__(entries, per_page=1)

    def format_page(self, menu: menus.Menu, anime: dict):

        title = [anime.get('title')]

        if score := anime.get('score'):
            title.append(f"Score : {score}")

        embed = utils.Embed(title=' | '.join(title),
                            url=anime.get('url'),
                            description=(anime.get('synopsis') or 'Not found')[:2000])

        if thumbnail := anime.get('image_url'):
            embed.set_thumbnail(url=thumbnail)

        if genres := anime.get('genres'):
            embed.add_field(name='Genres', value=', '.join((g.get('name') for g in genres)))

        if licensors := anime.get('licensors'):
            embed.add_field(name='Licensors', value='-' + '\n-'.join(licensors))

        if producers := anime.get('producers'):
            embed.add_field(name='Producers', value=', '.join((p.get('name') for p in producers)))

        return embed


CooldownMapping = commands.CooldownMapping
BucketType = commands.BucketType


class Anime(commands.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot
        self.aiojikan = aiojikan = jikanpy.AioJikan(session=bot.session)

        aiojikan.api_cooldowns = [CooldownMapping.from_cooldown(30, 60, BucketType.default),
                                  CooldownMapping.from_cooldown(2, 1, BucketType.default)]

    @commands.group(invoke_without_command=True)
    async def mal(self, ctx: core.Context):
        """My anime list related commands"""
        await ctx.send_help(ctx.command)

    # TODO : Finish covering jikan's api and refactor the commands

    @mal.command(aliases=['planning'], cooldown_after_parsing=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def schedule(self, ctx: core.Context, day: utils.dayconverter = None):
        """Gets the anime schedule for a day in this week"""

        day = day or dt.datetime.now().strftime('%A').lower()

        if raw_data := await ctx.redis.get(ctx.cache_key):
            data = await utils.executor_json_loads(raw_data)

        else:
            data = await self.aiojikan.schedule(day)
            await ctx.redis.set(ctx.cache_key, json.dumps(data), expire=3600)

        if not (anime_data := data.get(day)):
            raise commands.BadArgument("Sorry ! The api I'm communicating with seems to be down")

        source = JikanAnimeSource(anime_data, is_nsfw=ctx.channel.is_nsfw())

        await menus.MenuPages(source).start(ctx, wait=True)

    @mal.command(aliases=['later_season'], cooldown_after_parsing=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def season_later(self, ctx: core.Context):
        """Gets the schedule for the next seasons"""

        if raw_data := await ctx.redis.get(ctx.cache_key):
            data = await utils.executor_json_loads(raw_data)

        else:
            data = await self.aiojikan.season_later()
            await ctx.redis.set(ctx.cache_key, json.dumps(data), expire=86400)

        if not (anime_data := data.get('anime')):
            raise commands.BadArgument("Sorry ! The api I'm communicating with seems to be down")

        source = JikanAnimeSource(anime_data, is_nsfw=ctx.channel.is_nsfw())

        await menus.MenuPages(source).start(ctx, wait=True)




    @mal.before_invoke
    async def check_mal_cooldowns(self, ctx: core.Context):
        for cd in self.aiojikan.api_cooldowns:
            bucket = cd.get_bucket(ctx.message)
            retry_after = bucket.update_rate_limit()

            if retry_after:
                if retry_after < 3:
                    await asyncio.sleep(retry_after)
                else:
                    raise commands.CommandOnCooldown(bucket, retry_after)


def setup(bot: core.Bot):
    bot.add_cog(Anime(bot))
