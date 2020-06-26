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
from discord.ext import commands, menus

import core

from ..owner import extension


class Owner(commands.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot
        self.make_extension_commands()
    
    # Extension related stuff
    
    @commands.group(name='extension', aliases=['ext'], invoke_without_command=True)
    async def extension(self, ctx: core.Context):
        """Extensions related commands"""
        await ctx.send_help(ctx.command)

    def make_extension_commands(self):
        """Creates all extensions related commands at once"""
        
        @commands.command()
        async def template(ctx: core.Context, *, query: str):
            iterable = extension.get_path(query)
            source = extension.Source(ctx.command.load_type.__name__, [*extension.handle(ctx, iterable)])
            menu = menus.MenuPages(source, delete_message_after=True)
            await menu.start(ctx)

        for name in ('load', 'reload', 'unload'):
            ext_command = template.copy()

            ext_command.name = name
            ext_command.load_type = getattr(self.bot, name + '_extension')
            ext_command.help = name + 's an extension'

            self.extension.add_command(ext_command)

    async def cog_check(self, ctx: core.Context):
        """Owner only cog"""
        return await self.bot.is_owner(ctx.author)
        
        
def setup(bot: core.Bot):
    bot.add_cog(Owner(bot))
