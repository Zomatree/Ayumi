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
import jishaku.codeblocks
from discord.ext import commands, menus

import core
import main
import utils

ExtensionResult = tp.Tuple[str, str]


IGNORED_COGS = {'cogs.owner'}

EXTENSIONS_IGNORE = (commands.ExtensionAlreadyLoaded, 
                     commands.ExtensionNotLoaded,
                     commands.NoEntryPointError, 
                     commands.ExtensionNotFound)


class ExtensionSource(menus.ListPageSource):
    def __init__(self, load_type: str, entries: tp.List[ExtensionResult]):
        super().__init__(entries, per_page=2)
        self.load_type = load_type

    def format_page(self, menu: menus.MenuPages, page: tp.List[ExtensionResult]) -> utils.Embed:
        """Formats the page into an embed"""

        embed = utils.Embed(title=self.load_type, color=discord.Color.orange(), default_inline=False)

        for ext_name, error in page:

            clean_ext_name = discord.utils.escape_markdown(ext_name)

            if not isinstance(error, str):

                if isinstance(error, EXTENSIONS_IGNORE):  # those errors aren't worth a full traceback
                    error = str(error)

                else:
                    error = utils.format_exception(*utils.exc_info(error), limit=4)

            embed.add_field(name=clean_ext_name, value=utils.codeblock(error, lang='py')[:1024])

        return embed




class Owner(commands.Cog):
    def __init__(self, bot: core.Bot):
        self.bot = bot

        self.make_extension_commands()

        bot.loop.create_task(self.load_all_extensions())


    async def cog_check(self, ctx: core.Context):
        """Owner only cog"""

        if await self.bot.is_owner(ctx.author):
            return True

        raise commands.NotOwner(message="Not owner")

    # -- Extensions -- #

    @staticmethod
    def get_extension_path(query: str, exclude: set = set()) -> tp.Generator[str, None, None]:
        """Yields all extensions corresponding to the query"""

        for file in pathlib.Path('./cogs').glob('**/*.py'):

            ext_path = '.'.join(file.parts[:-1]) + '.' + file.stem

            if (query == '*' or query in ext_path.split('.')) and not exclude & {ext_path}:

                yield ext_path


    @staticmethod
    def handle_extension(func: callable, extensions: tp.Iterable[str]
                         ) -> tp.Generator[ExtensionResult, None, None]:
        """Tries to load all corresponding extensions"""
        for ext in extensions:
            try:
                func(ext)

            except Exception as error:
                yield ext, error

            else:
                yield ext, "Success"

    async def load_all_extensions(self) -> None:
        """Loads all extensions and sends all pages in the log channel"""

        extensions = self.get_extension_path('*', IGNORED_COGS)

        source = ExtensionSource('load_extension', [*self.handle_extension(self.bot.load_extension, extensions)])

        for index in range(source.get_max_pages()):

            page = source.format_page(None, await source.get_page(index))

            await self.bot.log_webhook.send(embed=page)


    @utils.group(name='extension', aliases=['ext'], invoke_without_command=True, only_sends_help=True)
    async def extension(self, ctx: core.Context):
        """Utils to manage extensions"""
        await ctx.send_help(ctx.command)

    def make_extension_commands(self):
        """Creates all extensions related commands at once"""

        @utils.command()
        async def template(self, ctx: core.Context, query: str, *ignore: tp.Tuple[str]):
            extensions = self.get_extension_path(query, IGNORED_COGS | set(ignore))
            report = [*self.handle_extension(ctx.command.load_type, extensions)]
            source = ExtensionSource(ctx.command.load_type.__name__, report)
            await menus.MenuPages(source, delete_message_after=True).start(ctx)

        for name in ('load', 'reload', 'unload'):
            ext_command = template.copy()

            ext_command.name = name
            ext_command.load_type = getattr(self.bot, name + '_extension')
            ext_command.help = name + 's an extension'
            ext_command.cog = self

            self.extension.add_command(ext_command)

    # -- Config -- #

    @utils.group(aliases=['conf'], invoke_without_command=True, only_sends_help=True)
    async def config(self, ctx: core.Context):
        """Utils to manage the config file"""
        await ctx.send_help(ctx.command)

    @config.command(aliases=['show'])
    async def display(self, ctx: core.Context):
        """Displays the json config file"""
        await ctx.author.send(utils.codeblock(json.dumps(self.bot.config, indent=4), lang='json'))
        await ctx.send('Successfully opened the currently loaded config and sent it to you !')

    @staticmethod
    async def display_config(ctx: core.Context, conf: dict):
        """Sends the current config file to the owner"""
        await ctx.author.send(utils.codeblock(json.dumps(conf, indent=4), lang='json'))
        await ctx.send(f'Successfully {ctx.command.name}ed the config file and sent it to you !')

    @config.command(aliases=['refresh'])
    async def reload(self, ctx: core.Context):
        """Reloads the json config file"""
        self.bot.config = conf = await ctx.bot.loop.run_in_executor(None, main.load_config)
        await self.display_config(ctx, conf)

    @config.command(aliases=['change', 'modify'])
    async def edit(self, ctx: core.Context, *, to_exec: str):
        """Edits the json config file"""

        config = main.load_config()

        _, content = jishaku.codeblocks.codeblock_converter(to_exec)

        exec(content, {'config': config})

        with open(main.CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)

        await self.display_config(ctx, config)


def setup(bot: core.Bot):
    bot.add_cog(Owner(bot))
