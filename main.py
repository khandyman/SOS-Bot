# bot.py
import os

import discord  # actually using py-cord instead of discord.py
from database import Database
from helpers import Helpers
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
names = []
nicks = []

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)
# bot.load_extension('cogs.lookups')
db = Database()
helper = Helpers(bot, GUILD, db)


@bot.event
async def on_ready():
    global names, nicks
    guild = helper.get_guild()

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


# @bot.slash_command(name="sync", description="Sync all bot commands with server.")
# async def sync(ctx: discord.ApplicationContext):
#     try:
#         synced_commands = await bot.sync_commands()
#         print(f'Synced {synced_commands} commands.')
#         await ctx.respond(f'Synced {synced_commands} commands.', ephemeral=True)
#     except Exception as e:
#         print(f"Syncing error: {e}")


@bot.slash_command(name="lookup_characters_everquest",
                   description="Find a user's characters by their EQ name")
async def lookup_characters_everquest(ctx: discord.ApplicationContext, char_name: str):
    target_role = discord.utils.get(ctx.guild.roles, name="Seeker")

    if helper.validate_role(ctx.author.roles, target_role):
        helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        results = db.lookup_eq(char_name)
        discord_name = helper.get_discord_name(char_name)

        if len(results) > 0:
            await ctx.respond(
                f"```List of characters for: {discord_name}\n"
                f"\n{helper.format_message(results)}```",
                ephemeral=True
            )
        else:
            await ctx.respond(f"```No records found for {char_name}.\nPlease try again.```", ephemeral=True)
    else:
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
            ephemeral=True
        )


@bot.slash_command(name="lookup_characters_discord",
                   description="Find a user's characters by their Discord id")
async def lookup_characters_discord(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(names))
):
    target_role = discord.utils.get(ctx.guild.roles, name="Seeker")

    if helper.validate_role(ctx.author.roles, target_role):
        helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        discord_id = helper.get_discord_id(discord_name)

        if discord_id != "":
            results = db.lookup_discord(discord_id)

            await ctx.respond(f"```{helper.format_message(results)}```", ephemeral=True)
        else:
            await ctx.respond(
                f"```Discord ID not found for {discord_name}.\n"
                f"Unable to query database.```",
                ephemeral=True
            )
    else:
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
            ephemeral=True
        )


@bot.slash_command(name="find_main_from_discord", description="Find a user's main character")
async def find_main_from_discord(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(names))
):
    target_role = discord.utils.get(ctx.guild.roles, name="Seeker")

    if helper.validate_role(ctx.author.roles, target_role):
        helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        discord_id = helper.get_discord_id(discord_name)

        if discord_id != "":
            results = db.lookup_main(discord_id)

            if len(results) > 0:
                await ctx.respond(f'```{discord_name} = {results[0]['char_name']}```', ephemeral=True)
            else:
                await ctx.respond(f'```No records found for {discord_name}.```', ephemeral=True)
        else:
            await ctx.respond(
                f'```Discord ID not found for {discord_name}.\n'
                f'Unable to query database.```',
                ephemeral=True
            )
    else:
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
            ephemeral=True
        )


@bot.slash_command(name="get_all_mains", description="Get a list of all mains")
async def get_all_mains(ctx: discord.ApplicationContext):
    target_role = discord.utils.get(ctx.guild.roles, name="Officer")

    if helper.validate_role(ctx.author.roles, target_role):
        helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        results = db.get_all_mains()
        main_list = "Main characters in Seekers Of Souls:\n"

        for result in results:
            main_list = main_list + f"{result}\n"

        await ctx.respond(f"```{main_list}```", ephemeral=True)
    else:
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
            ephemeral=True
        )


@bot.slash_command(name="add_character", description="Add a character to the database")
async def add_character(
        ctx: discord.ApplicationContext,
        discord_name: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(names)),
        char_name: str,
        char_race: helper.get_races(),
        char_class: helper.get_classes(),
        char_type: helper.get_types()
):
    target_role = discord.utils.get(ctx.guild.roles, name="Officer")

    if helper.validate_role(ctx.author.roles, target_role):
        helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        discord_id = helper.get_discord_id(discord_name)

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
                row = helper.get_row(results)

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
                    helper.log_activity(ctx.author, ctx.command, str(err))
                    await ctx.respond(
                        f"```An error has occurred: {err}.```", ephemeral=True
                    )
    else:
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
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
    target_role = discord.utils.get(ctx.guild.roles, name="Officer")

    if helper.validate_role(ctx.author.roles, target_role):
        helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        results = db.update_character(char_name, new_name, char_race, char_class, char_type)
        row = helper.get_row(results)

        await ctx.respond(
            f"```You entered: {char_name} | {new_name} | {char_race} | {char_class} | {char_type}."
            f"\n{results} {row} updated in database.```",
            ephemeral=True
        )
    else:
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
            ephemeral=True
        )


@bot.slash_command(name="delete_character", description="Delete a character")
async def delete_character(ctx: discord.ApplicationContext, char_name: str):
    target_role = discord.utils.get(ctx.guild.roles, name="Officer")

    if helper.validate_role(ctx.author.roles, target_role):
        helper.log_activity(ctx.author, ctx.command, ctx.selected_options)

        results = db.delete_character(char_name)
        row = helper.get_row(results)

        await ctx.respond(
            f"```You deleted: {char_name}."
            f"\n{results} {row} deleted from database.```",
            ephemeral=True
        )
    else:
        await ctx.respond(
            f"```You do not have permission to use this command.\n"
            f"Please try another command.```",
            ephemeral=True
        )


bot.run(TOKEN)
