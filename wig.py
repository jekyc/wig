import json, pprint, os, time, queue, sys
import argparse
from collections import defaultdict, Counter
from classes.color import Color

try:
	import requests
except:
	c = Color()
	warning = c.format("The python library 'requests' is missing", 'red', True)

	print(warning)
	print("Installation methods:")
	print("  Debian/Kali:   apt-get install python3-requests")
	print("  pip:           pip3 install requests")
	print()
	sys.exit(1)

from classes.cache import Cache
from classes.results import Results
from classes.requester import Requester
from classes.fingerprints import Fingerprints
from classes.discovery import DiscoverCMS, DiscoverVersion
from classes.discovery import DiscoverOS, DiscoverJavaScript, DiscoverAllCMS
from classes.discovery import DiscoverRedirect, DiscoverErrorPage, DiscoverMore
from classes.headers import ExtractHeaders
from classes.matcher import Match
from classes.printer import Printer
from classes.output import Output




class Wig(object):

	def __init__(self, host, verbosity, stop_after=1, run_all=False, match_all=False, no_load_cache=False, no_save_cache=False):
		self.verbosity = verbosity
		self.colorizer = Color()
		self.printer = Printer(verbosity, self.colorizer)

		self.cache = Cache()					# cache for requests
		self.results = Results()				# storage of results
		self.threads = 10						# number of threads to run
		
		self.printer.print('Loading fingerprints... ', 1, '')
		self.fingerprints = Fingerprints()		# load fingerprints
		self.printer.print(' Done', 1)

		self.host = host
		self.run_all = run_all
		self.match_all = match_all
		self.stop_after = stop_after
		self.useragent = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'

		self.no_cache_load = no_load_cache
		self.no_cache_save = no_save_cache

		# set the amount of urls to fetch in parallel to the
		# amount of threads
		self.chuck_size = self.threads

		# get an ordered list of fingerprints
		# the list is ordered such that a breadth first search is performed
		self.ordered_list = self.fingerprints.get_ordered_list()

		# a list containing the cms' detected so far
		# this is used to skip detection for a CMS that has alreay been
		# through version discovery
		self.detected_cms = set()

		# a set of md5sums for error pages
		self.error_pages = set()

	def run(self):
		fps = self.fingerprints
		num_fps = fps.get_size()
		printer = self.printer

		########################################################################
		# PRE PROCESSING
		########################################################################

		# check if the input URL redirects to somewhere else
		dr = DiscoverRedirect(self.host, self.useragent)

		# make sure that the input is valid
		if dr.get_valid_url() is None:
			printer.print('Invalid host name')
			sys.exit(1)

		# if the hosts redirects, ask user if the redirection should be followed
		elif dr.is_redirected():
			hilight_host = self.colorizer.format(dr.get_valid_url(), 'red', False)
			choice = input("Redirected to %s. Continue? [Y|n]:" % (hilight_host,))

			# if not, exit
			if choice in ['n', 'N']:
				sys.exit(1)
			# else update the host
			else:
				self.host = dr.get_valid_url()

		# timer started after the user interaction
		t = time.time()

		# load cache if this is not disabled
		self.cache.set_host(self.host)
		if not self.no_cache_load:
			printer.print('Loading results from cache...', 1, '')
			self.cache.load()
			printer.print(' Done.', 1)

		# set a requester instance to use for all the requests
		requester = Requester(self.host, self.cache)
		requester.set_find_404(True)
		requester.set_useragent(self.useragent)

		# find error pages
		printer.print('Detecting error pages...', 1, '')
		find_error = DiscoverErrorPage(requester, self.host, self.fingerprints.get_error_urls())
		find_error.run()
		error_pages = find_error.get_error_pages()
		printer.print(' (Found %s error page(s))' % len(error_pages),2, '')
		printer.print(' Done', 1)


		# set the requester to not find 404s
		requester.set_find_404(False)

		# create a matcher
		matcher = Match()
		matcher.set_404s(error_pages)

		########################################################################
		# PROCESSING
		########################################################################
		cms_finder = DiscoverCMS(requester, matcher, self.ordered_list, self.chuck_size)
		version_finder = DiscoverVersion(requester, matcher, self.results, self.chuck_size)

		# as long as there are more fingerprints to check, and
		# no cms' have been detected
		printer.print('Beginning CMS detection...', 1)
		counter = 0
		while not cms_finder.is_done() and (len(self.detected_cms) < self.stop_after or self.run_all):
			printer.print('Requests: %s' % (counter * self.threads,), 1, '                                                \r')
			counter += 1

			# check the next chunk of urls for cms detection
			cms_list = list(set(cms_finder.run(self.host, self.detected_cms)))
			for cms in cms_list:

				# skip checking the cms, if it has already been detected
				if cms in self.detected_cms: continue

				printer.print(' Found %s. Running version detection...' % cms, 1, '')
				version_finder.run(self.host, fps.get_fingerprints_for_cms(cms))

				# if a match was found, then it has been added to the results object
				# and the detected_cms list should be updated
				if self.results.found_match(cms):
					printer.print(' Found something!', 2, '')
					self.detected_cms.add(cms)
				else:
					printer.print(' Found nothing.', 2, '')

				printer.print(' Done', 1)

		# iterate over the results stored in the cache and check all the
		# fingerprints against all of the responses, as the URLs
		# for the fingerprints are no longer valid
		printer.print('Fetching extra ressources...', 1, '')
		cache_items = self.cache.get_num_urls()

		fps = self.fingerprints.get_all()
		crawler = DiscoverMore(self.host, requester, self.cache, fps, matcher, self.results)
		crawler.run()

		new_items = self.cache.get_num_urls() - cache_items
		printer.print(' (Found %s new items)' %  new_items, 2, '')
		printer.print(' Done', 1)

		########################################################################
		# POST PROCESSING
		########################################################################

		# check for headers
		printer.print('Checking for headers...', 1, '')
		header_finder = ExtractHeaders(self.cache, self.results)
		header_finder.run()
		printer.print(' Done', 1)

		# detect JavaScript libraries
		printer.print('Checking for JavaScript...', 1, '')
		js_fps = self.fingerprints.get_js_fingerprints()
		js = DiscoverJavaScript(self.cache, js_fps, matcher, self.results)
		js.run()
		printer.print(' Done', 1)

		# match all fingerprints against all responses ?
		# this might produce false positives
		if self.match_all:
			printer.print('Running desparate mode - checking for all matches...', 1, '')			
			desparate = DiscoverAllCMS(self.cache, fps, matcher, self.results)
			desparate.run()
			printer.print(' Done', 1)

		# find Operating system
		printer.print('Checking for operating system...', 1, '')		
		os_finder = DiscoverOS(self.cache, self.results, self.fingerprints.get_os_fingerprints())
		os_finder.run()
		printer.print(' Done', 1)


		# save the cache
		if not self.no_cache_save:
			printer.print('Saving cache...', 1, '')
			self.cache.save()
			printer.print(' Done', 1)

		########################################################################
		# RESULT PRINTING
		########################################################################
		runtime = time.time() - t
		num_urls = self.cache.get_num_urls()

		o = Output(self.results.get_results(), runtime, num_urls, num_fps)
		print(o.get_results())



		
		# urls_200 = [ r.url for r in self.cache.get_responses() if r.status_code == 200 ]
		# urls_200.sort()
		# for u in urls_200: print(u)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='WebApp Information Gatherer')
	parser.add_argument('host', type=str, help='The host name of the target')
	
	parser.add_argument('-n', type=int, default=1, dest="stop_after",
						help='Stop after this amount of CMSs have been detected. Default: 1')
	
	parser.add_argument('-a', action='store_true', dest='run_all', default=False,
						help='Do not stop after the first CMS is detected')

	parser.add_argument('-m', action='store_true', dest='match_all', default=False,
						help='Try harder to find a match without making more requests')
	
	parser.add_argument('--no_cache_load', action='store_true', default=False,
						help='Do not load cached responses')

	parser.add_argument('--no_cache_save', action='store_true', default=False,
						help='Do not save the cache for later use')

	parser.add_argument('-N', action='store_true', dest='no_cache', default=False,
						help='Shortcut for --no_cache_load and --no_cache_save')

	parser.add_argument('--verbosity', '-v', action='count', help='Increase verbosity. Use twice for even more info')

	parser.add_argument('-e',   action='store_true', dest='enumerate', default=False,
						help='Use the built-in list of common files and directories (much like dirbuster). NOT IMPLEMENTED YET')


	args = parser.parse_args()

	if args.no_cache:
		args.no_cache_load = True
		args.no_cache_save = True

	if args.verbosity is None:
		verbosity = 0
	else:
		verbosity = args.verbosity


	try:
		wig = Wig(args.host, verbosity, args.stop_after, args.run_all, args.match_all, args.no_cache_load, args.no_cache_save)
		wig.run()
	except KeyboardInterrupt:
		# detect ctrl+c
		for w in wig.workers:
			w.kill = True
		raise

























