# bot.py
import os

import discord  # actually using py-cord instead of discord.py
# from discord.ext import commands
from discord.ui import Select, View
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
members = []

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    global members
    guild = discord.utils.get(bot.guilds, name=GUILD)

    for member in guild.members:
        if member.nick is None:
            members.append(member.name)
        else:
            members.append(member.nick)

    members.sort(key=lambda s: s.lower())

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
async def lookup_characters_discord(ctx: discord.ApplicationContext, discord_id: str):
    discord_ids = Select(placeholder="Select a Discord id")

    class MyView(View):
        def __init__(self, options1, options2):
            super().__init__()

            self.select1 = Select(options=options1)
            self.select2 = Select(options=options2)
            self.add_item(self.select1)
            self.add_item(self.select2)

    options1 = [discord.SelectOption(label=f"Option {i}") for i in range(1, 26)]
    options2 = [discord.SelectOption(label=f"Option {i}") for i in range(26, 51)]

    view = MyView(options1, options2)

    await ctx.send("Select an option:", view=view)

    # for member in members:
    #     print(member)
    #     discord_ids.add_option(label=member)

    # await ctx.respond(f"You entered: {discord_id}", ephemeral=True)


@bot.slash_command(name="get_all_mains", description="Get a list of all mains")
async def get_all_mains(ctx: discord.ApplicationContext):
    await ctx.respond("This is a big list!", ephemeral=True)


@bot.slash_command(name="find_discord_users_main", description="Find a user's main character")
async def find_discord_users_main(ctx: discord.ApplicationContext, discord_id: str):
    await ctx.respond(f"{discord_id}'s main character is: ", ephemeral=True)


# @bot.slash_command(name="add_character", description="Add a new character")
# async def add_character(ctx: discord.ApplicationContext, discord_id: str, char_name: str, eq_race: str,
#                         eq_class: str, char_type: str):
#     await ctx.respond(f"You are entering: "
#                       f"{discord_id} | {char_name} | {eq_race} | {eq_class} | {char_type}",
#                       ephemeral=True)

@bot.command()
async def add_character(ctx):
    # char_race = Select(placeholder="Choose a race")

    # for member in members:
        # char_race.add_option(label=member)
        # print(member)

    char_class = Select(
        placeholder="Choose a class",
        options=[
            discord.SelectOption(label="Bard"),
            discord.SelectOption(label="Cleric")
        ]
    )

    view = View()
    # view.add_item(char_race)
    view.add_item(char_class)

    await ctx.respond(view=view, ephemeral=True)


@bot.slash_command(name="edit_character", description="Edit an existing character")
async def edit_character(ctx: discord.ApplicationContext, char_name: str, eq_race: str, eq_class: str, char_type: str):
    await ctx.respond(f"You are updating: {char_name} | {eq_race} | {eq_class} | {char_type}", ephemeral=True)


@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, char_name: str):
    await ctx.respond(f"You are deleting: {char_name}", ephemeral=True)


bot.run(TOKEN)

