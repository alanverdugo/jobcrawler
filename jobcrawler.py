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
	Author:		Date:		Notes:
	Alan		2016-06-08	Added this header.
	Alan        2016-06-11	Separated everything into functions.
	Alan		2016-07-16	Added some error checking.
	Alan		2016-07-17	Improved style according to:
							https://google.github.io/styleguide/pyguide.html
	Alan		2016-07-20	Replaced getopt with argparse.
							Added the get_job_summary function.
	Alan		2016-07-24	Added os module for handling paths and files.
"""

import os

import sys

import json

import logging

# For the actual email sending.
import smtplib

# To get the API call results.
import requests

# To get arguments from CLI.
import argparse

# Some email modules we'll need.
from email.mime.text import MIMEText

from bs4 import BeautifulSoup


headers = {'content-type': 'application/json'}
home_dir = "/opt/jobcrawler/"
output_file = home_dir + "results.json"
# Variables for sending notification email.
# TODO: Change this to read from config.json
smtp_server = "localhost"  # The hostname of the SMTP server.
email_from = "JobCrawler@localhost"  # Sender address.
mail_list = home_dir + "mailList.txt"  # Dist. list, one address per line.
config_file = os.path.join(home_dir, "config.json")

# Simple search
# http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX&q=google&l=austin%2C+tx&sort=&radius=&st=&jt=&start=&limit=100&fromage=&filter=&latlong=1&co=us&chnl=&userip=1.2.3.4&useragent=Mozilla/%2F4.0(Firefox)&v=2&format=json

# All software engineer jobs from Google in the US
#http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX&q=software+engineer+company:google&l=&sort=&highlight=false&radius=&st=&jt=&start=&limit=100&fromage=&filter=&latlong=1&co=us&chnl=&userip=1.2.3.4&useragent=Mozilla/%2F4.0(Firefox)&v=2&format=json

# All software engineer jobs from Google in Japan
#http://api.indeed.com/ads/apisearch?publisher=XXXXXXXXXXXXXXXXXXXXXXX&q=software+engineer+company:google&l=&sort=&highlight=false&radius=&st=&jt=&start=&limit=100&fromage=&filter=&latlong=1&co=jp&chnl=&userip=1.2.3.4&useragent=Mozilla/%2F4.0(Firefox)&v=2&format=json


def send_email(results_message, originCity, destinationCity, saleTotal):
	# Send email with results.
	try:
		email_file = open(mail_list, "r+")
		email_to = email_file.readlines()
		email_file.close()  # Close file after reading the email recipients.
	except Exception as error:
		print "ERROR: Unable to open", mail_list, error
		sys.exit(1)
	# TODO (Alan): Use an HTML email instead of plain text.
	msg = MIMEText(results_message,"plain")
	# TODO (Alan): Change this subject.
	email_subject = "Flights found: "+originCity+" to "+destinationCity+", "+destinationCity+" to "+originCity+" for "+saleTotal+" or less."
	msg['Subject'] = email_subject
	try:
		s = smtplib.SMTP(smtp_server)
		s.sendmail(email_from, email_to, msg.as_string())
		s.quit()
	except Exception as error:
		print "ERROR: Unable to send email:", error
		sys.exit(1)


def get_args(argv):
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
		print "-----------------------------JOB SUMMARY:---------------------------------\n",job_summary.text
	except Exception as error:
		print "FATAL ERROR: Unable to get response from URL:", url, error


def save_result():
	'''
	This function will save new job results into the appropiate file/DB,
	and it will NOT save any duplicates.
	'''
	# TODO (Alan): Remove the next line so this function does something.
	sys.exit(0)
	# If there is not a directory for this <countryCode>_<query> combo, create one.
	results_dir = home_dir + country_code + query
	results_file = results_dir + "results.json"
	if not os.path.exists(results_dir):
		os.makedirs(results_dir)
	# If the results file does not exist, create it.
	if not os.path.exists(results_file):
		os.makedirs(results_file)
	# if the results file does exists, open it.
    # Open the results file so we can add new results.
	#try:
	#	results_file_handle = open(results_file, "r+")
	#	results_file_handle.close() # Close file. 
    #except Exception as exception:
	#	print "ERROR: Unable to open", str(resultsFile), exception
	#	sys.exit(1)
	# Make sure we are not inserting a duplicate into the results file.
	# Read all the jobkeys (Unique IDs) to avoid inserting duplicates.
	# Close the appropiate results file.


def main(query, country_code, location):
	# Arguments for the API call,
	# (refer to https://ads.indeed.com/jobroll/xmlfeed)
	# TODO: Read all this from a config file.
	publisher_ID = "XXXXXXXXXXXXXXXXXXXXXXX"
	output_format = "json"  # "xml" or "json". If omitted or invalid, XML is used.
	# TODO (Alan): Change the limit to something a lot larger than 10.
	limit = "10"  # Max results returned per query. Default is 10 
	from_age = ""
	highlight = "false"
	sort = ""
	radius = ""  # Distance from search location ("as the crow flies"). Default is 25.
	site_type = ""  # Site type. To show only jobs from job boards use "jobsite". For jobs from direct employer websites use "employer".
	job_type = "fulltime"
	start = ""  # Start results at this result number, beginning with 0. Default is 0.
	duplicate_filter = "1"  #Filter duplicate results. 0 turns off duplicate job filtering. Default is 1.
	# TODO: Read all this from a config file.
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
		print "FATAL ERROR: Unable to get response from API:", error
		sys.exit(1)

	# The status code should be 200 (success). Catch anything else and handle.
	if api_response.status_code != 200:
		print "FATAL ERROR: The response status is:", response.status_code
		sys.exit(1)

	# Validate that we got a non-empty result set.
	try:
		readable_api_response = api_response.json()
	except ValueError:
		print "WARNING: Empty result set. Request URL:", indeed_url 
		sys.exit(2)

	# Validate that there were job openings returned.
	try:
		api_results = readable_api_response["results"]
	except KeyError:
		print datetime.today(), ("WARNING: There were no results found. "
			"Request URL:", indeed_url)
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
