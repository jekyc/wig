import json, pprint, os, time, queue, sys
from collections import defaultdict, Counter
from classes.cache import Cache
from classes.results import Results
from classes.requester import Requester
from classes.fingerprints import Fingerprints
from classes.discovery import DiscoverCMS, DiscoverVersion, DiscoverOS
from classes.headers import ExtractHeaders

"""
TODO:
	- save cache for future use 
	- implement log
	- improve ordering of fingerprints in discovery list
	- implement os detection
	- implement command line arguments
		- use/save cache
		- use crawler
		- stop after first 'hit'
	- implement crawler
	- detection of error pages

	- Nice to have:
		- dirbuster-ish 
		- tree structure
"""


class Wig(object):

	def __init__(self):
		t = time.time()

		self.cache = Cache()					# cache for requests
		self.results = Results()				# storage of results
		self.threads = 10						# number of threads to run
		self.fingerprints = Fingerprints()		# load fingerprints

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
		print("Init time: %s" % (time.time() - t))


	def run(self):
		t = time.time()

		host = "http://www.sbstv.dk/"

		fps = self.fingerprints
		num_fps = fps.get_size()

		cms_finder = DiscoverCMS(self.ordered_list, self.cache, self.chuck_size)
		version_finder = DiscoverVersion(self.results, self.cache, self.chuck_size)


		# as long as there are more fingerprints to check, and
		# no cms' have been detected
		# 										currently stops after the first 
		# 										cms match
		while not cms_finder.is_done() and len(self.detected_cms) == 0:
			
			# check the next chunk of urls for cms detection 
			cms_list = cms_finder.run(host, self.detected_cms)
			for cms in cms_list:
				version_finder.run(host, fps.get_fingerprints_for_cms(cms))
				# if a match was found, then it has been added to the results object
				# and the detected_cms list should be updated 
				if self.results.found_match(cms):
					self.detected_cms.append(cms)


		# check for headers
		header_finder = ExtractHeaders(self.cache, self.results)
		header_finder.run()

		# find Operating system
		os_finder = DiscoverOS(self.cache, self.results, self.fingerprints.get_os_fingerprints())
		os_finder.run()


		run_time = "%.1f" % (time.time() - t)
		num_urls = self.cache.get_num_urls()

		status = "Time: %s sec | Urls: %s | Fingerprints: %s" % (run_time, num_urls, num_fps)
		bar = "_"*len(status)
		self.results.set_width(len(status))


		print(self.results)
		print(bar)
		print(status + "\n")



w = Wig()
w.run()

























