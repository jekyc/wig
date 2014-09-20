import json, pprint, os, time, queue, sys
import argparse, requests
from collections import defaultdict, Counter
from classes.color import Color
from classes.cache import Cache
from classes.results import Results
from classes.requester import Requester
from classes.fingerprints import Fingerprints
from classes.discovery import DiscoverCMS, DiscoverVersion, DiscoverOS
from classes.headers import ExtractHeaders

"""
TODO:
	- detection of error pages
	- implement log
	- improve ordering of fingerprints in discovery list
	- implement functions
		- crawler
		- don't stop after first 'hit'
		- dirbuster-ish 
	- implement crawler
	- implement tree structure view
"""


class Wig(object):

	def __init__(self, host):
		self.colorizer = Color()
		self.cache = Cache()					# cache for requests
		self.results = Results()				# storage of results
		self.threads = 10						# number of threads to run
		self.fingerprints = Fingerprints()		# load fingerprints
		self.host = host

		# set the amount of urls to fetch in parallel to the
		# amount of threads
		self.chuck_size = self.threads 


		# get an ordered list of fingerprints 
		# the list is ordered such that a breadth first search is performed
		self.ordered_list = self.fingerprints.get_ordered_list()

		# a list containing the cms' detected so far
		# this is used to skip detection for a CMS that has alreay been
		# through version discovery
		self.detected_cms = []

		# check if the input URL redirects to somewhere else
		self.check_url()
		self.redirect()


	def check_url(self):
		# adds http:// to input if not present
		if not self.host.startswith("http"):
			self.host = "http://" + self.host


	def redirect(self):
		# detects redirection if this happend
		try:
			r = requests.get(self.host, verify=False)
		except:
			print("Invalid URL or host not found. Exiting...")
			sys.exit(1)

		if not r.url == self.host:

			# ensure that folders and files are removed
			parts = r.url.split('//')
			http, url = parts[0:2]

			# remove subfolders and/or files
			# http://example.com/test -> http://example.com/
			if '/' in url:
				redirected = http + '//' + url.split('/')[0] + '/'
			else:
				redirected = http + '//' + url + '/'

			self.host = redirected


	def run(self):
		t = time.time()

		fps = self.fingerprints
		num_fps = fps.get_size()


		##########################################################################
		# PRE PROCESSING
		##########################################################################



		##########################################################################
		# PROCESSING
		##########################################################################
		cms_finder = DiscoverCMS(self.ordered_list, self.cache, self.chuck_size)
		version_finder = DiscoverVersion(self.results, self.cache, self.chuck_size)


		# as long as there are more fingerprints to check, and
		# no cms' have been detected
		# 										currently stops after the first 
		# 										cms match
		while not cms_finder.is_done() and len(self.detected_cms) == 0:
			
			# check the next chunk of urls for cms detection 
			cms_list = cms_finder.run(self.host, self.detected_cms)
			for cms in cms_list:
				version_finder.run(self.host, fps.get_fingerprints_for_cms(cms))
				# if a match was found, then it has been added to the results object
				# and the detected_cms list should be updated 
				if self.results.found_match(cms):
					self.detected_cms.append(cms)


		##########################################################################
		# POST PROCESSING
		##########################################################################

		# check for headers
		header_finder = ExtractHeaders(self.cache, self.results)
		header_finder.run()

		# find Operating system
		os_finder = DiscoverOS(self.cache, self.results, self.fingerprints.get_os_fingerprints())
		os_finder.run()


		##########################################################################
		# RESULT PRINTING
		##########################################################################
		run_time = "%.1f" % (time.time() - t)
		num_urls = self.cache.get_num_urls()

		status = "Time: %s sec | Urls: %s | Fingerprints: %s" % (run_time, num_urls, num_fps)
		bar = "_"*len(status)
		self.results.set_width(len(status))

		print(self.results)
		print(bar)
		print(status + "\n")



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='WebApp Information Gatherer')
	parser.add_argument('host', type=str, help='The host name of the target')
	
	parser.add_argument('-n', type=int, default=1,
		help='Stop after this amount of CMSs have been detected. Default: 1')
	
	parser.add_argument('-a', action='store_true', dest='run_all', default=False,	    
		help='Do not stop after the first CMS is detected')

	parser.add_argument('-c', action='store_true', dest='crawl', default=False,     
		help='Enable the crawler - include encountered static ressources (js,css,etc)')
	
	parser.add_argument('-e',   action='store_true', dest='enumerate', default=False,
		help='Use the built-in list of common files and directories (much like dirbuster)')

	#parser.add_argument('-v', action="store_const", dest="loglevel",  const=True, help="list all the urls where matches have been found")
	#parser.add_argument('-d', action="store_const", dest="desperate", const=True, help="Desperate mode - crawl pages fetched for additional ressource and try to match all fingerprints. ")


	args = parser.parse_args()

	try:
		wig = Wig(args.host)
		if not wig.host == args.host:
			hilight_host = wig.colorizer.format(wig.host, 'red', False)

			# if a redirection has been detected on the input host, notify the user
			choice = input("Redirected to %s. Continue? [Y|n]:" %(hilight_host,))
			if choice in ['n', 'N']:
				sys.exit(0)

		wig.run()
	except KeyboardInterrupt:
		# detect ctrl+c 
		for w in wig.workers:
			w.kill = True
		raise

























