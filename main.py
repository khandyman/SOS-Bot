# bot.py
import os

import discord  # actually using py-cord instead of discord.py
from database import Database
from dotenv import load_dotenv
from prettytable import PrettyTable

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
    query = (
        "SELECT b.char_name, b.char_race, b.char_class, b.char_type, b.char_priority FROM sos_bot.characters a"
        f" JOIN sos_bot.characters b ON a.discord_id = b.discord_id WHERE a.char_name = '{char_name}'"
        "ORDER BY b.char_priority ASC"
    )
    results = db.retrieve_records(query)

    if len(results) > 0:
        await ctx.respond(f"```{format_message(results)}```", ephemeral=True)
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
        query = (
            "SELECT char_name, char_race, char_class, char_type, char_priority FROM sos_bot.characters"
            f" WHERE discord_id = '{discord_id}' ORDER BY char_priority ASC"
        )
        results = db.retrieve_records(query)

        await ctx.respond(f"```{format_message(results)}```", ephemeral=True)
    else:
        await ctx.respond(f"```Discord ID not found for {discord_name}.\nUnable to query database.```", ephemeral=True)


# @bot.slash_command(name="get_all_mains", description="Get a list of all mains")
# async def get_all_mains(ctx: discord.ApplicationContext):
#     query = (
#         "SELECT char_name FROM sos_bot.characters WHERE char_type = 'Main' ORDER BY char_name"
#     )
#     results = db.retrieve_records(query)
#
#     await ctx.respond(f"```{results}```", ephemeral=True)


@bot.slash_command(name="find_discord_users_main", description="Find a user's main character")
async def find_discord_users_main(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(names))
):
    discord_id = get_discord_id(discord_name)

    if discord_id != "":
        query = (
            "SELECT char_name from sos_bot.characters WHERE "
            f" discord_id = {discord_id} AND char_type = 'Main'"
        )
        results = db.retrieve_records(query)

        if len(results) > 0:
            await ctx.respond(f'```{results[0]['char_name']}```', ephemeral=True)
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

        query = (
            "INSERT INTO sos_bot.characters" 
            "(discord_id, char_name, char_race, char_class, char_type, is_officer, char_priority)"
            f" VALUES ('{discord_id}', '{char_name}', '{char_race}', '{char_class}', '{char_type}', 0, {char_priority})"
        )
        results = db.insert_character(query)

        await ctx.respond(
            f'```You entered: {discord_id} | {char_name} | {char_race} | {char_class} | {char_type}```',
            ephemeral=True
        )


@bot.slash_command(name="edit_character", description="Edit an existing character")
async def edit_character(
        ctx: discord.ApplicationContext,
        char_name: str,
        char_race: get_races(),
        char_class: get_classes(),
        char_type: get_types()
):
    query = f"UPDATE sos_bot.characters SET char_name = '{char_name}'"

    if char_race is not None:
        query = query + f", char_race = '{char_race}'"

    if char_class is not None:
        query = query + f", char_class = '{char_class}'"

    if char_type is not None:
        query = query + f", char_type = '{char_type}'"

    query = query + f" WHERE char_name = '{char_name}'"
    print(query)

    await ctx.respond(f"```You are updating: {char_name} | {char_race} | {char_class} | {char_type}```", ephemeral=True)


@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, char_name: str):
    query = f"DELETE FROM sos_bot.characters WHERE char_name = '{char_name}'"
    results = db.insert_character(query)

    await ctx.respond(f"```Successfully deleted: {char_name}```", ephemeral=True)


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


bot.run(TOKEN)
