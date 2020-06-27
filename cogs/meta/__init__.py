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

import inspect
import textwrap
import typing as tp

import discord
from discord.ext import commands

import core
import utils

from . import source

GITHUB_PATH = '/blob/master/'

class Meta(commands.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot

    @commands.command()
    async def source(self, ctx: core.Context, show_full: tp.Optional[bool] = False, *, target: source.CommandConverter = None):
        """Gets the source for a command"""
        if target is None:
            return await ctx.send(f"Drop a star to support my development !\n<{self.bot.config['github']['url']}>")
        
        callback = target.callback
        
        try:
            source_lines, line_number = inspect.getsourcelines(callback)
            
        except OSError:
            raise OSError("Sorry ! I couldn't retrieve this command's source code")

        source_lines = textwrap.dedent(''.join(source_lines))
        module = callback.__module__.replace('.', '/') + '.py'
        github_link = f"{self.bot.config['github']['url']}{GITHUB_PATH}{module}#L{line_number}"
        
        embed = (utils.Embed(title=f"Here's the source the command named \"{target}\" !", default_inline=True)
                 .add_field(name="External view", value=f"[Github]({github_link})")
                 .add_field(name="Module", value=discord.utils.escape_markdown(module))
                 .add_field(name="Line", value=line_number))
        
        if show_full:
            embed.description = utils.codeblock(source_lines[:2000], lang='py')
            menu = utils.OnePage(embed)
            await menu.start(ctx)

        else:
            await ctx.send(embed=embed)


def setup(bot: core.Bot):
    bot.add_cog(Meta(bot))
