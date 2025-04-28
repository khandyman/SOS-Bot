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
