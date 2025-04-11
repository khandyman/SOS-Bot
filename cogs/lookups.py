import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from classes.database import Database
from classes.helpers import Helpers


class Lookups(commands.Cog):
    """
    All slash commands that read information from database
    """
    def __init__(self, bot, database, helper):
        self._bot = bot
        self._database = database
        self._helper = helper

    async def discord_name_autocompletion(
            self,
            ctx: discord.AutocompleteContext
    ):
        """
        Create a filtering list of discord names
        :param ctx: the application context of the bot
        :return: filtered list
        """
        current_value = ctx.value
        discord_list = self._helper.get_all_discord_names('name')

        return [choice for choice in discord_list if current_value.lower() in choice.lower()]

    async def combined_name_autocompletion(
            self,
            ctx: discord.AutocompleteContext
    ):
        """
        Create a filtering list of combined char names and discord names
        :param ctx: the application context of the bot
        :return: filtered list
        """
        current_value = ctx.value

        name_list = self._helper.get_combined_names(self._database.get_all_characters())
        name_list.sort()

        return [choice for choice in name_list if current_value.lower() in choice.lower()]

    @discord.slash_command(name="lookup_characters",
                           description="Find a user's characters by their EQ name, "
                                       "Discord user name, or Discord display name",
                           )
    async def lookup_characters(
            self,
            ctx: discord.ApplicationContext,
            member_name: discord.Option(
                str,
                description='[ EverQuest ] [ Discord ]',
                autocomplete=combined_name_autocompletion
            )
    ):
        """
        find all characters associated with a
        given eq character name
        :param ctx: the application context of the bot
        :param member_name: string selected by user (required)
        :return: none
        """
        # # this slash command available to all users
        target_role = discord.utils.get(ctx.guild.roles, name="Seeker")

        # if validate_role returns false, user is not authorized,
        # so exit function
        if not self._helper.validate_role(ctx.author.roles, target_role):
            await self.not_authorized(ctx)
            return

        self._helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        # obtain the user's selection and get just the string name
        option_selected = ctx.selected_options[0]['value']
        bracket = option_selected.find(']')
        user_choice = option_selected[2:bracket - 1]

        # get the list of chars from database
        results = self._database.lookup_eq(user_choice)
        # get discord name that matches discord id from database
        discord_name = self._helper.get_discord_name(
            self._database.lookup_discord_id(user_choice)
        )

        # if no matches found, notify user then exit
        if len(results) == 0:
            await ctx.respond(
                f"```No records found for {user_choice}.\n"
                f"Please try again.```",
                ephemeral=True
            )
            return

        # if matches found display discord id,
        # then print table of character results
        await ctx.respond(
            f"```List of characters for: {discord_name}\n"
            f"\n{self._helper.format_message(results)}```",
            ephemeral=True
        )

    @discord.slash_command(
        name="find_main_from_discord",
        description="Find a user's main character"
    )
    async def find_main_from_discord(
            self,
            ctx: discord.ApplicationContext,
            discord_name: discord.Option(
                str,
                description='Discord account name',
                autocomplete=discord_name_autocompletion
            )
    ):
        """

        :param ctx: the application context of the bot
        :param discord_name: string selected from dropdown (required)
        :return: none
        """
        # this slash command available to all users
        target_role = discord.utils.get(ctx.guild.roles, name="Seeker")

        # if validate_role returns false, user is not authorized,
        # so exit function
        if not self._helper.validate_role(ctx.author.roles, target_role):
            await self.not_authorized(ctx)
            return

        self._helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        discord_id = self._helper.get_discord_id(discord_name, 'account')

        # if no discord id found, notify user and exit function
        if discord_id == "":
            await ctx.respond(
                f'```Discord ID not found for {discord_name}.\n'
                f'Unable to query database.```',
                ephemeral=True
            )
            return

        results = self._database.lookup_main(discord_id)

        # if results > 0, match was found
        if len(results) > 0:
            await ctx.respond(
                f'```{discord_name} = {results[0]['char_name']}```',
                ephemeral=True
            )
        else:
            await ctx.respond(
                f'```No records found for {discord_name}.```',
                ephemeral=True
            )

    @discord.slash_command(
        name="get_all_mains",
        description="Get a list of all mains"
    )
    async def get_all_mains(
            self,
            ctx: discord.ApplicationContext
    ):
        """
        get list of all characters in database with char_type of 'Main'
        :param ctx: the application context of the bot
        :return: none
        """
        # this slash command only available to officers
        target_role = discord.utils.get(ctx.guild.roles, name="Officer")

        # if validate_role returns false, user is not authorized,
        # so exit function
        if not self._helper.validate_role(ctx.author.roles, target_role):
            await self.not_authorized(ctx)
            return

        self._helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        results = self._database.get_all_mains()
        main_list = f"Main characters in Seekers Of Souls...\n"

        # print one character per line
        for result in results:
            main_list = main_list + f"{result}\n"

        main_list = main_list + f"Total count of mains: {len(results)}"

        await ctx.respond(
            f"```{main_list}```",
            ephemeral=True
        )

    async def not_authorized(
            self,
            ctx: discord.ApplicationContext):
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
            ephemeral=True
        )


def setup(bot):
    load_dotenv()

    guild = os.getenv('DISCORD_GUILD')
    helper = Helpers(bot, guild)
    database = Database()

    bot.add_cog(Lookups(bot, database, helper))
