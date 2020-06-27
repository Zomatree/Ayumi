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
import re

import core
import main
import utils

DOT_PATTERN = re.compile(r"(.+\s?)=")


def load() -> dict:
    """Opens the config file and return it as a dict"""
    with open(main.CONFIG_PATH, 'r') as f:
        return json.load(f)  # not sure about whether open or json.load is blocking, so they both run in exec


def edit(to_exec: str) -> dict:
    """
    Edits the config file according to the query, using dot or normal dict notation
    There must be a better way to do this, tho
    """
    if not all(char in to_exec for char in ('[]')):

        splitted = to_exec.replace(' ', '').split('=')
        splitted[0] = "['" + splitted[0].replace('.', "']['") + "']"

        to_exec = ' = '.join(splitted)

    config = load()

    exec('config' + to_exec, locals())

    with open(main.CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)

    return config


async def display(ctx: core.Context, conf: dict):
    """Sends the current config file to the owner"""
    await ctx.author.send(utils.codeblock(json.dumps(conf, indent=4), lang='json'))
    await ctx.send(f'Successfully {ctx.command.name}ed the config file and sent it you !')


def setup(bot: core.Bot):
    pass
