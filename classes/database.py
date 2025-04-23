from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from os import environ


class Database:
    """
    This class provides all database interaction
    """

    def __init__(self):
        load_dotenv()

        # obtain database parameters securely as environment variables
        self._MYSQL_USER = environ.get('MYSQL_USER')
        self._MYSQL_PASSWORD = environ.get('MYSQL_PASSWORD')
        self._MYSQL_HOST = environ.get('MYSQL_HOST')
        self._MYSQL_DB = environ.get('MYSQL_DB')

        # set connection string
        self._params = f"mysql+pymysql://{self._MYSQL_USER}:{self._MYSQL_PASSWORD}@{self._MYSQL_HOST}/{self._MYSQL_DB}?charset=utf8mb4"

    ################# READ METHODS #################
    def get_discord_ids(self):
        """
        Get discord ids and char names
        :return: results of the select query, in list form
        """
        query = (
            ("SELECT discord_id, char_name FROM sos_bot.characters "
             "WHERE char_type = 'Main' ORDER BY char_name")
        )

        return self.execute_read(query)

    def lookup_characters(self, char_name):
        """
        Get all character details that share the same discord id and match
        the char name entered, sorted by the priority level of the chars
        (i.e., mains, then alts, then mules)
        :char_name: the name to look up
        :return: results of the select query, in list form
        """
        query = (
            "SELECT b.char_name, b.char_race, b.char_class, b.char_type, b.char_priority FROM sos_bot.characters a"
            f" JOIN sos_bot.characters b ON a.discord_id = b.discord_id WHERE a.char_name = '{char_name}'"
            "ORDER BY b.char_priority ASC"
        )

        return self.execute_read(query)

    def find_main_from_discord(self, discord_id):
        """
        Get main character for a given discord id
        :discord_id: discord id to look up
        :return: results of the select query, in list form
        """
        query = (
            "SELECT char_name from sos_bot.characters WHERE "
            f" discord_id = {discord_id} AND char_type = 'Main'"
        )

        return self.execute_read(query)

    def lookup_discord_id(self, char_name):
        """
        Get discord id for a given char name
        :char_name: the name to lookup
        :return: results of the select query, in list form
        """
        query = (
            "SELECT discord_id from sos_bot.characters WHERE "
            f" char_name = '{char_name}'"
        )

        return self.execute_read(query)

    def find_all_mains(self):
        """
        Get all chars flagged as mains
        :return: results of the select query, in list form
        """
        query = (
            "SELECT char_name FROM sos_bot.characters WHERE char_type = 'Main' ORDER BY char_name"
        )

        return self.get_list(self.execute_read(query), 'char_name')

    def get_all_characters(self):
        """
        Get all discord ids and char names
        :return: results of the select query, in list form
        """
        query = (
            "SELECT discord_id, char_name FROM sos_bot.characters"
        )

        return self.execute_read(query)

    def get_all_char_names(self):
        """
        Get all char names only from database, uses
        previous query and filters its result
        :return: results of the query, in list form
        """
        return self.get_list(self.get_all_characters(), 'char_name')

    def get_all_mob_names(self):
        """
        Get all mob names
        :return: results of the select query, in list form
        """
        query = (
            "SELECT mob_name FROM sos_bot.respawns"
        )

        return self.get_list(self.execute_read(query), 'mob_name')

    def get_all_zone_names(self):
        """
        Get all zone names
        :return: results of the select query, in list form
        """
        query = (
            "SELECT DISTINCT mob_zone FROM sos_bot.respawns"
        )

        return self.get_list(self.execute_read(query), 'mob_zone')

    def get_mob_data(self, mob_name):
        """
        obtain all fields of a mob's database entry
        :param mob_name: string
        :return: results of the select query, in list form
        """
        query = f"SELECT * FROM sos_bot.respawns WHERE mob_name = '{mob_name}'"

        return self.execute_read(query)

    def get_mob_respawn(self, mob_name):
        """
        get the kill, respawn, and time zone data for a mob
        :param mob_name: string
        :return: results of the select query, in list form
        """
        query = (f"SELECT mob_name, kill_time, respawn_time, time_zone FROM sos_bot.respawns "
                 f"WHERE mob_name = '{mob_name}'")

        return self.execute_read(query)

    def get_zone_respawns(self, zone_name):
        """
        obtain all fields of each mob's database entry for a given zone
        :param zone_name: string
        :return: results of the select query, in list form
        """
        # special processing to handle single quotes in zone names
        # single quotes are invalid in SQL queries
        find_quote = zone_name.find("'")

        # if a single quote was found, insert an additional
        # single quote into the SQL string at the position
        # of the existing quote, this escapes the quote,
        # allowing the query string to go through as valid
        if find_quote != -1:
            temp_zone = zone_name
            zone_name = temp_zone[:find_quote] + "'" + temp_zone[find_quote:]

        query = (f"SELECT mob_name, kill_time, respawn_time, time_zone FROM sos_bot.respawns "
                 f"WHERE mob_zone = '{zone_name}'")

        return self.execute_read(query)

    ################# UPDATE METHODS #################
    def insert_character(self, discord_id, char_name, char_race, char_class, char_type, char_priority):
        """
        Add a new character to the database
        :parameters: the details of the new character
        :return: results of the insert query
        """
        query = (
            "INSERT INTO sos_bot.characters"
            "(discord_id, char_name, char_race, char_class, char_type, is_officer, char_priority)"
            f" VALUES ('{discord_id}', '{char_name}', '{char_race}', '{char_class}', '{char_type}', 0, {char_priority})"
        )

        return self.execute_update(query)

    def update_character(self, char_name, new_name, char_race, char_class, char_type):
        """
        Edit an existing character to have new attributes
        :parameters: the updated details of the character
        :return: results of the update query, in list form
        """
        # begin the query string
        query = f"UPDATE sos_bot.characters SET "

        # add only the options selected by user to query
        if new_name is not None:
            query = query + f"char_name = '{new_name}', "

        if char_race is not None:
            query = query + f"char_race = '{char_race}', "

        if char_class is not None:
            query = query + f"char_class = '{char_class}', "

        # translate char type to an int, since this is hidden from user
        if char_type is not None:
            if char_type == 'Main':
                char_priority = 0
            elif char_type == 'Alt':
                char_priority = 1
            else:
                char_priority = 2

            query = query + f"char_type = '{char_type}', char_priority = {char_priority}, "

        # trim off trailing comma and space, then add WHERE clause
        query = query[0:len(query) - 2]
        query = query + f" WHERE char_name = '{char_name}'"

        return self.execute_update(query)

    def delete_character(self, char_name):
        """
        Remove character from database
        :char_name: string, the name to delete
        :return: results of the delete query, in list form
        """
        query = f"DELETE FROM sos_bot.characters WHERE char_name = '{char_name}'"

        return self.execute_update(query)

    def update_kill_time(self, mob_name, kill_time, respawn_time, time_zone):
        """
        edit database entry for a given mob with new kill time,
        respawn time, and time zone
        :param mob_name: string
        :param kill_time: datetime in string format
        :param respawn_time: datetime in string format
        :param time_zone: string
        :return: results of the update query, in list form
        """
        query = (
            f"UPDATE sos_bot.respawns SET kill_time = '{kill_time}', respawn_time = '{respawn_time}', "
            f"time_zone = '{time_zone}' WHERE mob_name = '{mob_name}'"
        )

        return self.execute_update(query)

    def update_mob_respawn(self, mob_name, respawn_dict):
        """
        edit the database entry for a mob with respawn timer data
        :param mob_name: string
        :param respawn_dict: dictionary of int values, with keys corresponding to units of time
        :return: results of the update query, in list form
        """
        query = (
            f"UPDATE sos_bot.respawns SET lockout_weeks = '{respawn_dict['weeks']}', "
            f"lockout_days = '{respawn_dict['days']}', lockout_hours = '{respawn_dict['hours']}', "
            f"lockout_minutes = '{respawn_dict['minutes']}' "
            f"WHERE mob_name = '{mob_name}'"
        )

        return self.execute_update(query)

    ################# UTILITY METHODS #################
    def create_engine(self):
        """
        create a new engine object upon request, to prevent
        MySQL server from timing out
        :return: SQL alchemy engine object
        """
        # create the query engine
        return create_engine(self._params)

    def execute_read(self, query):
        """
        Send a read query to database engine
        :query: the formatted query string to send
        to database engine
        :return: results of the operation, in list form
        """
        records_list = []

        # open a connection to database, dynamically close
        # it when with block closes
        with self.create_engine().connect() as conn:
            result = conn.execute(text(query))

            # get query results and, line by line,
            # convert to dict entries; add each
            # dict to list
            for row in result.all():
                row_to_dict = row._asdict()
                records_list.append(row_to_dict)

            conn.close()

        return records_list

    def execute_update(self, query):
        """
        Send an update query to database engine
        :query: the formatted query string to send
        to database engine
        :return: int, representing the results of the operation
        """
        # open a connection to database, dynamically close
        # it when with block closes
        with self.create_engine().connect() as conn:
            # get a count of rows affected, to act as
            # indicator of success or failure
            result = conn.execute(text(query)).rowcount
            conn.commit()

            conn.close()

        return result

    def get_list(self, results, field):
        """
        Take in a list of dicts and return a list of strings
        :param results: list of dict entries
        :param field: the desired dict key
        :return: list of dict values corresponding to the given key
        """
        results_list = []

        for result in results:
            results_list.append(result[field])

        return results_list

    def format_quotes(self, mob_name):
        quote_index = mob_name.find("'")

        if quote_index != -1:
            temp_string = mob_name
            mob_name = temp_string[:quote_index] + "'" + temp_string[quote_index:]

        return mob_name
