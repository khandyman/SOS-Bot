from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from os import environ


class Database:
    def __init__(self):
        load_dotenv()

        self._MYSQL_USER = environ.get('MYSQL_USER')
        self._MYSQL_PASSWORD = environ.get('MYSQL_PASSWORD')
        self._MYSQL_HOST = environ.get('MYSQL_HOST')
        self._MYSQL_DB = environ.get('MYSQL_DB')

        self._params = f"mysql+pymysql://{self._MYSQL_USER}:{self._MYSQL_PASSWORD}@{self._MYSQL_HOST}/{self._MYSQL_DB}?charset=utf8mb4"

        self._engine = create_engine(self._params)

    def get_discord_ids(self):
        query = (
            ("SELECT discord_id, char_name FROM sos_bot.characters "
             "WHERE char_type = 'Main' ORDER BY char_name")
        )

        return self.execute_read(query)

    def lookup_eq(self, char_name):
        query = (
            "SELECT b.char_name, b.char_race, b.char_class, b.char_type, b.char_priority FROM sos_bot.characters a"
            f" JOIN sos_bot.characters b ON a.discord_id = b.discord_id WHERE a.char_name = '{char_name}'"
            "ORDER BY b.char_priority ASC"
        )

        return self.execute_read(query)

    def lookup_discord(self, discord_id):
        query = (
            "SELECT char_name, char_race, char_class, char_type, char_priority FROM sos_bot.characters"
            f" WHERE discord_id = '{discord_id}' ORDER BY char_priority ASC"
        )

        return self.execute_read(query)

    def lookup_main(self, discord_id):
        query = (
            "SELECT char_name from sos_bot.characters WHERE "
            f" discord_id = {discord_id} AND char_type = 'Main'"
        )

        return self.execute_read(query)

    def lookup_discord_id(self, char_name):
        query = (
            "SELECT discord_id from sos_bot.characters WHERE "
            f" char_name = '{char_name}'"
        )

        return self.execute_read(query)

    def get_all_mains(self):
        query = (
            "SELECT char_name FROM sos_bot.characters WHERE char_type = 'Main' ORDER BY char_name"
        )

        return self.get_list(self.execute_read(query), 'char_name')

    def get_all_characters(self):
        query = (
            "SELECT discord_id, char_name FROM sos_bot.characters"
        )

        return self.execute_read(query)

    def get_all_char_names(self):
        return self.get_list(self.get_all_characters(), 'char_name')

    def insert_character(self, discord_id, char_name, char_race, char_class, char_type, char_priority):
        query = (
            "INSERT INTO sos_bot.characters"
            "(discord_id, char_name, char_race, char_class, char_type, is_officer, char_priority)"
            f" VALUES ('{discord_id}', '{char_name}', '{char_race}', '{char_class}', '{char_type}', 0, {char_priority})"
        )

        return self.execute_update(query)

    def update_character(self, char_name, new_name, char_race, char_class, char_type):
        query = f"UPDATE sos_bot.characters SET "

        if new_name is not None:
            query = query + f"char_name = '{new_name}', "

        if char_race is not None:
            query = query + f"char_race = '{char_race}', "

        if char_class is not None:
            query = query + f"char_class = '{char_class}', "

        if char_type is not None:
            if char_type == 'Main':
                char_priority = 0
            elif char_type == 'Alt':
                char_priority = 1
            else:
                char_priority = 2

            query = query + f"char_type = '{char_type}', char_priority = {char_priority}, "

        query = query[0:len(query) - 2]
        query = query + f" WHERE char_name = '{char_name}'"

        return self.execute_update(query)

    def delete_character(self, char_name):
        query = f"DELETE FROM sos_bot.characters WHERE char_name = '{char_name}'"

        return self.execute_update(query)

    def execute_read(self, query):
        records_list = []

        with self._engine.connect() as conn:
            result = conn.execute(text(query))

            for row in result.all():
                row_to_dict = row._asdict()
                records_list.append(row_to_dict)

            conn.close()

        return records_list

    def execute_update(self, query):
        with self._engine.connect() as conn:
            result = conn.execute(text(query)).rowcount
            conn.commit()

            conn.close()

        return result

    def get_list(self, results, field):
        results_list = []

        for result in results:
            results_list.append(result[field])

        return results_list
