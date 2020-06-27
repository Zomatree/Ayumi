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

import pathlib
import typing as tp

import discord
from discord.ext import menus, commands

import core
import utils

Result = tp.Tuple[str, str]


def get_path(query: str, exclude: set = set()) -> tp.Generator[str, None, None]:
    """Yields all extensions corresponding to the query"""
    for file in pathlib.Path('./cogs').glob('**/*.py'):
        ext_path = '.'.join(file.parts[:-1]) + '.' + file.stem
        if (query == '*' or query in ext_path.split('.')) and not exclude & {ext_path}:
            yield ext_path


def handle(func: callable, extensions: tp.Iterable[str]) -> tp.Generator[Result, None, None]:
    """Tries to load all corresponding extensions"""
    for ext in extensions:
        try:
            func(ext)
        except Exception as error:
            yield ext, error
        else:
            yield ext, "Success"


EXTENSIONS_IGNORE = (commands.ExtensionAlreadyLoaded, commands.ExtensionNotLoaded,
                     commands.NoEntryPointError, commands.ExtensionNotFound)


class Source(menus.ListPageSource):
    def __init__(self, load_type: str, entries: tp.List[Result]):
        super().__init__(entries, per_page=2)
        self.load_type = load_type

    def format_page(self, menu: menus.MenuPages, page: tp.List[Result]) -> utils.Embed:
        """Formats the page into an embed"""
        embed = utils.Embed(title=self.load_type, color=discord.Color.orange())

        for ext_name, error in page:
            clean_ext_name = discord.utils.escape_markdown(ext_name)

            if not isinstance(error, str):

                if isinstance(error, EXTENSIONS_IGNORE):  # those errors aren't worth a full traceback
                    error = str(error)

                else:
                    error = utils.format_exception(*utils.exc_info(error))

            embed.add_field(name=clean_ext_name, value=utils.codeblock(error, lang='py'), inline=False)

        return embed


async def load_all_extensions(bot: core.Bot):
    """Loads all extensions and sends all pages in the log channel"""
    extensions = get_path('*', {'cogs.owner.__init__'})
    source = Source('load_extension', [*handle(bot.load_extension, extensions)])

    for index in range(source.get_max_pages()):
        page = source.format_page(None, await source.get_page(index))
        await bot.log_webhook.send(embed=page)


def setup(bot: core.Bot):
    pass
