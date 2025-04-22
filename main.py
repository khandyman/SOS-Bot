# bot.py
import os
import threading
import discord  # actually using py-cord instead of discord.py
from discord.ext.tasks import loop
from classes.database import Database
from classes.helpers import Helpers
from classes.tracker import Tracker
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
# helper = Helpers(bot, GUILD)
tracker = Tracker()


@bot.event
async def on_connect():
    # load slash command classes
    bot.load_extension("cogs.lookups")
    bot.load_extension("cogs.updates")

    await bot.sync_commands()


@bot.event
async def on_ready():
    """
    start up function: gets guild instance
    and starts keep alive routine
    :return: none
    """
    guild = discord.utils.get(bot.guilds, name=GUILD)

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


def start_bot():
    bot.run(TOKEN)


def start_tracker():
    log_lines = tracker.follow()

    for line in log_lines:
        if 'Druzzil Ro tells the guild' in line:
            kill_time = tracker.parse_time(line)
            mob_name = tracker.parse_mob(line)

            tracker.update_kill_time(mob_name, kill_time)


async def send_message(mob_name, kill_time):
    general = bot.get_channel(1155966760919511172)
    await general.send(tracker.update_kill_time(mob_name, kill_time))


if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot)
    tracker_thread = threading.Thread(target=start_tracker)

    bot_thread.start()
    tracker_thread.start()

    bot_thread.join()
    tracker_thread.join()


# test_kill = f"[Fri Apr 18 00:45:28 2025] Druzzil Ro tells the guild, 'Cauthorn of <Seekers of Souls> has killed Essedera in Temple of Veeshan!'"
