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

import random

import async_cleverbot as ac
import discord
from discord.ext import commands
import typing as tp
import core


class Misc(commands.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot
        self.cleverbot = cb = ac.Cleverbot(api_key=bot.config['travitia']['token'],
                                           session=bot.session, context=ac.DictContext())

        cb.emotions = tuple(ac.Emotion)

    # -- Cleverbot -- #

    @commands.Cog.listener('on_message')
    async def cleverbot_listener(self, msg: discord.Message, *, ask: str = ''):
        """Handles the implementation for cleverbot"""
        content = msg.content
        bot = self.bot
        cb = self.cleverbot

        # Filtering out messages that don't start with the bot's mention
        if msg.author.bot:
            return

        if not ask:
            for mention in (bot.user.mention + ' ', f'<@!{bot.user.id}> '):
                if content.startswith(mention):
                    ask = content[len(mention):]
                    break
            else:
                return

        key = f'cleverbot {msg.author.id}'

        emotion_index: tp.Optional[int] = await bot.redis.get(key)

        if emotion_index is None:
            emotion_index = random.randint(0, len(ac.Emotion) - 1)
            await bot.redis.set(key, emotion_index, expire=600)

        emotion = cb.emotions[int(emotion_index)]  # storing only the index is a bit lighter, I guess

        async with msg.channel.typing():
            response = await cb.ask(query=ask, id_=msg.author.id, emotion=emotion)

        await msg.channel.send(f"> {msg.content}\n{msg.author.mention}, {response.text}")

    @commands.command()
    async def ask(self, ctx: core.Context, *, text: str):
        """Ask something, you can also mention me and write a message"""
        await self.cleverbot_listener(ctx.message, ask=text)


def setup(bot: core.Bot):
    bot.add_cog(Misc(bot))
