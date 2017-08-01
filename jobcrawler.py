#!/usr/bin/python
"""
 Copyright (C) Alan Verdugo.

 Description:
    This program will monitor the indeed.com API in search of interesting 
    jobs postings.
    Once it finds anything, it will send a notification email to the
    specified recipients.
    Also, it will save the data of the interesting job openings into a 
    results file, which then could be analysed in search of patterns.

 Usage:
    python jobcrawler.py [-h] -q QUERY [-l LOCATION] -c COUNTRY_CODE

 Arguments:
    QUERY : The query to search in the API.
        E.g.:
            "software engineer"
            "software engineer company:google"      
    LOCATION : The location for the job E.g.: "Austin, TX"
    COUNTRY_CODE : The country code. E.g.: us, mx, jp, gb, ca.
        Default: us

 Author:
    Alan Verdugo (alan@kippel.net)

 Creation date:
    2016-06-08

 Revision history:
    Author:     Date:       Notes:
    Alan        2016-06-08  Added this header.
    Alan        2016-06-11  Separated everything into functions.
    Alan        2016-07-16  Added some error checking.
    Alan        2016-07-17  Improved style according to:
                            https://google.github.io/styleguide/pyguide.html
    Alan        2016-07-20  Replaced getopt with argparse.
                            Added the get_job_summary function.
    Alan        2016-07-24  Added os module for handling paths and files.
    Alan        2017-07-14  Did some cleanup.
"""

import os

import sys

import json

import logging

# Custom module for email sending (refer to emailer.py)
import emailer

# For the actual email sending.
import smtplib

# To get the API call results.
import requests

# To get arguments from CLI.
import argparse

# Some email modules we'll need.
from email.mime.text import MIMEText

from bs4 import BeautifulSoup


# TODO: Change this to read from config.json
headers = {'content-type': 'application/json'}
home_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(home_dir, "results.json")

config_file = os.path.join(home_dir, "config.json")

# Logging configuration.
log = logging.getLogger("jobcrawler")
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
log.setLevel(logging.INFO)

# Simple search
# http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX&q=google&l=austin%2C+tx&sort=&radius=&st=&jt=&start=&limit=100&fromage=&filter=&latlong=1&co=us&chnl=&userip=1.2.3.4&useragent=Mozilla/%2F4.0(Firefox)&v=2&format=json

# All software engineer jobs from Google in the US
#http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX&q=software+engineer+company:google&l=&sort=&highlight=false&radius=&st=&jt=&start=&limit=100&fromage=&filter=&latlong=1&co=us&chnl=&userip=1.2.3.4&useragent=Mozilla/%2F4.0(Firefox)&v=2&format=json

# All software engineer jobs from Google in Japan
#http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX&q=software+engineer+company:google&l=&sort=&highlight=false&radius=&st=&jt=&start=&limit=100&fromage=&filter=&latlong=1&co=jp&chnl=&userip=1.2.3.4&useragent=Mozilla/%2F4.0(Firefox)&v=2&format=json


def get_args(argv):
    '''
        Parse and validate arguments.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("-q","--query", 
        dest="query",
        help="The query to search in the API",
        required=True)
    parser.add_argument("-l","--location", 
        dest="location",
        help="The location for the job E.g.: Austin, TX")
    parser.add_argument("-c","--country", 
        dest="country_code", 
        help="The country code. E.g.: us, mx, jp, gb, ca.",
        default="us",
        required=True)
    args = parser.parse_args()
    main(args.query, args.country_code, args.location)


class _Settings(object):
    '''
        I've named the class with a single leading underscore (just like the 
        two instance attributes that underlie the read-only properties) to 
        suggest that it's not meant to be used from "outside" the module -- 
        only the settings object is supposed to be.
        get properties as "settings.publisher_ID", etc
        set properties like "settings = _Settings(<publisher_ID_value>, <etc>)"
        https://stackoverflow.com/questions/3640700/alternative-to-passing-global-variables-around-to-classes-and-functions
    '''
    @property
    def publisher_ID(self): return self._publisher_ID
    @property
    def output_format(self): return self._output_format
    @property
    def limit(self): return self._limit
    @property
    def from_age(self): return self._from_age
    @property
    def highlight(self): return self._highlight
    @property
    def sort(self): return self._sort
    @property
    def radius(self): return self._radius
    @property
    def site_type(self): return self._site_type
    @property
    def job_type(self): return self._job_type
    @property
    def start(self): return self._start
    @property
    def duplicate_filter(self): return self._duplicate_filter
    @property
    def lat_long(self): return self._lat_long
    @property
    def channel(self): return self._channel
    @property
    def user_IP(self): return self._user_IP
    @property
    def user_agent(self): return self._user_agent
    @property
    def version(self): return self._version
    def __init__(self, publisher_ID, output_format, limit, from_age, 
        highlight, sort, radius, site_type, job_type, start, duplicate_filter,
        lat_long, channel, user_IP, user_agent, version):
        self._publisher_ID = publisher_ID
        self._output_format = output_format
        self._limit = limit
        self._from_age = from_age
        self._highlight = highlight
        self._sort = sort
        self._radius = radius
        self._site_type = site_type
        self._job_type = job_type
        self._start = start
        self._duplicate_filter = duplicate_filter
        self._lat_long = lat_long
        self._channel = channel
        self._user_IP = user_IP
        self._user_agent = user_agent
        self._version = version


def read_config():
    '''
        This function will read the configuration values from config.json
        and assign the values to a "settings" object.
    '''
    try:
        config = json.load(open(config_file, "r+"))

        request_config = config["request"]

        publisher_ID = request_config["publisher_ID"]
        output_format = request_config["output_format"]
        limit = request_config["limit"]
        from_age = request_config["from_age"]
        highlight = request_config["highlight"]
        sort = request_config["sort"]
        radius = request_config["radius"]
        site_type = request_config["site_type"]
        job_type = request_config["job_type"]
        start = request_config["start"]
        duplicate_filter = request_config["duplicate_filter"]
        lat_long = request_config["lat_long"]
        channel = request_config["channel"]
        user_IP = request_config["user_IP"]
        user_agent = request_config["user_agent"]
        version = request_config["version"]

    except Exception as exception:
        log.error("Cannot read configuration file. {0}".format(exception))
        sys.exit(1)


def get_job_summary(url):
    '''
        This function will access the URL from each job result in the 
        api_response, and get the contents of the "job_summary" object 
        in the DOM (i.e. the actual description text of the job).
    ''' 
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text,"html5lib")
        # Only 1 job summary per page, so we can use find instead of findAll
        job_summary = soup.find("span", attrs={"id" : "job_summary"})
        print "-----JOB SUMMARY:-----\n",job_summary.text
    except Exception as error:
        log.error("Unable to get response from URL: {0} {1}".format(url, error))


def save_result():
    '''
        This function will save new job results into the appropiate file/DB,
        and it will NOT save any duplicates.
    '''
    # If there is not a directory for this <countryCode>_<query> combo, 
    # create one.
    results_dir = home_dir + country_code + query
    results_file = os.path.join(results_dir, "results.json")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    # If the results file does not exist, create it.
    if not os.path.exists(results_file):
        os.makedirs(results_file)
    # if the results file does exists, open it.
    # Open the results file so we can add new results.
    #try:
    #   results_file_handle = open(results_file, "r+")
    #   results_file_handle.close() # Close file. 
    #except Exception as exception:
    #   print "ERROR: Unable to open", str(resultsFile), exception
    #   sys.exit(1)
    # Make sure we are not inserting a duplicate into the results file.
    # Read all the jobkeys (Unique IDs) to avoid inserting duplicates.
    # Close the appropiate results file.


def main(query, country_code, location):
    # Arguments for the API call,
    # (refer to https://ads.indeed.com/jobroll/xmlfeed)
    # TODO: Read all this from a config file.
    read_config()

    # Concatenate the provided values to form the request URL.
    # TODO: Change the string concatenation into a list,
    # then concatenate the list items.
    indeed_url = "http://api.indeed.com/ads/apisearch?"
    indeed_url += "publisher=" + publisher_ID
    indeed_url += "&q=" + query
    if location:
        indeed_url += "&l=" + location
    indeed_url += "&sort=" + sort
    indeed_url += "&radius=" + radius
    indeed_url += "&st=" + site_type
    indeed_url += "&jt=" + job_type
    indeed_url += "&start=" + start
    indeed_url += "&limit=" + limit
    indeed_url += "&fromage=" + from_age
    indeed_url += "&highlight=" + highlight
    indeed_url += "&filter=" + duplicate_filter
    indeed_url += "&latlong=" + lat_long
    indeed_url += "&co=" + country_code
    indeed_url += "&chnl=" + channel
    indeed_url += "&userip=" + user_IP
    indeed_url += "&useragent=" + user_agent
    indeed_url += "&v=" + version
    indeed_url += "&format=" + output_format

    try:
        api_response = requests.get(indeed_url, headers=headers)
    except Exception as error:
        log.error("Unable to get response from API: {0}".format(error))
        sys.exit(1)

    # The status code should be 200 (success). Catch anything else and handle.
    if api_response.status_code != 200:
        log.error("The response status is: {0}".format(response.status_code))
        sys.exit(1)

    # Validate that we got a non-empty result set.
    try:
        readable_api_response = api_response.json()
    except ValueError:
        log.warning("Empty result set. Request URL: {0}".format(indeed_url))
        sys.exit(2)

    # Validate that there were job openings returned.
    try:
        api_results = readable_api_response["results"]
    except KeyError:
        log.warning("No results found. Request URL: {0}".format(indeed_url))
        sys.exit(3)

    # Parse the response from the Indeed API.
    for job in api_results:
        job_title = job["jobtitle"]
        get_job_summary(job["url"])
        # Finally, save the results into the results file.
        save_result()
    sys.exit()


if __name__ == "__main__":
    get_args(sys.argv[1:])
