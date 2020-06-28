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

import os
import json
import core

CONFIG_PATH = 'config.json'


def load() -> dict:  # we reuse this to edit the config, in an executor ofc, because aiofiles is dum dum
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


if __name__ == '__main__':

    # Jishaku env

    for env in ('NO_UNDERSCORE', 'HIDE', 'RETAIN'):
        os.environ['JISHAKU_' + env] = 'True'

    # Bot

    config = load()

    # Init

    bot = core.Bot()
    disc = config['discord']

    bot._config = config
    bot.owner_id = int(disc['owner_id'])
    bot.run(disc['token'])
