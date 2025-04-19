import time
from datetime import datetime, timedelta
import requests


class Tracker:
    def __init__(self):
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

    def calculate_respawn(self, kill_time):
        kill_time = "Thu Apr 17 23:57:03 2025"
        format_string = "%a %b %d %H:%M:%S %Y"

        datetime_killtime = datetime.strptime(kill_time, format_string)
        respawn_time = datetime_killtime + timedelta(days=2, hours=18)
        timezone_name = respawn_time.astimezone().tzname()

        print(datetime_killtime)
        print(respawn_time)
        print(timezone_name)

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
        mob_start = line.find('killed') + 7
        mob_end = line.find('in') - 1

        mob_name = line[mob_start:mob_end]

        return mob_name
