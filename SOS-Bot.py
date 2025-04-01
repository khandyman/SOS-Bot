# bot.py
import os

import discord
import random
from dotenv import load_dotenv
from redbot.core import commands, app_commands

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)

    # for guild in client.guilds:
    #     if guild.name == GUILD:
    #         break

    print(
        f'{client.user} has connected to the following guild:\n'
        f'{guild.name} (id: {guild.id})'
    )

    # members = '\n - '.join([member.name for member in guild.members])
    # print(f'Guild Members:\n - {members}')


@app_commands.command()
async def on_message(message):
    if message.author == client.user:
        return

    random_officers = ['Twin', 'Luna', 'Toryn', 'Kleo', 'Punk', 'Dark', 'Raf', 'Steel', 'Math']

    if message.content == 'coolest!':
        response = random.choice(random_officers)
        # await message.channel.send(response)
        await interaction.response.send_message(response, ephemeral=True)

client.run(TOKEN)
