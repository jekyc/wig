#!/usr/bin/env python3

import json, pprint, os, time, queue, sys
import argparse
from collections import defaultdict, Counter

from classes.color import Color
from classes.cache import Cache
from classes.results import Results
from classes.fingerprints import Fingerprints

from classes.discovery import *

from classes.headers import ExtractHeaders
from classes.matcher import Match
from classes.printer import Printer
from classes.output import OutputPrinter, OutputJSON
from classes.request2 import Requester, UnknownHostName



class Wig(object):

	def __init__(self, args):

		urls = None
		interactive = True
		
		if args.input_file is not None:
			interactive = False

			with open(args.input_file,'r') as input_file:
				urls = []
				for url in input_file.readlines():
					u = url.strip()
					urls.append( u if '://' in u else 'http://'+u )

		elif '://' not in args.url:
			args.url = 'http://' + args.url


		self.options = {
			'url': args.url,
			'urls': urls,
			'interactive': interactive,
			'prefix': '',
			'user_agent': args.user_agent,
			'proxy': args.proxy,
			'verbosity': args.verbosity,
			'threads': 10,
			'batch_size': 20,
			'run_all': args.run_all,
			'match_all': args.match_all,
			'stop_after': args.stop_after,
			'no_cache_load': args.no_cache_load,
			'no_cache_save': args.no_cache_save,
			'write_file': args.output_file
		}

		self.data = {
			'cache': Cache(),
			'results': Results(self.options),
			'fingerprints': Fingerprints(),
			'matcher': Match(),
			'colorizer': Color(),
			'printer': Printer(args.verbosity, Color()),
			'detected_cms': set(),
			'error_pages': set(),
			'requested': queue.Queue()
		}

		
		if self.options['write_file'] is not None:
			self.json_outputter = OutputJSON(self.options, self.data)
	


	def scan_site(self):
		
		self.data['results'].printer = self.data['printer']
		self.data['requester'] = Requester(self.options, self.data)

		
		""" --- DETECT REDIRECTION ------------- """
		try:
			is_redirected, new_url = self.data['requester'].detect_redirect()
		except UnknownHostName as e:
			error = self.data['colorizer'].format(e, 'red', False)
			print(error)

			# fix for issue 8: https://github.com/jekyc/wig/issues/8
			# Terminate gracefully if the url is not 
			# resolvable
			if self.options['write_file'] is not None:
				self.json_outputter.add_error(str(e))
			
			return

		if is_redirected:
			hilight_host = self.data['colorizer'].format(new_url, 'red', False)
			
			if self.options['interactive']:
				choice = input("Redirected to %s. Continue? [Y|n]:" % (hilight_host,))
			else:
				choice = 'Y'

			# if not, exit
			if choice in ['n', 'N']:
				sys.exit(1)
			# else update the host
			else:
				self.options['url'] = new_url
				self.data['requester'].url = new_url
		""" ------------------------------------ """

		msg = 'Scanning %s...' % (self.options['url'])
		print(self.data['colorizer'].format(msg, 'green', True))

		
		# load cache if this is not disabled
		self.data['cache'].set_host(self.options['url'])
		if not self.options['no_cache_load']:
			self.data['cache'].load()


		# timer started after the user interaction
		self.data['timer'] = time.time()


		""" --- GET SITE INFO ------------------ """
		# get the title
		title = DiscoverTitle(self.options, self.data).run()
		self.data['results'].site_info['title'] = title

		# get the IP of the domain
		ip = DiscoverIP(self.options['url']).run()
		self.data['results'].site_info['ip'] = ip
		""" ------------------------------------ """



		""" --- DETECT ERROR PAGES ------------- """
		# find error pages
		self.data['error_pages'] = DiscoverErrorPage(self.options, self.data).run()

		# set matcher error pages
		self.data['matcher'].error_pages = self.data['error_pages']
		""" ------------------------------------ """


		""" --- VERSION DETECTION -------------- """
		# Search for the first CMS
		cms_finder = DiscoverCMS(self.options, self.data).run()

		# find Platform
		platform_finder = DiscoverPlatform(self.options, self.data).run()
		""" ------------------------------------ """


		""" --- GET MORE DATA FROM THE SITE ---- """
		# find interesting files
		DiscoverInteresting(self.options, self.data).run()

		# find and request links to static files on the pages		
		DiscoverMore(self.options, self.data).run()
		""" ------------------------------------ """


		""" --- SEARCH FOR JAVASCRIPT LIBS ----- """
		# do this after 'DiscoverMore' has been run, to detect JS libs
		# located in places not covered by the fingerprints
		DiscoverJavaScript(self.options, self.data).run()
		""" ------------------------------------ """


		""" --- SEARCH THE CACHE --------------- """
		# some fingerprints do not have urls - search the cache
		# for matches
		DiscoverUrlLess(self.options, self.data).run()

		# search for cookies
		DiscoverCookies(self.data).run()

		# search the cache for headers
		ExtractHeaders(self.data).run()

		# search for indications of the used operating system
		DiscoverOS(self.options, self.data).run()

		# search for all CMS if specified by the user
		if self.options['match_all']:
			DiscoverAllCMS(self.data).run()
		""" ------------------------------------ """


		# mark the end of the run
		self.data['results'].update()
	

		""" --- SEARCH FOR VULNERABILITIES ----- """
		# search the vulnerability fingerprints for matches
		DiscoverVulnerabilities(self.data).run()
		""" ------------------------------------ """


		""" --- SAVE THE CACHE ----------------- """
		if not self.options['no_cache_save']:
			self.data['cache'].save()
		""" ------------------------------------ """
	

		""" --- PRINT RESULTS ------------------ """
		# calc an set run time
		self.data['runtime'] = time.time() - self.data['timer']

		# update the URL count 
		self.data['url_count'] = self.data['cache'].get_num_urls()

		# Create outputter and get results
		if self.options['write_file'] is not None:
			self.json_outputter.add_results()

		outputter = OutputPrinter(self.options, self.data)
		title, data = outputter.get_results()


		# quick, ugly hack for issue 5 (https://github.com/jekyc/wig/issues/5) 
		try:
			# this will fail, if the title contains unprintable chars
			print(title)
		except:
			pass

		print(data)
		""" ------------------------------------ """


	def reset(self):
		self.data['results'] = Results(self.options)
		self.data['cache'] = Cache()

	def run(self):
		
		if self.options['urls'] is not None:
			for url in self.options['urls']:
				self.reset()
				self.options['url'] = url.strip()
				self.scan_site()

		else:
			self.scan_site()

		
		if self.options['write_file'] is not None:
			self.json_outputter.write_file()



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='WebApp Information Gatherer')
	

	parser.add_argument('url', nargs='?', type=str, default=None,
						help='The url to scan e.g. http://example.com')
	
	parser.add_argument('-l', type=str, default=None, dest="input_file",
						help='File with urls, one per line.')
	
	parser.add_argument('-n', type=int, default=1, dest="stop_after",
						help='Stop after this amount of CMSs have been detected. Default: 1')
	
	parser.add_argument('-a', action='store_true', dest='run_all', default=False,
						help='Do not stop after the first CMS is detected')

	parser.add_argument('-m', action='store_true', dest='match_all', default=False,
						help='Try harder to find a match without making more requests')

	parser.add_argument('-u', action='store_true', dest='user_agent', 
						default='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
						help='User-agent to use in the requests')	

	parser.add_argument('--no_cache_load', action='store_true', default=False,
						help='Do not load cached responses')

	parser.add_argument('--no_cache_save', action='store_true', default=False,
						help='Do not save the cache for later use')

	parser.add_argument('-N', action='store_true', dest='no_cache', default=False,
						help='Shortcut for --no_cache_load and --no_cache_save')

	parser.add_argument('--verbosity', '-v', action='count', default=0,
						help='Increase verbosity. Use multiple times for more info')

	parser.add_argument('--proxy', dest='proxy', default=None, 
						help='Tunnel through a proxy (format: localhost:8080)')

	parser.add_argument('-w', dest='output_file', default=None, 
						help='File to dump results into (JSON)')

	args = parser.parse_args()

	
	if args.input_file is None and args.url is None:
		print('No target(s) specified')
		sys.exit(1)

	if args.no_cache:
		args.no_cache_load = True
		args.no_cache_save = True

	try:
		title = """
dP   dP   dP    dP     .88888.  
88   88   88    88    d8'   `88 
88  .8P  .8P    88    88        
88  d8'  d8'    88    88   YP88 
88.d8P8.d8P     88    Y8.   .88 
8888' Y88'      dP     `88888'  

  WebApp Information Gatherer
"""
		print(title)
		wig = Wig(args)
		wig.run()
	except KeyboardInterrupt:
		# detect ctrl+c
		for w in wig.workers:
			w.kill = True
		raise
