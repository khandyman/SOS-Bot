# bot.py
import os

import discord  # actually using py-cord instead of discord.py
# from discord.ext import commands
from discord.ui import Select, View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
discord_ids = []
nicknames = []

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    global discord_ids, nicknames
    guild = discord.utils.get(bot.guilds, name=GUILD)

    for member in guild.members:
        discord_ids.append(member.name)

        if member.nick is None:
            nicknames.append(member.name)
        else:
            nicknames.append(member.nick)

    discord_ids.sort(key=lambda s: s.lower())
    nicknames.sort(key=lambda s: s.lower())

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
    await ctx.respond(f"You entered: {char_name}", ephemeral=True)


@bot.slash_command(name="lookup_characters_discord",
                   description="Find a user's characters by their Discord id")
async def lookup_characters_discord(
        ctx: discord.ApplicationContext,
        discord_id: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(discord_ids))
):
    await ctx.respond(f'You selected `{discord_id}`!', ephemeral=True)


@bot.slash_command(name="get_all_mains", description="Get a list of all mains")
async def get_all_mains(ctx: discord.ApplicationContext):
    await ctx.respond("This is a big list!", ephemeral=True)


@bot.slash_command(name="find_discord_users_main", description="Find a user's main character")
async def find_discord_users_main(
        ctx: discord.ApplicationContext,
        discord_id: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(discord_ids))
):
    await ctx.respond(f'You selected `{discord_id}`!', ephemeral=True)


@bot.slash_command()
async def add_character(
        ctx: discord.ApplicationContext,
        discord_id: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(discord_ids)),
        char_name: str,
        char_race: discord.Option(
            str,
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
        ),
        char_class: discord.Option(
            str,
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
        ),
        char_type: discord.Option(
            str,
            choices=[
                'Main',
                'Alt',
                'Mule'
            ]
        )
):

    await ctx.respond(
        f'You entered: {discord_id} | {char_name} | {char_race} | {char_class} | {char_type}',
        ephemeral=True
    )


@bot.slash_command(name="edit_character", description="Edit an existing character")
async def edit_character(ctx: discord.ApplicationContext, char_name: str, eq_race: str, eq_class: str, char_type: str):
    await ctx.respond(f"You are updating: {char_name} | {eq_race} | {eq_class} | {char_type}", ephemeral=True)


@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, char_name: str):
    await ctx.respond(f"You are deleting: {char_name}", ephemeral=True)


bot.run(TOKEN)
