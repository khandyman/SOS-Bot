# import os
# import discord
# from discord.ext import commands
# from database import Database
# from helpers import Helpers
# from dotenv import load_dotenv
#
#
# # load_dotenv()
#
#
# class Lookups(commands.Cog):
#     def __init__(self, bot, db, helper):
#         self._bot = bot
#         self._db = db
#         self._helper = helper
#
#     @discord.slash_command(name="lookup_characters_eq",
#                            description="Find a user's characters by their EQ name")
#     async def lookup_characters_eq(self, ctx: discord.ApplicationContext, char_name: str):
#         results = self._db.lookup_eq(char_name)
#         discord_name = self._helper.get_discord_name(char_name)
#
#         if len(results) > 0:
#             await ctx.respond(
#                 f"```List of characters for: {discord_name}"
#                 f"\n{self._helper.format_message(results)}```",
#                 ephemeral=True)
#         else:
#             await ctx.respond(f"```No records found for {char_name}.\nPlease try again.```", ephemeral=True)
#
#
# def setup(bot):
#     guild = os.getenv('DISCORD_GUILD')
#     db = Database()
#     helper = Helpers(bot, guild, db)
#     bot.add_cog(Lookups(bot, db, helper))
