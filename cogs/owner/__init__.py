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
import pathlib
import typing as tp

import discord
from discord.ext import commands, menus

import core
import utils

from . import config, extension


class Owner(commands.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot
        self.make_extension_commands()
        bot.loop.create_task(extension.load_all_extensions(bot))

    async def cog_check(self, ctx: core.Context):
        """Owner only cog"""
        if await self.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner(message="Not owner")

    # -- Extensions -- #

    @commands.group(name='extension', aliases=['ext'], invoke_without_command=True)
    async def extension(self, ctx: core.Context):
        """Utils to manage extensions"""
        await ctx.send_help(ctx.command)

    def make_extension_commands(self):
        """Creates all extensions related commands at once"""

        @commands.command()
        async def template(self, ctx: core.Context, query: str, *ignore: tp.Tuple[str]):
            extensions = extension.get_path(query, set(ignore))
            report = [*extension.handle(ctx.command.load_type, extensions)]
            source = extension.Source(ctx.command.load_type.__name__, report)
            await menus.MenuPages(source, delete_message_after=True).start(ctx)

        for name in ('load', 'reload', 'unload'):
            ext_command = template.copy()

            ext_command.name = name
            ext_command.load_type = getattr(self.bot, name + '_extension')
            ext_command.help = name + 's an extension'
            ext_command.cog = self

            self.extension.add_command(ext_command)

    # -- Config -- #

    @commands.group(aliases=['conf'], invoke_without_command=True)
    async def config(self, ctx: core.Context):
        """Utils to manage the config file"""
        await ctx.send_help(ctx.command)

    @config.command(aliases=['show'])
    async def display(self, ctx: core.Context):
        """Displays the json config file"""
        await ctx.author.send(utils.codeblock(json.dumps(self.bot.config, indent=4), lang='json'))
        await ctx.send('Successfully opened the currently loaded config and sent it to you !')

    @config.command(aliases=['refresh'])
    async def reload(self, ctx: core.Context):
        """Reloads the json config file"""
        self.bot.config = conf = await self.bot.loop.run_in_executor(None, config.load)
        await config.display(ctx, conf)

    @config.command(aliases=['change', 'modify'])
    async def edit(self, ctx: core.Context, *, to_exec: str):
        """Edits the json config file"""
        self.bot.config = conf = await self.bot.loop.run_in_executor(None, config.edit, to_exec)
        await config.display(ctx, conf)


def setup(bot: core.Bot):
    bot.add_cog(Owner(bot))
