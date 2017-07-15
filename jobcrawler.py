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
    publisher_ID = "XXXXXXXXXXXXXXXXXXXXXXX"

    # "xml" or "json". If omitted or invalid, XML is used.
    output_format = "json"

    # TODO (Alan): Change the limit to something a lot larger than 10.
    # Max results returned per query. Default is 10 
    limit = "10"
    
    from_age = ""
    
    highlight = "false"
    
    sort = ""

    # Distance from search location ("as the crow flies"). Default is 25.
    radius = ""
    
    # Site type. To show only jobs from job boards use "jobsite". 
    # For jobs from direct employer websites use "employer".
    site_type = ""
    
    job_type = "fulltime"

    # Start results at this result number, beginning with 0. Default is 0.
    start = ""

    # Filter duplicate results. 0 turns off duplicate job filtering.
    # Default is 1.
    duplicate_filter = "1"

    lat_long = "1"

    channel = ""

    user_IP = "1.2.3.4"

    user_agent = "Mozilla/%2F4.0(Firefox)"

    version = "2"

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
