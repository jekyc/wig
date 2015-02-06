import json, pprint, os, time, queue, sys
import argparse
from collections import defaultdict, Counter

from classes.color import Color
from classes.cache import Cache
from classes.results import Results
from classes.fingerprints import Fingerprints
from classes.discovery import DiscoverTitle, DiscoverIP, DiscoverCookies
from classes.discovery import DiscoverCMS, DiscoverVersion
from classes.discovery import DiscoverOS, DiscoverJavaScript, DiscoverAllCMS
from classes.discovery import DiscoverErrorPage, DiscoverMore
from classes.discovery import DiscoverInteresting, DiscoverUrlLess
from classes.discovery import DiscoverVulnerabilities, DiscoverTools
from classes.headers import ExtractHeaders
from classes.matcher import Match
from classes.printer import Printer
from classes.output import Output
from classes.request2 import Requester, UnknownHostName




class Wig(object):

	def __init__(self, args):

		self.options = {
			'url': args.url,
			'prefix': '',
			'user_agent': args.user_agent,
			'proxy': args.proxy,
			'verbosity': args.verbosity,
			'threads': 10,
			'chunk_size': 10, # same as threads
			'run_all': args.run_all,
			'match_all': args.match_all,
			'stop_after': args.stop_after,
			'no_cache_load': args.no_cache_load,
			'no_cache_save': args.no_cache_save,
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
			'queue': queue.Queue(),
			'requested': queue.Queue()
		}

		self.data['results'].set_printer(self.data['printer'])
		self.data['requester'] = Requester(self.options, self.data)

	def run(self):
		
		########################################################################
		# PRE PROCESSING
		########################################################################
		
		try:
			is_redirected, new_url = self.data['requester'].detect_redirect()
		except UnknownHostName as e:
			error = self.data['colorizer'].format(e, 'red', False)
			print(error)
			sys.exit(1)


		if is_redirected:
			hilight_host = self.data['colorizer'].format(new_url, 'red', False)
			choice = input("Redirected to %s. Continue? [Y|n]:" % (hilight_host,))

			# if not, exit
			if choice in ['n', 'N']:
				sys.exit(1)
			# else update the host
			else:
				self.options['url'] = new_url
				self.data['requester'].set_url(new_url)

		# timer started after the user interaction
		self.data['timer'] = time.time()

		# load cache if this is not disabled
		self.data['cache'].set_host(self.options['url'])
		if not self.options['no_cache_load']:
			self.data['cache'].load()

		# find error pages
		self.data['error_pages'] = DiscoverErrorPage(self.options, self.data).run()

		# create a matcher
		self.data['matcher'].set_404s(self.data['error_pages'])

		ip = DiscoverIP(self.options['url']).run()
		self.data['results'].set_ip(ip)

		########################################################################
		# PROCESSING
		########################################################################
		cms_finder = DiscoverCMS(self.options, self.data)
		version_finder = DiscoverVersion(self.options, self.data)
		p = self.data['printer']

		# as long as there are more fingerprints to check, and
		# no cms' have been detected
		counter = 0
		p.print('Running CMS detection...' ,1)
		while not cms_finder.is_done() and (len(self.data['detected_cms']) < self.options['stop_after'] or self.options['run_all']):
			counter += 1

			# check the next chunk of urls for cms detection
			cms_list = list(set(cms_finder.run()))
			for cms in cms_list:
				
				# skip checking the cms, if it has already been detected
				if cms in self.data['detected_cms']: continue

				p.print('- Running CMS version detection on %s' % (cms, ) ,2)
				version_finder.run(cms)

				# if a match was found, then it has been added to the results object
				# and the detected_cms list should be updated
				if self.data['results'].found_match(cms):
					self.data['detected_cms'].add(cms)
				else:
					pass

		########################################################################
		# POST PROCESSING
		########################################################################

		# set site into
		ip = DiscoverIP(self.options['url']).run()
		self.data['results'].set_ip(ip)
		title = DiscoverTitle(self.options, self.data).run()
		self.data['results'].set_title(title)

		# find interesting files
		DiscoverInteresting(self.options, self.data).run()
		DiscoverMore(self.options, self.data).run()
		ExtractHeaders(self.data).run()
		DiscoverJavaScript(self.options, self.data).run()
		DiscoverUrlLess(self.options, self.data).run()
		
		if self.options['match_all']:
			DiscoverAllCMS(self.data).run()

		DiscoverOS(self.options, self.data).run()

		cookies = DiscoverCookies(self.data).run()
		self.data['results'].set_cookies(cookies)

		DiscoverVulnerabilities(self.data).run()

		if not self.options['no_cache_save']:
			self.data['cache'].save()
	
		########################################################################
		# RESULT PRINTING
		########################################################################
		self.data['runtime'] = time.time() - self.data['timer']
		self.data['url_count'] = self.data['cache'].get_num_urls()

		outputter = Output(self.options, self.data)
		title, data = outputter.get_results()
		try:
			print(title)
		except:
			pass

		print(data)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='WebApp Information Gatherer')
	parser.add_argument('url', type=str, help='The url to scan e.g. http://example.com')
	
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


	args = parser.parse_args()

	if '://' not in args.url:
		args.url = 'http://' + args.url

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
