import discord
import datetime


class Helpers:
    """
    This class provides miscellaneous functions,
    primarily to the command cogs
    """
    def __init__(self, bot, guild):
        self._bot = bot
        self._guild = guild

    def validate_role(self, user_roles, target_role):
        """
        Compare target role to list of user's roles;
        return true if found (i.e., user is authorized)
        :param user_roles: list
        :param target_role: string
        :return: boolean
        """
        if target_role in user_roles:
            return True
        else:
            return False

    def format_char_message(self, results):
        """
        Format database results into table format
        :param results: list of dictionary entries;
        each item is a different character
        :return: formatted string
        """
        headers = "Name Race Class Type".split()
        row = "{:<15} {:<10} {:<15} {:<5} \n"       # set column widths

        message = row.format(*headers)
        message = message + "-" * 52 + "\n"         # add a separator

        for result in results:
            # for each character, arrange them in the correct order
            message = message + row.format(
                str(result['char_name']),
                str(result['char_race']),
                str(result['char_class']),
                str(result['char_type'])
            )

        return message

    def format_mob_message(self, results):
        """
        Format database results into table format
        :param results: list of dictionary entries;
        each item is a different character
        :return: formatted string
        """
        headers = "Mob Killed Respawning".split()
        row = "{:<30} {:<20} {:<20} \n"       # set column widths
        time_zone = None

        message = row.format(*headers)
        message = message + "-" * 71 + "\n"         # add a separator

        for result in results:
            # for each mob, arrange them in the correct order
            message = message + row.format(
                str(result['mob_name']),
                str(result['kill_time']),
                str(result['respawn_time'])
            )

            if result['kill_time'] is not None:
                time_zone = result['time_zone']

        message = message + f"\nTime Zone: {time_zone}"

        return message

    @staticmethod
    def log_activity(user, command, entries):
        """
        Write every command entered into bot to log file
        :param user: the Discord user who entered the command
        :param command: the command name
        :param entries: the list of dictionary options user selected
        :return: none
        """
        # begin the log string that will be written to log file
        log_string = f"{datetime.datetime.now()} - {user} - {command}"

        # if command had options to select
        if entries is not None:
            log_string = log_string + " - ["
            # loop through selected options
            for entry in entries:
                # grab the name of the option and what
                # user entered; add it to log string
                entry_value = f"{entry['name']}: {entry['value']} | "
                log_string = log_string + entry_value

            # trim off the trailing pipe and spaces
            log_string = log_string[0:len(log_string) - 3]
            log_string = log_string + "]\n"

        file_path = "logs//bot-log.txt"

        print(log_string)
        file = open(file_path, 'a')
        file.write(log_string)
        file.close()

    def get_guild(self):
        """
        Obtain the target Discord guild
        :return: a Discord guild instance
        """
        return discord.utils.get(self._bot.guilds, name=self._guild)

    def get_discord_id(self, discord_name, name_type):
        """
        Find the discord id of a member
        :param name_type: flag for type of Discord name
        :param discord_name: Discord display_name
        :return: string Discord ID number
        """
        discord_id = ""

        # loop through members of guild, if match
        # is found, grab the ID
        for member in self.get_guild().members:
            if name_type == 'display':
                if discord_name == member.display_name:
                    discord_id = member.id
            elif name_type == 'account':
                if discord_name == member.name:
                    discord_id = member.id

        return discord_id

    def get_discord_name(self, discord_id):
        """
        Find the discord name of a member
        :param discord_id: Discord ID number
        :return: string Discord display_name
        """
        discord_name = ""

        # if a valid dict entry was passed in...
        if len(discord_id) > 0:
            discord_id = discord_id[0]['discord_id']

        # loop through members of guild, if match
        # is found, grab the display_name
        for member in self.get_guild().members:
            if str(discord_id) == str(member.id):
                discord_name = member.display_name

        return discord_name

    def get_all_discord_names(self, name_type):
        """
        Grab all member display_names
        :return: list of Discord display_names
        """
        discord_names = []

        # loop through all members, add display_names to list
        for member in self.get_guild().members:
            if name_type == "display":
                discord_names.append(member.display_name)
            elif name_type == "name":
                discord_names.append(member.name)

        # fancy looking, but just sorts both lists case insensitively
        discord_names.sort(key=lambda s: s.lower())

        return discord_names

    def get_combined_names(self, database_names):
        """
        Take all char names from database and account names from Discord;
        concatenate them together into a master list
        :param database_names: list of dict entries;
        discord_id and char_names obtained from database
        :return:
        """
        combined_names_list = []

        # loop through each name
        for guild_member in database_names:
            # for each name, loop through all members of guild
            for discord_member in self.get_guild().members:
                # if match found
                if str(guild_member['discord_id']) == str(discord_member.id):
                    # isolate char_name
                    char_name = guild_member['char_name']
                    # isolate discord name
                    discord_name = discord_member.name
                    # put them together, then exit inner loop
                    combined_names_list.append(f"[ {char_name} ]" + " " * 4 + f"[ {discord_name} ]")
                    break

        return combined_names_list

    def get_row(self, results):
        """
        Return correct form of row based on number of results
        :param results: int
        :return: string
        """
        if results == 1:
            row = "row"
        else:
            row = "rows"

        return row

    def get_races(self):
        """
        Return EQ races
        :return: list
        """
        races = [
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

        return races

    def get_classes(self):
        """
        Return EQ classes
        :return: list
        """
        classes = [
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

        return classes

    def get_types(self):
        """
        Return database character types
        :return: list
        """
        types = [
                'Main',
                'Alt',
                'Mule'
            ]

        return types
