import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
from classes.database import Database
from classes.helpers import Helpers
from classes.tracker import Tracker

class Updates(commands.Cog):
    """
    All slash commands that update information in database
    """
    def __init__(self, bot, database, helper, tracker):
        self._bot = bot
        self._database = database
        self._helper = helper
        self._tracker = tracker

        self._char_list = []
        self._discord_list = []
        self._race_list = []
        self._class_list = []
        self._type_list = []

    async def char_name_autocompletion(
            self,
            ctx: discord.AutocompleteContext,
    ):
        """
        Create a filtering list of char names
        :param ctx: the application context of the bot
        :return: filtered list
        """
        current_value = ctx.value

        self._char_list = self._database.get_all_char_names()

        return [choice for choice in self._char_list if current_value.lower() in choice.lower()]

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

        self._discord_list = self._helper.get_all_discord_names('display')

        return [choice for choice in self._discord_list if current_value.lower() in choice.lower()]

    async def races_autocompletion(
            self,
            ctx: discord.AutocompleteContext
    ):
        """
        Create a filtering list of eq races
        :param ctx: the application context of the bot
        :return: filtered list
        """
        current_value = ctx.value

        if len(self._race_list) == 0:
            self._race_list = self._helper.get_races()

        return [choice for choice in self._race_list if current_value.lower() in choice.lower()]

    async def classes_autocompletion(
            self,
            ctx: discord.AutocompleteContext
    ):
        """
        Create a filtering list of eq classes
        :param ctx: the application context of the bot
        :return: filtered list
        """
        current_value = ctx.value

        if len(self._class_list) == 0:
            self._class_list = self._helper.get_classes()

        return [choice for choice in self._class_list if current_value.lower() in choice.lower()]

    async def types_autocompletion(
            self,
            ctx: discord.AutocompleteContext
    ):
        """
        Create a filtering list of database char types
        :param ctx: the application context of the bot
        :return: filtered list
        """
        current_value = ctx.value

        if len(self._type_list) == 0:
            self._type_list = self._helper.get_types()

        return [choice for choice in self._type_list if current_value.lower() in choice.lower()]

    def add_member(
            self,
            discord_id
    ):
        try:
            if self._database.insert_member(discord_id) > 0:
                return True
            else:
                return False
        except Exception as err:
            if "Duplicate entry" in str(err):
                return True
            else:
                return False

    @discord.slash_command(name="add_character", description="Add a character to the database")
    async def add_character(
            self,
            ctx: discord.ApplicationContext,
            discord_name: discord.Option(
                str,
                description='Discord display name',
                autocomplete=discord_name_autocompletion
            ),
            char_name: discord.Option(
                str,
                description='EverQuest character name',
            ),
            char_race: discord.Option(
                str,
                description='EverQuest character race',
                autocomplete=races_autocompletion,
                required=False
            ),
            char_class: discord.Option(
                str,
                description='EverQuest character class',
                autocomplete=classes_autocompletion,
                required=False
            ),
            char_type: discord.Option(
                str,
                description='EverQuest character type',
                autocomplete=types_autocompletion,
                required=False
            )
    ):
        """
        Add a new character to bot database
        :param ctx: the application context of the bot
        :param discord_name: string selected from dropdown (required)
        :param char_name: string entered by user (required)
        :param char_race: string (all eq races) selected from dropdown (optional)
        :param char_class: string (all eq classes) selected from dropdown (optional)
        :param char_type: string (main/alt/mule) selected from dropdown (optional)
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

        # this is checking the characters database to see if
        # the discord id for the provided discord name exists
        # i.e., have any characters ever been entered for this
        # discord user
        print(f"discord name entered: {discord_name}")
        discord_id = self._helper.get_discord_id(discord_name, 'display')
        print(f"discord_id returned: {discord_id}")
        # if no discord id in database, notify user and exit
        if discord_id == "":
            await ctx.respond(
                f"```Discord ID not found for {discord_name}.\n"
                "Characters must have a valid Discord ID.```",
                ephemeral=True
            )
            return

        if self.add_member(discord_id) is False:
            await ctx.respond(
                f"```Problem inserting discord id into database.```",
                ephemeral=True
            )
            return

        # assign char_priority int based on char_type string
        # note: this is a hidden field in the database
        # it is purely for sorting purposes
        if char_type == "Main":
            char_priority = 0
        elif char_type == "Alt":
            char_priority = 1
        else:
            char_priority = 2

        try:
            results = self._database.insert_character(discord_id, char_name, char_race,
                                          char_class, char_type, char_priority)
            row = self._helper.get_row(results)

            # customize response message to user based on how
            # many character options were input
            message = f"({char_name} | "

            if char_race is not None:
                message = message + f"{char_race} | "

            if char_class is not None:
                message = message + f"{char_class} | "

            if char_type is not None:
                message = message + f"{char_type} | "

            # trim trailing pipe symbol and whitespace
            message = message[0:len(message) - 3]

            await ctx.respond(
                f"```{message}) entered."
                f"\n{results} {row} added to database.```",
                ephemeral=True
            )
        except Exception as err:
            if "Duplicate entry" in str(err):
                await ctx.respond(
                    f"{char_name} already exists in the database.",
                    ephemeral=True
                )
            else:
                self._helper.log_activity(ctx.author, ctx.command, str(err))
                await ctx.respond(
                    f"```An error has occurred: {err}.```",
                    ephemeral=True
                )

    @discord.slash_command(name="edit_character", description="Edit an existing character")
    async def edit_character(
            self,
            ctx: discord.ApplicationContext,
            char_name: discord.Option(
                str,
                description='Original name',
                autocomplete=char_name_autocompletion
            ),
            new_name: discord.Option(
                str,
                description='New name',
                required=False
            ),
            char_race: discord.Option(
                str,
                description='New race',
                autocomplete=races_autocompletion,
                required=False
            ),
            char_class: discord.Option(
                str,
                description='New class',
                autocomplete=classes_autocompletion,
                required=False
            ),
            char_type: discord.Option(
                str,
                description='New type',
                autocomplete=types_autocompletion,
                required=False
            )
    ):
        """
        Edit an existing character in the database
        :param ctx: the application context of the bot
        :param char_name: string entered by user (required)
        :param new_name: string entered by user if name needs changed (optional)
        :param char_race: string (all eq races) selected from dropdown (optional)
        :param char_class: string (all eq classes) selected from dropdown (optional)
        :param char_type: string (main/alt/mule) selected from dropdown (optional)
        :return: none
        """
        # this slash command only available to officers
        target_role = discord.utils.get(ctx.guild.roles, name="Officer")

        # if validate_role returns false, user is not authorized,
        # so exit function
        if not self._helper.validate_role(ctx.author.roles, target_role):
            await self.not_authorized(ctx)
            return

        # if ctx.selection_option is only 1, then user either
        # entered nothing after character name, or they did
        # not select from the slash command options
        # so exit function
        if len(ctx.selected_options) < 2:
            await ctx.respond(
                f"```No options selected.\n"
                f"Please try again.```",
                ephemeral=True
            )
            return

        self._helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        results = self._database.update_character(
            char_name, new_name, char_race, char_class, char_type
        )
        row = self._helper.get_row(results)

        # customize response message to user based on how
        # many edit options were input
        if results > 0:
            message = f"{char_name} updated to: "

            if new_name is not None:
                message = message + f"{new_name} | "

            if char_race is not None:
                message = message + f"{char_race} | "

            if char_class is not None:
                message = message + f"{char_class} | "

            if char_type is not None:
                message = message + f"{char_type} | "

            # trim trailing pipe symbol and whitespace
            message = message[0:len(message) - 3]
        else:
            message = f"{char_name} not found"

        await ctx.respond(
            f"```{message}."
            f"\n{results} {row} updated in database.```",
            ephemeral=True
        )

    def delete_member(self, discord_id):
        """
        Delete a member from the database
        :param discord_id: the discord_id to check
        :return: boolean
        """
        # count the number of discord_ids left in characters table
        num_ids = len(self._database.count_ids(discord_id))

        # if at least one character left, return True
        if num_ids > 0:
            return True

        # if no more characters left for discord_id, we need
        # to delete discord_id from members table, return True
        # if delete successful, otherwise return False
        if self._database.delete_member(discord_id) > 0:
            return True
        else:
            return False

    @discord.slash_command(name="delete_character", description="Delete a character")
    async def delete_character(
            self,
            ctx: discord.ApplicationContext,
            char_name: discord.Option(
                str,
                description='EverQuest character name',
                autocomplete=char_name_autocompletion
            )
    ):
        """
        Delete a character from the database
        :param ctx: the application context of the bot
        :param char_name: string entered by user (required)
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

        # get discord_id before character is deleted
        discord_id = self._database.lookup_discord_id(char_name)[0]['discord_id']

        # delete character from database
        char_results = self._database.delete_character(char_name)
        row = self._helper.get_row(char_results)

        # get results of delete_member function
        member_results = self.delete_member(discord_id)

        # if char_results > 0 then query was successful
        # i.e., character was deleted
        # if member_results is True then either more than
        # one character for given discord_id left in
        # characters table, or this was last character
        # and discord_id was deleted from members table
        if char_results > 0 and member_results is True:
            message = f"You deleted: {char_name}."
        else:
            message = f"There was a problem deleting {char_name}."

        await ctx.respond(
            f"```{message}."
            f"\n{char_results} {row} deleted from database.```",
            ephemeral=True
        )

    @discord.slash_command(
        name="update_respawns",
        description="Syncs bot database respawn times with Quarm database"
    )
    async def update_respawns(
            self,
            ctx: discord.ApplicationContext,
    ):
        """
        Sync the respawn times in the database with the Quarm database
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

        # this is a moderately long process, so inform user
        await ctx.respond(
            "```Updating all mob respawn times. This will take a while.\n"
            "Please be patient...```",
            ephemeral=True
        )

        # obtain databse mob list
        mob_list = self._database.get_all_mob_names()

        # run tracker update method; does not return anything
        self._tracker.update_respawn_times(mob_list)

        # notify user process is complete
        await ctx.respond(
            "```Database mob respawn time update is complete.```",
            ephemeral=True
        )

    async def not_authorized(
            self,
            ctx: discord.ApplicationContext
    ):
        # Display unauthorized message to user in Discord
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
    tracker = Tracker()

    bot.add_cog(Updates(bot, database, helper, tracker))
