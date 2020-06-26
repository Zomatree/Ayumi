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
import logging
import os

import core

if __name__ == '__main__':

    # Logging

    logger = logging.getLogger('discord')
    logger.setLevel(logging.WARNING)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    # Jishaku env

    for env in ('NO_UNDERSCORE', 'HIDE', 'RETAIN'):
        os.environ['JISHAKU_' + env] = 'True'

    # Bot

    with open('config.json', 'r') as f:
        config = json.load(f)

    disc = config['discord']
    bot = core.Bot(command_prefix=disc['prefix'])
    bot.config = config
    bot.run(disc['token'])
