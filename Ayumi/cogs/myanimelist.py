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
import random
import collections
import typing as tp
import datetime as dt

import jikanpy
import humanize
from discord.ext import commands, menus

import core
import utils
import orjson

BucketType = commands.BucketType
CooldownMapping = commands.CooldownMapping
Rating = collections.namedtuple('Rating', 'desc nsfw')

ANIME_RATINGS = {
    'G': Rating(desc='G - All ages', nsfw=False),
    'PG': Rating(desc='Children', nsfw=False),
    'PG-13': Rating(desc='Teens 13 or older', nsfw=False),
    'R': Rating(desc='17+ recommended (violence & profanity)', nsfw=False),  # guess that's where we draw the line

    'R+': Rating(desc='Mild nudity (may also contain violence & profanity)', nsfw=True),
    'Rx': Rating(desc='Hentai (extreme sexual content/nudity)', nsfw=True)

}

EXAMPLE_ANIMES = 'no game no life', 'jojo', 'pokemon'
EXAMPLE_MANGAS = 'attack on Titan', 'demon slayer', 'death note'

class JikanAnimeSource(menus.ListPageSource):
    def __init__(self, footer: str, *, entries: tp.List[dict], is_nsfw: bool):
        self.footer = footer

        if not is_nsfw:
            entries = [e for e in entries if not e.get('r18', False)]

        super().__init__(entries, per_page=1)

    @staticmethod
    def format_named_data(data: tp.List[dict]):
        return '\n'.join([f"[{d.get('name')}]({d.get('url')})" for d in data])

    @staticmethod
    def format_date(data: str):
        try:
            iso = dt.datetime.fromisoformat(data)
            return humanize.naturaldate(iso)

        except ValueError:
            return data

    def format_page(self, menu: menus.Menu, anime: dict):
        """An extremely lazy way to put everything together"""

        title = [anime.get('title'), ]

        if score := anime.get('score'):
            title.append(f"Score : {score}")


        embed = utils.Embed(title=' | '.join(title),

                            url=anime.get('url'),

                            description=(anime.get('synopsis') or 'Not found')[:2000])  # might get none

        embed.set_footer(text=self.footer)

        funcs = (
            lambda: embed.set_thumbnail(url=anime['image_url']),
            lambda: embed.add_field(name='Genres', value=self.format_named_data(anime['genres'])),
            lambda: embed.add_field(name='Producers', value=self.format_named_data(anime['producers'])),
            lambda: embed.add_field(name='Licensors', value='-' + '\n-'.join(anime['licensors'])),
            lambda: embed.add_field(name='Rank', value=anime['rank']),
            lambda: embed.add_field(name='Start date', value=self.format_date(anime['start_date'])),
            lambda: embed.add_field(name='End date', value=self.format_date(anime['end_date']))
        )

        for fn in funcs:
            try:
                fn()
            except KeyError:
                pass

        return embed


class MyAnimeList(commands.Cog):
    """The category containing all my anime list related commands"""

    def __init__(self, bot: core.Bot):
        self.bot = bot
        self.aiojikan = aiojikan = jikanpy.AioJikan(session=bot.session)
        self._make_mal_schedule_commands()
        self._make_mal_season_commands()
        self._make_mal_top_subcommands()

        aiojikan.api_cooldowns = [CooldownMapping.from_cooldown(30, 60, BucketType.default),
                                  CooldownMapping.from_cooldown(2, 1, BucketType.default)]

    # -- My anime list -- #

    @utils.group(invoke_without_command=True)
    async def mal(self, ctx: core.Context):
        """
        My anime list-related commands,
        Please note that those most of them
        are api-dependant and might randomly
        be down for an undefined period of time
        """
        await ctx.send_help(ctx.command)


    # TODO : Finish covering jikan's api and refactor the commands

    # Schedule subcommands

    async def _mal_schedule_handler(self, ctx: core.Context, day: str):
        """Handles the requests for schedules"""
        if raw_data := await ctx.redis.get(ctx.cache_key):
            data = orjson.loads(raw_data)

        else:
            data = await self.aiojikan.schedule(day)

            key = f"{ctx.qname} {day}"

            str_data = orjson.dumps(data)

            await ctx.redis.set(key, str_data, expire=43200)

        if not (anime_data := data.get(day)):

            raise commands.BadArgument("Sorry ! The api I'm communicating with seems to be down")

        source = JikanAnimeSource(f"Planning for {day.capitalize()}",
                                  entries=anime_data,
                                  is_nsfw=ctx.channel.is_nsfw())

        menu = menus.MenuPages(source, delete_message_after=True)
        await menu.start(ctx, wait=True)

    @mal.group(name='schedule', aliases=['planning'], invoke_without_command=True)
    async def mal_schedule(self, ctx: core.Context):
        """Gets the anime schedule for today, or another day in the week"""

        today = dt.datetime.today()

        curr_day = today.strftime('%A')

        lower = curr_day.lower()

        await self._mal_schedule_handler(ctx, lower)

    @mal_schedule.command(name='today', aliases=['now'])
    async def mal_schedule_today(self, ctx: core.Context):
        """Gets the anime schedule for today"""
        await self.mal_schedule(ctx)

    def _make_mal_schedule_commands(self):
        """Adds a subcommand corresponding to each day of the week"""
        for day in utils.DAYS:
            help_ = f'Shows the schedule for this {day}'

            @self.mal_schedule.command(name=day, aliases=[day[:3]], help=help_, cog=self)
            async def mal_schedule_template(self, ctx: core.Context):
                await self._mal_schedule_handler(ctx, ctx.cname)

    # Season subcommands
    async def _mal_season_handler(self, ctx: core.Context, season: str, year: int):
        """Handles the requests for seasons"""
        if raw_data := await ctx.redis.get(ctx.cache_key):
            data = orjson.loads(raw_data)

        else:
            data = await self.aiojikan.season(year=year, season=season)

            str_data = orjson.dumps(data)

            await ctx.redis.set(ctx.cache_key, str_data, expire=43200)

        if not (anime_data := data.get('anime')):
            raise commands.BadArgument("Sorry ! The api I'm communicating with seems to be down")

        source = JikanAnimeSource(f"Planning for {season} - {year}",
                                  entries=anime_data,
                                  is_nsfw=ctx.channel.is_nsfw())

        menu = menus.MenuPages(source, delete_message_after=True)
        await menu.start(ctx, wait=True)

    @mal.group(name='season', invoke_without_command=True)
    async def mal_season(self, ctx: core.Context):
        """Gets the planning for the current season or another season of any year"""
        for (start, end), value in utils.SEASONS.items():
            if start <= dt.datetime.today().timetuple().tm_yday <= end:
                season = value
                break
        else:
            season = 'winter'

        await self._mal_season_handler(ctx, season, dt.datetime.today().year)

    def _make_mal_season_commands(self):
        """Adds a subcommand corresponding to each season of the year"""
        for season in utils.SEASONS.values():
            
            help_ = f"Shows the anime planning for a {season} of this year, or another"
            example_args = [tuple(range(2000, dt.datetime.now().year))]
            
            @self.mal_season.command(name=season,help=help_, example_args=example_args, cog=self)
            async def mal_season_template(self, ctx: core.Context, year: tp.Optional[int] = None):

                year = year or dt.datetime.now().year

                await self._mal_season_handler(ctx, ctx.cname, year)

    @mal_season.command(name='later', cooldown_after_parsing=True)
    async def mal_season_later(self, ctx: core.Context):
        """Gets the schedule for the next seasons (use season-later to get a precise one)"""
        if raw_data := await ctx.redis.get(ctx.cache_key):
            data = orjson.loads(raw_data)
        else:
            data = await self.aiojikan.season_later()
            await ctx.redis.set(ctx.cache_key, orjson.dumps(data), expire=43200)

        if not (anime_data := data.get('anime')):
            raise commands.BadArgument("Sorry ! The api I'm communicating with seems to be down")

        source = JikanAnimeSource("Planning for next seasons",
                                  entries=anime_data,
                                  is_nsfw=ctx.channel.is_nsfw())

        menu = menus.MenuPages(source, delete_message_after=True)
        await menu.start(ctx, wait=True)

    # Top subcommands
    async def _mal_top_handler(self, ctx: core.Context, media: tp.Literal['anime', 'manga'], page: int):
        if raw_data := await ctx.redis.get(ctx.cache_key):
            data = orjson.loads(raw_data)

        else:
            data = await self.aiojikan.top(type=media, page=page)
            await ctx.redis.set(ctx.cache_key, orjson.dumps(data), expire=43200)

        if not (anime_data := data.get('top')):
            raise commands.BadArgument("Sorry ! The api I'm communicating with seems to be down")

        source = JikanAnimeSource("Top animes", entries=anime_data,
                                  is_nsfw=ctx.channel.is_nsfw())

        menu = menus.MenuPages(source, delete_message_after=True)
        await menu.start(ctx, wait=True)

    @mal.group(name='top', only_sends_help=True, invoke_without_command=True)
    async def mal_top(self, ctx: core.Context):
        """Gets the current top animes or manga on my anime list"""
        await ctx.send_help(ctx.command)

    def _make_mal_top_subcommands(self):
        for media in ('anime', 'manga'):
            @self.mal_top.command(name=media, help=f'Gets the top ranked {media}', example_args=[tuple(range(5))], cog=self)
            async def mal_top_template(self, ctx: core.Context, page: int = 0):
                await self._mal_top_handler(ctx, ctx.cname, page)

    @mal.group(name='search', invoke_without_command=True, only_sends_help=True)
    async def mal_search(self, ctx: core.Context):
        """Searches something on my anime list"""
        await ctx.send_help(ctx.command)

    @mal_search.command(name='anime', example_args=[EXAMPLE_ANIMES])
    async def mal_search_anime(self, ctx: core.Context, *, name: str):
        response = await self.aiojikan.search(ctx.cname, name)

        source = JikanAnimeSource(f"Here are the results for the {ctx.cname} named {name}",
                                  entries=response['results'],
                                  is_nsfw=ctx.channel.is_nsfw())

        await menus.MenuPages(source, delete_message_after=True).start(ctx)

    @mal_search.command(name='manga', example_args=[EXAMPLE_MANGAS])
    async def mal_search_manga(self, ctx: core.Context, *, name: str):
        results = await self.aiojikan.search(ctx.cname, name)
        source = JikanAnimeSource(f"Here are the results for the {ctx.cname} named {name}",
                                  entries=results,
                                  is_nsfw=ctx.channel.is_nsfw())

        await menus.MenuPages(source, delete_message_after=True).start(ctx)

    @mal.before_invoke
    async def check_mal_cooldowns(self, ctx: core.Context):
        
        await ctx.author.send('applied rate limits')
        
        for cd in self.aiojikan.api_cooldowns:
            bucket = cd.get_bucket(ctx.message)
            retry_after = bucket.update_rate_limit()

            if retry_after:
                if retry_after < 3:
                    await asyncio.sleep(retry_after)
                else:
                    raise commands.CommandOnCooldown(bucket, retry_after)


def setup(bot: core.Bot):
    bot.add_cog(MyAnimeList(bot))
