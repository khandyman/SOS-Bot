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

    def retrieve_records(self, sql_string):
        records_list = []

        with self._engine.connect() as conn:
            result = conn.execute(text(sql_string))

            for row in result.all():
                row_to_dict = row._asdict()
                records_list.append(row_to_dict)

        return records_list

    def insert_user(self, usr, pwd):
        pwd = str(generate_password_hash(pwd))

        query = f"INSERT INTO users (user_name, user_password) values ('{usr}', '{pwd}')"

        with self._engine.connect() as conn:
            result = conn.execute(text(query))

        return result
