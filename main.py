# bot.py
import os

import discord  # actually using py-cord instead of discord.py
from discord.ext.tasks import loop
from classes.database import Database
from classes.helpers import Helpers
from dotenv import load_dotenv
import asyncio

load_dotenv()  # sets up environment variables, stored locally in .env

TOKEN = os.getenv('DISCORD_TOKEN')  # bot token
GUILD = os.getenv('DISCORD_GUILD')  # target guild
discord_names = []  # list of Discord names

# give bot access to all Discord intents and
# instantiate database and helper classes
intents = discord.Intents.all()
bot = discord.Bot(intents=intents)
db = Database()
helper = Helpers(bot, GUILD)


@bot.event
async def on_connect():
    # load slash command classes
    bot.load_extension("cogs.lookups")
    bot.load_extension("cogs.updates")

    await bot.sync_commands()


@bot.event
async def on_ready():
    """
    start up function: gets guild instance,
    builds names and nicks lists from guild,
    and starts keep alive routine
    :return: none
    """
    guild = helper.get_guild()

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


bot.run(TOKEN)
