# bot.py
import os

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = discord.Bot()


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)

    print(
        f'{bot.user} has connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})'
    )


@bot.slash_command(name="lookup_characters_eq",
                   description="Find a user's characters by their EQ name")
async def lookup_characters_eq(ctx: discord.ApplicationContext, char_name: str):
    await ctx.respond(f"You entered: {char_name}", ephemeral=True)


@bot.slash_command(name="lookup_characters_discord",
                   description="Find a user's characters by their Discord id")
async def lookup_characters_eq(ctx: discord.ApplicationContext, discord_id: str):
    await ctx.respond(f"You entered: {discord_id}", ephemeral=True)


@bot.slash_command(name="get_all_mains", description="Get a list of all mains")
async def get_all_mains(ctx: discord.ApplicationContext):
    await ctx.respond("This is a big list!", ephemeral=True)


@bot.slash_command(name="find_discord_users_main", description="Find a user's main character")
async def find_discord_users_main(ctx: discord.ApplicationContext, discord_id: str):
    await ctx.respond(f"{discord_id}'s main character is: ", ephemeral=True)


@bot.slash_command(name="add_character", description="Add a new character")
async def add_character(ctx: discord.ApplicationContext,
                        discord_id: str, char_name: str, eq_race: str, eq_class: str, char_type: str):
    await ctx.respond(f"You are entering: "
                      f"{discord_id} | {char_name} | {eq_race} | {eq_class} | {char_type}",
                      ephemeral=True)


@bot.slash_command(name="edit_character", description="Edit an existing character")
async def edit_character(ctx: discord.ApplicationContext,
                         char_name: str, eq_race: str, eq_class: str, char_type: str):
    await ctx.respond(f"You are updating: {char_name} | {eq_race} | {eq_class} | {char_type}", ephemeral=True)


@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, char_name: str):
    await ctx.respond(f"You are deleting: {char_name}", ephemeral=True)


bot.run(TOKEN)
