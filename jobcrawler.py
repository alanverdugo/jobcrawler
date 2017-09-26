#!/usr/bin/python
"""
 Description:
    This program will monitor the indeed.com API in search of interesting 
    jobs postings.
    Once it finds anything, it will send a notification email to the
    specified recipients.
    Also, it will analyse the data of the interesting job openings.

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
    Alan        2017-09-22  Major changes.
                            Added the analyze_most_common_words function.
                            Removed save_results.
                            Fixed the Settings class.
    Alan        2017-09-26  We now send en email with all the jobs' data.
                            Fixed some bugs.
"""

import os

import sys

import json

import logging

# Custom module for email sending (refer to emailer.py)
import emailer

# To get the API call results.
import requests

# To get arguments from CLI.
import argparse

# For getting data from HTML pages.
from bs4 import BeautifulSoup

# For text analysis.
from collections import Counter

# To get punctuation sumbols (,.:;?!...).
import string

# For text analysis.
import nltk


home_dir = os.path.dirname(os.path.abspath(__file__))

config_file = os.path.join(home_dir, "config.json")

# Logging configuration.
log = logging.getLogger("jobcrawler")
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
log.setLevel(logging.INFO)


## Indeed.com API call examples:
# Simple search
# http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX
#   &q=google
#   &l=austin%2C+tx
#   &sort=
#   &radius=
#   &st=
#   &jt=
#   &start=
#   &limit=100
#   &fromage=
#   &filter=
#   &latlong=1
#   &co=us
#   &chnl=
#   &userip=1.2.3.4
#   &useragent=Mozilla/%2F4.0(Firefox)
#   &v=2&format=json

# All software engineer jobs from Google in the US
# http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX
#   &q=software+engineer+company:google
#   &l=&sort=
#   &highlight=false
#   &radius=
#   &st=
#   &jt=
#   &start=
#   &limit=100
#   &fromage=
#   &filter=
#   &latlong=1
#   &co=us
#   &chnl=
#   &userip=1.2.3.4
#   &useragent=Mozilla/%2F4.0(Firefox)
#   &v=2&format=json

# All software engineer jobs from Google in Japan
# http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX
#   &q=software+engineer+company:google
#   &l=&sort=
#   &highlight=false
#   &radius=
#   &st=
#   &jt=
#   &start=
#   &limit=100
#   &fromage=
#   &filter=
#   &latlong=1
#   &co=jp
#   &chnl=
#   &userip=1.2.3.4&useragent=Mozilla/%2F4.0(Firefox)
#   &v=2
#   &format=json


def get_technology_tags():
    '''
        This function will get a list of popular tags from the 
        StackExchange/StackOverflow API. They will be compared to the most 
        common words found in the job summaries in order to find the most 
        popular technologies for that specific job search. Those technologies 
        will be included in the final report for the user.
    '''
    # Get tags from StackExchange/StackOverflow.
    pass
    # Parse the API response.
    pass
    # Add the tags to a (very long) list and return it.
    pass


def analyze_most_common_words(job_summary):
    '''
        This function will read the job summary/description and analyze which 
        are the most common words. It will return a dictionary in the form of 
        { word:count, word2:count2, ... }
    '''
    # Remove punctuation and stopwords.
    punctuation = list(string.punctuation)
    stopwords = nltk.corpus.stopwords.words("english")
    useless_words = stopwords + punctuation

    # Divide the job summary into a list of words.
    words = []
    words = job_summary.split(" ")

    # Remove useless words (good_words = words - useless words).
    good_words = [word for word in words if word not in useless_words]

    print "10 most common words in job summary:"
    common_words = Counter(good_words).most_common(10)
    print common_words
    return common_words


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


class _Settings():
    '''
        This class is used to store the settings parsed from the config.json 
        file.
        To get the values, you need to create an instance of this class:
        and then do whatever you want with that value, like:
        "print new_setting_instance.publisher_ID"

        To set the values (which should only happen once during the execution 
        of the program) you have to call this class with all the parameters.
        E.g.
        _Settings(<API_URL>, <publisher_ID>, <output_format>, <limit>, 
            <from_age>, <highlight>, <sort>, <radius>, <site_type>, <job_type>, 
            <start>, <duplicate_filter>, <lat_long>, <channel>, <user_IP>, 
            <user_agent>, <version>, <headers>)
    '''
    @property
    def API_URL(self): return self._API_URL
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
    @property
    def headers(self): return self._headers
    def __init__(self, API_URL, publisher_ID, output_format, limit, from_age, 
        highlight, sort, radius, site_type, job_type, start, duplicate_filter,
        lat_long, channel, user_IP, user_agent, version, headers):
        self._API_URL = API_URL
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
        self._headers = headers


def read_config():
    '''
        This function will read the configuration values from config.json
        and assign the values to a "_Settings" object.
        It will return that object, so you can do something like:
        parsed_settings = read_config()
    '''
    try:
        config = json.load(open(config_file, "r+"))

        request_config = config["request"]

        API_URL = request_config["API_URL"]
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
        headers = request_config["headers"]

        # Assign values to the _Settings class.
        settings = _Settings(API_URL, publisher_ID, output_format, limit, 
            from_age, highlight, sort, radius, site_type, job_type, start, 
            duplicate_filter, lat_long, channel, user_IP, user_agent, version,
            headers)
    except Exception as exception:
        log.error("Cannot read configuration file. {0}".format(exception))
        sys.exit(1)
    else:
        return settings


def get_job_summary(url):
    '''
        This function will access the URL from each job result in the 
        api_response, and get the contents of the "job_summary" object 
        in the DOM (i.e. the actual, long description text of the job).
    ''' 
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text,"html5lib")
        # Only 1 job summary per page, so we can use find instead of findAll
        job_summary = soup.find("span", attrs={"id" : "job_summary"})
    except Exception as error:
        log.error("Unable to get response from URL: {0} {1}".format(url, error))
    else:
        return job_summary.text


def main(query, country_code, location):
    '''
        Main driver for the program logic.
    '''
    # Arguments for the API call,
    # (refer to https://ads.indeed.com/jobroll/xmlfeed)

    # Create an instance of the "Settings" class in order to access the values.
    parsed_settings = read_config()

    # Concatenate the provided values to form the request URL.
    indeed_url = []
    indeed_url.append(parsed_settings.API_URL)
    indeed_url.append("publisher=" + parsed_settings.publisher_ID)
    indeed_url.append("&q=" + query)
    if location != None:
        indeed_url.append("&l=" + location)
    indeed_url.append("&sort=" + parsed_settings.sort)
    indeed_url.append("&radius=" + parsed_settings.radius)
    indeed_url.append("&st=" + parsed_settings.site_type)
    indeed_url.append("&jt=" + parsed_settings.job_type)
    indeed_url.append("&start=" + parsed_settings.start)
    indeed_url.append("&limit=" + parsed_settings.limit)
    indeed_url.append("&fromage=" + parsed_settings.from_age)
    indeed_url.append("&highlight=" + parsed_settings.highlight)
    indeed_url.append("&filter=" + parsed_settings.duplicate_filter)
    indeed_url.append("&latlong=" + parsed_settings.lat_long)
    indeed_url.append("&co=" + country_code)
    indeed_url.append("&chnl=" + parsed_settings.channel)
    indeed_url.append("&userip=" + parsed_settings.user_IP)
    indeed_url.append("&useragent=" + parsed_settings.user_agent)
    indeed_url.append("&v=" + parsed_settings.version)
    indeed_url.append("&format=" + parsed_settings.output_format)

    # Join everything to form a full URL.
    full_indeed_url = "".join(indeed_url)

    try:
        api_response = requests.get(full_indeed_url)
    except Exception as exception:
        log.error("Unable to get response from API: {0}".format(exception))
        sys.exit(1)

    # The status code should be 200 (success). Catch anything else and handle.
    if api_response.status_code != 200:
        log.error("The response status is: {0}".format(response.status_code))
        sys.exit(1)

    # Validate that we got a non-empty result set.
    try:
        readable_api_response = api_response.json()
    except ValueError as exception:
        log.warning("Empty result set. Request URL: {0}\nException: "\
            "{1}".format(full_indeed_url, exception))
        sys.exit(2)

    # Validate that there were job openings returned.
    if readable_api_response["totalResults"] == 0:
        log.warning("No results found for query: '{0}':".format(query))
        sys.exit(3)
    else:
        api_results = readable_api_response["results"]

    email_message = []
    
    # Parse the response from the Indeed.com API.
    for job in api_results:
        job_title = job["jobtitle"]
        # Call the get_job_summary() function.
        job_summary = get_job_summary(job["url"])
        # Analyze the job posting text.
        common_words = analyze_most_common_words(job_summary)

        # Once we found the most commond words, build an email message with 
        # all the Job posting data.
        email_subject = "Job found for '{0}'".format(query)
        email_message.append("The most common words for this job are: "\
            "\n{0}".format("\n".join(str(p) for p in common_words)))
        email_message.append("Job title:\n" + job_title + "\n")
        email_message.append("Job summary:\n" + job_summary + "\n")
    str_email_message = "\n".join(email_message)

    # Call the emailer.build function 
    # (which will subsequently send the email)
    emailer.build_email("jobcrawler", email_subject, 
        "jobcrawler@kippel.net", str_email_message, None)


if __name__ == "__main__":
    get_args(sys.argv[1:])

