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

import json
import keyword

from jishaku import codeblocks

import core
import main
import utils

load = main.load   # no need for duplicates

KEYWORDS = tuple(keyword.kwlist)


def edit(to_exec: str) -> dict:
    """
    Edits the config file according to the query, using dot or normal dict notation
    There must be a better way to do this, tho
    """
    config = load()

    _, content = codeblocks.codeblock_converter(to_exec)

    exec(content, {'config': config})

    with open(main.CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

    return config


async def display(ctx: core.Context, conf: dict):
    """Sends the current config file to the owner"""
    await ctx.author.send(utils.codeblock(json.dumps(conf, indent=4), lang='json'))
    await ctx.send(f'Successfully {ctx.command.name}ed the config file and sent it to you !')


def setup(bot: core.Bot):
    pass
