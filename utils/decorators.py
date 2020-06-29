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

import functools
import types
import typing as tp

from discord.ext import commands


def multiple_cooldowns(*cooldowns: tp.Tuple[commands.CooldownMapping]):
    """A decorators that allows a command to have multiple cooldowns at once"""
    def wrapper(func: types.FunctionType):
        func.__multiple_cooldowns__ = cooldowns

        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            ctx = args[1] if isinstance(args[0], commands.Cog) else args[0]

            for cd in func.__multiple_cooldowns__:
                if retry_after := cd.get_bucket(ctx.message).update_rate_limit():
                    raise commands.CommandOnCooldown(cd, retry_after)

            return await func(*args, **kwargs)

        return wrapped

    return wrapper
