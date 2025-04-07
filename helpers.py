import discord
import datetime
from prettytable import PrettyTable


class Helpers:
    def __init__(self, bot, guild, db):
        self._bot = bot
        self._guild = guild
        self._db = db

    def validate_role(self, user_roles, target_role):
        if target_role in user_roles:
            return True
        else:
            return False

    # def format_message(self, results):
    #     message = PrettyTable()
    #     message.field_names = ["Name", "Race", "Class", "Type"]
    #     message.align = 'l'
    #
    #     for result in results:
    #         message.add_row([result['char_name'], result['char_race'], result['char_class'], result['char_type']])
    #
    #     return message

    def format_message(self, results):
        headers = "Name Race Class Type".split()
        row = "{:<15} {:<10} {:<15} {:<5} \n"

        message = row.format(*headers)
        message = message + "-" * 52 + "\n"

        for result in results:
            message = message + row.format(
                str(result['char_name']),
                str(result['char_race']),
                str(result['char_class']),
                str(result['char_type'])
            )

        return message

    @staticmethod
    def log_activity(user, command, entries):
        log_string = f"{datetime.datetime.now()} - {user} - {command}"

        if entries is not None:
            log_string = log_string + " - ["
            for entry in entries:
                entry_value = f"{entry['name']}: {entry['value']} | "
                log_string = log_string + entry_value

            log_string = log_string[0:len(log_string) - 3]
            log_string = log_string + "]\n"

        file_path = "logs//bot-log.txt"

        print(log_string)
        file = open(file_path, 'a')
        file.write(log_string)
        file.close()

    def get_guild(self):
        return discord.utils.get(self._bot.guilds, name=self._guild)

    def get_discord_id(self, discord_name):
        discord_id = ""

        for member in self.get_guild().members:
            if discord_name == member.display_name:
                discord_id = member.id

        return discord_id

    def get_discord_name(self, char_name):
        discord_name = ""

        discord_id = self._db.lookup_discord_id(char_name)

        if len(discord_id) > 0:
            discord_id = discord_id[0]['discord_id']

        for member in self.get_guild().members:
            if discord_id == str(member.id):
                discord_name = member.display_name

        return discord_name

    def get_row(self, results):
        if results == 1:
            row = "row"
        else:
            row = "rows"

        return row

    def get_races(self):
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

    def get_classes(self):
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

    def get_types(self):
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
