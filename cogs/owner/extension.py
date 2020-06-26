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

from discord.ext import menus

import core
import utils

Result = tp.Tuple[str, str]


def get_path(query: tp.Union[str, None]) -> tp.Generator[str, None, None]:
    """Yields all extensions corresponding to the query"""
    for file in pathlib.Path('./cogs').glob('**/*.py'):
        ext_path = '.'.join(file.parts[:-1]) + '.' + file.stem
        if query is None or query in ext_path.split('.'):
            yield ext_path


def handle(ctx: core.Context, extensions: tp.Iterable[str]) -> tp.Generator[Result, None, None]:
    """Tries to load all corresponding extensions"""
    for ext in extensions:
        try:
            ctx.command.load_type(ext)
        except Exception as e:
            yield ext, e
        else:
            yield ext, "Success"


class Source(menus.ListPageSource):
    def __init__(self, load_type: str, entries: tp.List[Result]):

        if len(entries) < 2:
            entries *= 2

        super().__init__(entries, per_page=5)
        self.load_type = load_type

    def format_page(self, menu: menus.MenuPages, page: tp.List[Result]):
        embed = utils.Embed(title=self.load_type)
        for ext_name, result in page:
            embed.add_field(name=ext_name, value=utils.codeblock(result, lang='py'), inline=False)
        return embed


def setup(bot):
    pass
