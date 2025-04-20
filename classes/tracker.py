import time
from datetime import datetime, timedelta
from classes.database import Database
import requests


class Tracker:
    def __init__(self):
        self._db = Database()
        self._file_path = "C:\\EQ-ProjectQuarm\\eqlog_Torynmule_pq.proj.txt"
        self._file = open(self._file_path, 'r')

    def follow(self):
        self._file.seek(0,2)

        while True:
            line = self._file.readline()

            if not line:
                time.sleep(0.1)
                continue

            yield line

    def calculate_respawn(self, mob_name, kill_time):
        # kill_time = "Thu Apr 17 23:57:03 2025"
        format_string = "%a %b %d %H:%M:%S %Y"
        datetime_killtime = datetime.strptime(kill_time, format_string)

        mob_data = self._db.get_mob_data(mob_name)

        delta_weeks = int(mob_data[0]['lockout_weeks'])
        delta_days = int(mob_data[0]['lockout_days'])
        delta_hours = int(mob_data[0]['lockout_hours'])
        delta_minutes = int(mob_data[0]['lockout_minutes'])

        add_time = timedelta(weeks=delta_weeks, days=delta_days, hours=delta_hours, minutes=delta_minutes)
        respawn_time = datetime_killtime + add_time

        timezone_name = respawn_time.astimezone().tzname()

        # print(f"mob name: {mob_data[0]['mob_name']}")
        # print(f"kill time: {datetime_killtime}")
        # print(f"respawn_time: {respawn_time}")
        # print(f"time zone: {timezone_name}")

        return respawn_time

    def scrape_respawn(self, mob):
        respawn_dict = {}

        url = "https://www.pqdi.cc/instances"
        page = requests.get(url, verify=False)
        html = page.text

        start = html.find(mob)
        respawn_flag = html.find('Respawn Time', start)
        next_line_flag = html.find('<', respawn_flag)
        respawn_time = html[respawn_flag + 13:next_line_flag - 1].strip()

        respawn_dict['weeks'] = self.get_parsed_int(respawn_time, 'week')
        respawn_dict['days'] = self.get_parsed_int(respawn_time, 'day')
        respawn_dict['hours'] = self.get_parsed_int(respawn_time, 'hour')
        respawn_dict['minutes'] = self.get_parsed_int(respawn_time, 'minute')

        return respawn_dict

    def get_parsed_int(self, respawn, time_type):
        starting_point = respawn.find(time_type)

        if time_type == 'week' or time_type == 'day':
            first_point = 2
        else:
            first_point = 3

        if starting_point != -1:
            parsed_int = respawn[respawn.find(time_type) - first_point:
                                 respawn.find(time_type) - 1]
        else:
            parsed_int = 0

        return parsed_int

    def parse_time(self, line):
        separates = line.split()
        time_string = ""

        for i in range(0, 5):
            time_part = separates[i].strip("[]")
            time_string = time_string + time_part + " "

        final_string = time_string[0:len(time_string) - 1]

        return final_string

    def parse_mob(self, line):
        mob_start = line.find(' killed ') + 8
        mob_end = line.find(' in ')

        mob_name = line[mob_start:mob_end]

        return mob_name

    def update_kill_time(self, mob_name, kill_time):
        # kill_time = "Thu Apr 17 23:57:03 2025"
        respawn_time = self.calculate_respawn(mob_name, kill_time)
        time_zone = respawn_time.astimezone().tzname()

        print(mob_name)
        print(kill_time)
        print(respawn_time)
        print(time_zone)

        if self._db.update_kill_time(mob_name, kill_time, respawn_time, time_zone):
            kill_message = (
                f"```{mob_name} was killed at: {kill_time}.\n"
                f"It will respawn at: {respawn_time}.```"
            )
        else:
            kill_message = f"```Database insert of kill time for {mob_name} failed.```"

        return kill_message

    def update_respawn_times(self, mob_list):
        for mob in mob_list:
            current_respawn = self.scrape_respawn(mob)
            self._db.update_mob_respawns(mob, current_respawn)
            print(f"{mob}: {current_respawn}")

    def get_mob_respawn(self, mob_name):
        mob_data = self._db.get_respawn_time(mob_name)

        return mob_data
