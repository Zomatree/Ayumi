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

import collections.abc
import functools
import typing as tp

from discord.ext import commands


class Context(commands.Context):

    @functools.cached_property
    def qname(self) -> tp.Union[str, None]:
        return getattr(self.command, 'qualified_name', None)

    @functools.cached_property
    def all_args(self) -> list:
        args = [arg for arg in self.args if not isinstance(arg, (commands.Cog, commands.Context))]
        kwargs = [*self.kwargs.values()]
        return args + kwargs

    @property
    def cache_key(self) -> list:
        return self._altered_cache_key or [self.qname] + self.all_args

    @cache_key.setter
    def cache_key(self, key: collections.abc.Hashable) -> None:
        """Sets another key to use for this Context"""
        self._altered_cache_key = key

    @property
    def redis(self):
        return self.bot.redis
