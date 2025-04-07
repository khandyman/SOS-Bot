# bot.py
import os
import typing

import discord  # actually using py-cord instead of discord.py
from discord.ext.tasks import loop
from discord.ext import commands
from discord import application_command
from database import Database
from helpers import Helpers
from dotenv import load_dotenv
import asyncio

load_dotenv()  # sets up environment variables, stored locally in .env

TOKEN = os.getenv('DISCORD_TOKEN')  # bot token
GUILD = os.getenv('DISCORD_GUILD')  # target guild
names = []  # list of Discord names
nicks = []  # list of Discord nicknames

# give bot access to all Discord intents and
# instantiate database and helper classes
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)
db = Database()
helper = Helpers(bot, GUILD, db)


@bot.event
async def on_ready():
    """
    start up function: gets guild instance,
    builds names and nicks lists from guild,
    and starts keep alive routine
    :return: none
    """
    global names, nicks
    guild = helper.get_guild()

    for member in guild.members:
        names.append(member.name)

        if member.nick is None:
            nicks.append(member.name)
        else:
            nicks.append(member.nick)

    # fancy looking, but just sorts both lists case insensitively
    names.sort(key=lambda s: s.lower())
    nicks.sort(key=lambda s: s.lower())

    # test = db.get_all_characters()
    # for char in test:
    #     print(char)

    print(
        f'{bot.user} has connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})'
    )

    keep_alive.start()
    # find_discrepancies(guild)


@loop(count=None)
async def keep_alive():
    """
    send query to database every 10 minutes
    to keep database from timing out
    :return: none
    """
    await bot.wait_until_ready()
    db.get_all_mains()
    print("Keeping MySQL connection alive.")
    await asyncio.sleep(600)


def find_discrepancies(guild):
    characters = db.get_discord_ids()
    discrepancies = []
    found = False

    for char_dict in characters:
        for member in guild.members:
            if str(char_dict['discord_id']) == str(member.id):
                found = True
                break

        if found is False:
            current_char = {
                "discord_id": char_dict['discord_id'],
                "char_name": char_dict['char_name']
            }
            discrepancies.append(current_char)

        found = False

    for item in discrepancies:
        print(item)


@bot.slash_command(name="lookup_characters_everquest",
                   description="Find a user's characters by their EQ name")
async def lookup_characters_everquest(
        ctx: discord.ApplicationContext,
        char_name: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(db.get_all_characters())
        )
):
    """
    find all characters associated with a
    given eq character name
    :param ctx: the application context of the bot
    :param char_name: string entered by user (required)
    :return: none
    """
    # # this slash command available to all users
    target_role = discord.utils.get(ctx.guild.roles, name="Seeker")

    # if validate_role returns false, user is not authorized,
    # so exit function
    if not helper.validate_role(ctx.author.roles, target_role):
        await not_authorized(ctx)
        return

    helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

    results = db.lookup_eq(char_name)
    discord_name = helper.get_discord_name(char_name)

    # if no matches found, notify user then exit
    if len(results) == 0:
        await ctx.respond(
            f"```No records found for {char_name}.\n"
            f"Please try again.```",
            ephemeral=True
        )
        return

    # if matches found display discord id,
    # then print table of character results
    await ctx.respond(
        f"```List of characters for: {discord_name}\n"
        f"\n{helper.format_message(results)}```",
        ephemeral=True
    )


@bot.slash_command(name="lookup_characters_discord",
                   description="Find a user's characters by their Discord id")
async def lookup_characters_discord(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(nicks)
        )
):
    """
    find all characters associated with a
    given discord name
    :param ctx: the application context of the bot
    :param discord_name: string selected from dropdown (required)
    :return: none
    """
    # this slash command available to all users
    target_role = discord.utils.get(ctx.guild.roles, name="Seeker")

    # if validate_role returns false, user is not authorized,
    # so exit function
    if not helper.validate_role(ctx.author.roles, target_role):
        await not_authorized(ctx)
        return

    helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

    discord_id = helper.get_discord_id(discord_name)

    # if no discord id found, notify user and exit function
    if discord_id == "":
        await ctx.respond(
            f'```Discord ID not found for {discord_name}.\n'
            f'Unable to query database.```',
            ephemeral=True
        )
        return

    results = db.lookup_discord(discord_id)

    # print table of character results, no need to
    # print discord name this time because it was
    # provided by user
    await ctx.respond(
        f"```{helper.format_message(results)}```",
        ephemeral=True
    )


@bot.slash_command(name="find_main_from_discord", description="Find a user's main character")
async def find_main_from_discord(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(nicks)
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
    if not helper.validate_role(ctx.author.roles, target_role):
        await not_authorized(ctx)
        return

    helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

    discord_id = helper.get_discord_id(discord_name)

    # if no discord id found, notify user and exit function
    if discord_id == "":
        await ctx.respond(
            f'```Discord ID not found for {discord_name}.\n'
            f'Unable to query database.```',
            ephemeral=True
        )
        return

    results = db.lookup_main(discord_id)

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


@bot.slash_command(name="get_all_mains", description="Get a list of all mains")
async def get_all_mains(ctx: discord.ApplicationContext):
    """
    get list of all characters in database with char_type of 'Main'
    :param ctx: the application context of the bot
    :return: none
    """
    # this slash command only available to officers
    target_role = discord.utils.get(ctx.guild.roles, name="Officer")

    # if validate_role returns false, user is not authorized,
    # so exit function
    if not helper.validate_role(ctx.author.roles, target_role):
        await not_authorized(ctx)
        return

    helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

    results = db.get_all_mains()
    main_list = "Main characters in Seekers Of Souls:\n"

    # print one character per line
    for result in results:
        main_list = main_list + f"{result}\n"

    await ctx.respond(
        f"```{main_list}```",
        ephemeral=True
    )


@bot.slash_command(name="add_character", description="Add a character to the database")
async def add_character(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(
            str,
            autocomplete=discord.utils.basic_autocomplete(names)
        ),
        char_name: str,
        char_race: helper.get_races(),
        char_class: helper.get_classes(),
        char_type: helper.get_types()
):
    """

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
    if not helper.validate_role(ctx.author.roles, target_role):
        await not_authorized(ctx)
        return

    helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

    # this is checking the characters database to see if
    # the discord id for the provided discord name exists
    # i.e., have any characters ever been entered for this
    # discord user
    discord_id = helper.get_discord_id(discord_name)

    # if no discord id in database, notify user and exit
    if discord_id == "":
        await ctx.respond(
            f"```Discord ID not found for {discord_name}.\n"
            "Characters must have a valid Discord ID.```",
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
        results = db.insert_character(discord_id, char_name, char_race,
                                      char_class, char_type, char_priority)
        row = helper.get_row(results)

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
            helper.log_activity(ctx.author, ctx.command, str(err))
            await ctx.respond(
                f"```An error has occurred: {err}.```",
                ephemeral=True
            )


@bot.slash_command(name="edit_character", description="Edit an existing character")
async def edit_character(
        ctx: discord.ApplicationContext,
        char_name: str,
        new_name: discord.Option(str, required=False),
        char_race: helper.get_races(),
        char_class: helper.get_classes(),
        char_type: helper.get_types()
):
    """

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
    if not helper.validate_role(ctx.author.roles, target_role):
        await not_authorized(ctx)
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

    helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

    results = db.update_character(char_name, new_name, char_race, char_class, char_type)
    row = helper.get_row(results)

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


@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, char_name: str):
    """
    delete a character from the database
    :param ctx: the application context of the bot
    :param char_name: string entered by user (required)
    :return: none
    """
    # this slash command only available to officers
    target_role = discord.utils.get(ctx.guild.roles, name="Officer")

    # if validate_role returns false, user is not authorized,
    # so exit function
    if not helper.validate_role(ctx.author.roles, target_role):
        await not_authorized(ctx)
        return

    helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

    results = db.delete_character(char_name)
    row = helper.get_row(results)

    # if results > 0 then query was successful
    # i.e., character was deleted
    if results > 0:
        message = f"You deleted: {char_name}"
    else:
        message = f"{char_name} not found"

    await ctx.respond(
        f"```{message}."
        f"\n{results} {row} deleted from database.```",
        ephemeral=True
    )


async def not_authorized(ctx: discord.ApplicationContext):
    await ctx.respond(
        f"```You do not have permission to use this command.\n"
        f"Please try another command.```",
        ephemeral=True
    )


bot.run(TOKEN)
