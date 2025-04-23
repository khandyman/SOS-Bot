import time
from datetime import datetime, timedelta
from classes.database import Database
import requests


class Tracker:
    """
    This class provides a generator for real time log file parsing
    and logic to calculate respawn times, scrape data from the Quarm
    database, and interact with the bot database
    """
    def __init__(self):
        self._database = Database()
        # log file path to track
        self._file_path = "C:\\EQ-ProjectQuarm\\eqlog_Torynmule_pq.proj.txt"
        self._file = open(self._file_path, 'r')

    def follow(self):
        """
        a generator function to read the last line of a
        log file, as it is written, and yield that line
        to the caller
        :yield: the line that was just written to the log
        """
        # set cursor position to end of file
        self._file.seek(0,2)

        # infinite loop
        while True:
            line = self._file.readline()

            # if no line written, pause briefly, then rescan
            if not line:
                time.sleep(0.1)
                continue

            # if new line exists, yield it back to caller and
            # pause generator
            yield line

    def calculate_respawn(self, mob_name, kill_time):
        """
        add the respawn time for a mob to its latest kill time
        :param mob_name: string
        :param kill_time: datetime in string format
        :return:
        """
        # set the format of the datetime string
        format_string = "%Y-%m-%d %H:%M:%S"
        # convert it into an actual datetime object
        datetime_killtime = datetime.strptime(kill_time, format_string)

        # get the respawn time units of a mob from database
        mob_data = self._database.get_mob_data(mob_name)

        # convert to ints, for arithmetic
        delta_weeks = int(mob_data[0]['lockout_weeks'])
        delta_days = int(mob_data[0]['lockout_days'])
        delta_hours = int(mob_data[0]['lockout_hours'])
        delta_minutes = int(mob_data[0]['lockout_minutes'])

        # create a time delta object with the time units obtained from database
        add_time = timedelta(
            weeks=delta_weeks,
            days=delta_days,
            hours=delta_hours,
            minutes=delta_minutes
        )

        # add the time delta to the kill time
        respawn_time = datetime_killtime + add_time

        return respawn_time

    def scrape_respawn(self, mob):
        """
        perform a scrape of HTML source code from Quarm
        database to update mob respawn time units
        :param mob:
        :return:
        """
        respawn_dict = {}

        # get the html source from pqdi
        url = "https://www.pqdi.cc/instances"
        page = requests.get(url, verify=False)
        html = page.text

        # search for the mob name given as a parameter
        start = html.find(mob)
        # find the next occurrence of Respawn Time, this should
        # be the entry for the current mob
        respawn_flag = html.find('Respawn Time', start)
        # look for the next html tag opener, this should be the next line
        next_line_flag = html.find('<', respawn_flag)
        # slice out the text containing just the respawn data
        respawn_time = html[respawn_flag + 13:next_line_flag - 1].strip()

        # set up dictionary with ints for time units
        # parsed out of the respawn time found above
        respawn_dict['weeks'] = self.get_parsed_int(respawn_time, 'week')
        respawn_dict['days'] = self.get_parsed_int(respawn_time, 'day')
        respawn_dict['hours'] = self.get_parsed_int(respawn_time, 'hour')
        respawn_dict['minutes'] = self.get_parsed_int(respawn_time, 'minute')

        return respawn_dict

    def get_parsed_int(self, respawn, time_type):
        """
        helper method to parse the integers for the time
        units needed by the scrape method
        :param respawn: string of time data
        :param time_type: the time unit to locate
        :return: int, the time unit found
        """
        # set start index based on time type
        starting_point = respawn.find(time_type)

        # logic to handle single vs double-digit entries
        # weeks and days will be a max of 1 digit, hours
        # and days could be two
        if time_type == 'week' or time_type == 'day':
            first_point = 2
        else:
            first_point = 3

        # if the time unit was found, slice out just the int
        # from the string
        if starting_point != -1:
            parsed_int = respawn[respawn.find(time_type) - first_point:
                                 respawn.find(time_type) - 1]
        # otherwise, return 0
        else:
            parsed_int = 0

        return parsed_int

    def parse_time(self, line):
        """
        method to parse just the time data at the beginning
        of an EQ log file line
        :param line: string
        :return: string
        """
        # split the line into a list of words
        separates = line.split()

        # convert the month from abbreviated text to an int
        month_int = str(datetime.strptime(separates[1], "%b").month).zfill(2)

        # create a new string with specific formatting, using pre-defined
        # indexes in the separated list created above
        kill_time = f"{separates[4].strip("]")}-{month_int}-{separates[2]} {separates[3]}"

        return kill_time

    def parse_mob(self, line):
        """
        method to parse the mob name from an
        an EQ log file line
        :param line: string
        :return: string
        """
        # set the starting index
        mob_start = line.find(' killed ') + 8
        # set the ending index
        mob_end = line.find(' in ')

        # slice out the mob name, could be multiple words
        mob_name = line[mob_start:mob_end]

        return mob_name

    def update_kill_time(self, mob_name, kill_time):
        """
        edit the database entry for a mob with new kill and respawn times
        :param mob_name: string
        :param kill_time: string
        :return: formatted string
        """
        # kill_time = "Thu Apr 17 23:57:03 2025"        # an example of the incoming kill_time format

        # get the respawn time from the calculate respawn method
        respawn_time = self.calculate_respawn(mob_name, kill_time)
        # get the time zone of the PC the mule is logged in on
        time_zone = datetime.now().astimezone().tzname()

        # print to console, to indicate a new log file capture
        print(f"{mob_name} | {kill_time} | {respawn_time} | {time_zone}")

        # attempt to update the database, print success or
        # failure message to console
        if self._database.update_kill_time(mob_name, kill_time, respawn_time, time_zone):
            kill_message = f"```Database insert of kill time for {mob_name} succeeded.```"
        else:
            kill_message = f"```Database insert of kill time for {mob_name} failed.```"

        print(kill_message)

    def update_respawn_times(self, mob_list):
        """
        interface method between scrape_respawn and database update_mob_respawn
        :param mob_list: list of mob names
        :return: none
        """
        # loop through mob list, scrape respawn data for current mob
        # and update database with scraped time units
        for mob in mob_list:
            current_respawn = self.scrape_respawn(mob)
            self._database.update_mob_respawn(mob, current_respawn)
            # print to console, to act as a progress bar
            print(f"{mob}: {current_respawn}")

    def get_mob_respawn(self, mob_name):
        """
        return mob respawn data from database
        :param mob_name: string
        :return: list of a single dict entry
        """
        mob_data = self._database.get_mob_respawn(mob_name)

        return mob_data

    def get_zone_respawns(self, zone_name):
        """
        return mob respawns for an entire zone
        :param zone_name: string
        :return: list of dict entries, one per mob
        """
        zone_data = self._database.get_zone_respawns(zone_name)

        return zone_data
