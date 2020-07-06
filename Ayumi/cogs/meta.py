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
import random
import textwrap
import typing as tp

import discord
from discord.ext import commands, menus

import core
import utils

GITHUB_PATH = '/blob/master/'
CONTAINS_COMMANDS = commands.Cog, commands.Group

SPACES   = '    '
VERTICAL = '│   '
T_BRANCH = '├── '
L_BRANCH = '└── '
CIRCLE   = '○ '


class CogAndGroupHelpSource(utils.ListPageSource):
    def __init__(self, entries: tp.List[str], *, entity: tp.Union[commands.Cog, commands.Group], title: str):  # future proofing
        super().__init__(entries, per_page=1)

        self.entity = entity

        self.walked_commands = [c for c in entity.walk_commands() if not getattr(c, 'only_sends_help', False)]

        self.title = title.format(entity)


    def format_page(self, menu: menus.MenuPages, page: str):
        """Formats the page into an embed"""

        embed = utils.Embed(title=self.title, description=page)

        embed.add_field(name='Description', value=getattr(self.entity, 'help', self.entity.description))

        embed.set_footer(text=f'Page {menu.current_page + 1} out of {self.get_max_pages()}')

        if not self.walked_commands:  # we got an empty cog / group or one that only sends help
            return embed

        example_amount = min(3, len(self.walked_commands))

        example_commands = random.sample(self.walked_commands, k=example_amount)

        # we might have a cog that mixes both subclassed and default commands

        examples = [getattr(c, 'get_example', lambda _: None)(menu.ctx) for c in example_commands]

        if not (filtered_examples := [*filter(None, examples)]):
            return embed

        embed.add_field(name='Examples', value='\n'.join(filtered_examples))

        return embed


class HelpCommand(commands.MinimalHelpCommand):

    async def send_bot_help(self, mapping):
        await self.display_menu(self.context.bot.cogs.values())


    @staticmethod
    def sort_by_weekdays_and_seasons(command: commands.Command) -> str:
        """Special sort that takes into accounts days and seasons"""

        name = command.name

        return utils.coalesce(

            lambda: str(utils.DAYS.index(name)),

            lambda: str(tuple(utils.SEASONS.values()).index(name)),

            ignored_exc=ValueError,

            default=name
        )

    async def tree(self, contents: tp.Union[commands.Cog, commands.Group],
                   *, prefix: str = '') -> tp.AsyncGenerator[str, None]:
        """Yields some fancy lines to display a tree"""

        if isinstance(contents, commands.Cog):

            contents = contents.get_commands()

        elif isinstance(contents, commands.GroupMixin):

            contents = contents.commands

        contents = await self.filter_commands(contents, sort=True, key=self.sort_by_weekdays_and_seasons)

        pointers = [T_BRANCH] * (len(contents) - 1) + [L_BRANCH]

        for pointer, entity in zip(pointers, contents):

            cname = getattr(entity, 'name', None) or getattr(entity, 'qualified_name')

            signature = getattr(entity, 'signature', '')

            yield f"{prefix}{pointer}{cname} {signature}"


            if isinstance(entity, (commands.Cog, commands.Group)):

                extension = VERTICAL if pointer == T_BRANCH else SPACES

                async for line in self.tree(entity, prefix=prefix + extension):
                    yield line


    async def display_grouped_menu(self, title: str, entity: tp.Union[commands.Group, commands.Cog]):
        """Handles the menu for cog and group help"""
        paginator = commands.Paginator(max_size=2048)

        lines = [line async for line in self.tree(entity)]

        dedented = textwrap.dedent('\n'.join(lines)).split('\n')  # lazy way to dedent it

        for line in dedented:
            paginator.add_line(line)

        source = CogAndGroupHelpSource(paginator.pages, entity=entity, title=title)

        menu = menus.MenuPages(source, delete_message_after=True)

        await menu.start(self.context, wait=True)


    async def send_cog_help(self, cog: commands.Cog):
        title = "Here are the commands inside of the category {0.qualified_name}"
        await self.display_grouped_menu(title, cog)


    async def send_group_help(self, group: commands.Group):
        title = "Here are {0.qualified_name}'s subcommands"
        await self.display_grouped_menu(title, group)


class CommandConverter(commands.Converter):
    async def convert(self, ctx: core.Bot, arg: str):
        if co := ctx.bot.get_command(arg.lower()):
            return co

        else:
            raise commands.BadArgument(f"Sorry ! I couldn't find the command named \"{arg}\"")


class Meta(commands.Cog):
    """
    Commands providing information about the myself !
    """
    def __init__(self, bot):
        self._original_help_command = bot.help_command

        bot.help_command = HelpCommand()

        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    # -- Source -- #
    @commands.command(aliases=['src'])
    @commands.max_concurrency(1, commands.BucketType.user)
    async def source(self, ctx: core.Context, show_full: tp.Optional[bool] = True, *,
                     target: CommandConverter = None):
        """Gets the source for a command"""
        if target is None:
            return await ctx.send(f"Drop a star to support my development !\n<{self.bot.config['github']['url']}>")

        callback = target.callback

        try:
            source_lines, line_number = inspect.getsourcelines(callback)

        except OSError:
            raise commands.BadArgument("Sorry ! I couldn't retrieve this command's source code")

        source_lines = textwrap.dedent(''.join(source_lines))

        module = callback.__module__.replace('.', '/') + '.py'

        github_link = f"{self.bot.config['github']['url']}{GITHUB_PATH}{module}#L{line_number}"

        embed = (utils.Embed(title=f"Here's the source the command named \"{target}\" !", default_inline=True)
                 .add_field(name="External view", value=f"[Github]({github_link})")
                 .add_field(name="Module", value=discord.utils.escape_markdown(module))
                 .add_field(name="Line", value=line_number))

        if show_full:
            src = utils.codeblock(source_lines[:2000], lang='py')
            await utils.OnePage({'embed': embed, 'content': src}).start(ctx)

        else:
            await ctx.send(embed=embed)


def setup(bot: core.Bot):
    bot.add_cog(Meta(bot))
