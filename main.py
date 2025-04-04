# bot.py
import os

import discord  # actually using py-cord instead of discord.py
from database import Database
from dotenv import load_dotenv
from prettytable import PrettyTable
import pymysql

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
names = []
nicks = []

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)
db = Database()


def get_races():
    races = discord.Option(
        str,
        required=False,
        choices=[
            'Barbarian',
            'Dark Elf',
            'Dwarf',
            'Erudite',
            'Gnome',
            'Half Elf',
            'Halfling',
            'High Elf',
            'Human',
            'Iksar',
            'Ogre',
            'Troll',
            'Wood Elf'
        ]
    )

    return races


def get_classes():
    classes = discord.Option(
        str,
        required=False,
        choices=[
            'Bard',
            'Beastlord',
            'Cleric',
            'Druid',
            'Enchanter',
            'Magician',
            'Monk',
            'Necromancer',
            'Paladin',
            'Ranger',
            'Rogue',
            'Shadow Knight',
            'Shaman',
            'Warrior',
            'Wizard'
        ]
    )

    return classes


def get_types():
    types = discord.Option(
        str,
        required=False,
        choices=[
            'Main',
            'Alt',
            'Mule'
        ]
    )

    return types


@bot.event
async def on_ready():
    global names, nicks
    guild = get_guild()

    for member in guild.members:
        names.append(member.name)

        if member.nick is None:
            nicks.append(member.name)
        else:
            nicks.append(member.nick)

    names.sort(key=lambda s: s.lower())
    nicks.sort(key=lambda s: s.lower())

    print(
        f'{bot.user} has connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})'
    )


@bot.slash_command(name="sync", description="Sync all bot commands with server.")
async def sync(ctx: discord.ApplicationContext):
    try:
        synced_commands = await bot.sync_commands()
        print(f'Synced {synced_commands} commands.')
        await ctx.respond(f'Synced {synced_commands} commands.', ephemeral=True)
    except Exception as e:
        print(f"Syncing error: {e}")


@bot.slash_command(name="lookup_characters_eq",
                   description="Find a user's characters by their EQ name")
async def lookup_characters_eq(ctx: discord.ApplicationContext, char_name: str):
    results = db.lookup_eq(char_name)
    discord_name = get_discord_name(char_name)

    if len(results) > 0:
        await ctx.respond(
            f"```List of characters for: {discord_name}"
            f"\n{format_message(results)}```",
            ephemeral=True)
    else:
        await ctx.respond(f"```No records found for {char_name}.\nPlease try again.```", ephemeral=True)


@bot.slash_command(name="lookup_characters_discord",
                   description="Find a user's characters by their Discord id")
async def lookup_characters_discord(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(names))
):
    discord_id = get_discord_id(discord_name)

    if discord_id != "":
        results = db.lookup_discord(discord_id)

        await ctx.respond(f"```{format_message(results)}```", ephemeral=True)
    else:
        await ctx.respond(f"```Discord ID not found for {discord_name}.\nUnable to query database.```", ephemeral=True)


@bot.slash_command(name="get_all_mains", description="Get a list of all mains")
async def get_all_mains(ctx: discord.ApplicationContext):
    results = db.get_all_mains()
    main_list = "Main characters in Seekers Of Souls:\n"

    for result in results:
        main_list = main_list + f"{result}\n"

    await ctx.respond(f"```{main_list}```", ephemeral=True)


@bot.slash_command(name="find_main_from_discord", description="Find a user's main character")
async def find_main_from_discord(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(names))
):
    discord_id = get_discord_id(discord_name)

    if discord_id != "":
        results = db.lookup_main(discord_id)

        if len(results) > 0:
            await ctx.respond(f'```{discord_name} = {results[0]['char_name']}```', ephemeral=True)
        else:
            await ctx.respond(f'```No records found for {discord_name}.```', ephemeral=True)
    else:
        await ctx.respond(f'```Discord ID not found for {discord_name}.\nUnable to query database.```', ephemeral=True)


@bot.slash_command()
async def add_character(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(names)),
        char_name: str,
        char_race: get_races(),
        char_class: get_classes(),
        char_type: get_types()
):
    discord_id = get_discord_id(discord_name)

    if discord_id == "":
        await ctx.respond(f"```Discord ID not found for {discord_name}.\n"
                          "Characters must have a valid Discord ID.```")
    else:
        if char_type == "Main":
            char_priority = 0
        elif char_type == "Alt":
            char_priority = 1
        else:
            char_priority = 2

        try:
            results = db.insert_character(discord_id, char_name, char_race,
                                          char_class, char_type, char_priority)
            row = get_row(results)

            await ctx.respond(
                f"```You entered: {discord_name} | {char_name} | {char_race} | {char_class} | {char_type}"
                f"\n{results} {row} added to database.```",
                ephemeral=True
            )
        except Exception as err:
            if "Duplicate entry" in str(err):
                await ctx.respond(
                    f"{char_name} already exists in the database.", ephemeral=True
                )
            else:
                await ctx.respond(
                    f"```An error has occurred: {err}.```", ephemeral=True
                )


@bot.slash_command(name="edit_character", description="Edit an existing character")
async def edit_character(
        ctx: discord.ApplicationContext,
        char_name: str,
        new_name: discord.Option(str, required=False),
        char_race: get_races(),
        char_class: get_classes(),
        char_type: get_types()
):
    results = db.update_character(char_name, new_name, char_race, char_class, char_type)
    row = get_row(results)

    await ctx.respond(
        f"```You entered: {char_name} | {new_name} | {char_race} | {char_class} | {char_type}."
        f"\n{results} {row} updated in database.```",
        ephemeral=True
    )


@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, char_name: str):
    results = db.delete_character(char_name)
    row = get_row(results)

    await ctx.respond(
        f"```You deleted: {char_name}."
        f"\n{results} {row} deleted from database.```",
        ephemeral=True
    )


def format_message(results):
    message = PrettyTable()
    message.field_names = ["Name", "Race", "Class", "Type"]
    message.align = 'l'

    for result in results:
        message.add_row([result['char_name'], result['char_race'], result['char_class'], result['char_type']])

    return message


def get_guild():
    return discord.utils.get(bot.guilds, name=GUILD)


def get_discord_id(discord_name):
    discord_id = ""

    for member in get_guild().members:
        if discord_name == member.nick or discord_name == member.name:
            discord_id = member.id

    return discord_id


def get_discord_name(char_name):
    discord_name = ""

    discord_id = db.lookup_discord_id(char_name)

    if len(discord_id) > 0:
        discord_id = discord_id[0]['discord_id']

    for member in get_guild().members:
        if discord_id == str(member.id):
            discord_name = member.name

    return discord_name


def get_row(results):
    if results == 1:
        row = "row"
    else:
        row = "rows"

    return row


bot.run(TOKEN)
