import json, pprint, os, time, queue, sys
import argparse
from collections import defaultdict, Counter

from classes.color import Color
from classes.cache import Cache
from classes.results import Results
from classes.fingerprints import Fingerprints
from classes.discovery import DiscoverCMS, DiscoverVersion
from classes.discovery import DiscoverOS, DiscoverJavaScript, DiscoverAllCMS
from classes.discovery import DiscoverRedirect, DiscoverErrorPage, DiscoverMore
from classes.discovery import DiscoverInteresting, DiscoverUrlLess
from classes.headers import ExtractHeaders
from classes.matcher import Match
from classes.printer import Printer
from classes.output import Output
from classes.requester2 import Requester




class Wig(object):

	def __init__(self, host, verbosity, stop_after=1, run_all=False, match_all=False, no_load_cache=False, no_save_cache=False):
		c = Color()

		self.options = {
			'host': host,
			'verbosity': verbosity,
			'printer': Printer(verbosity, c),
			'threads': 10,
			'chunk_size': 10, # same as threads
			'run_all': run_all,
			'match_all': match_all,
			'stop_after': stop_after,
			'no_cache_load': no_load_cache,
			'no_cache_save': no_save_cache,
		}

		self.data = {
			'cache': Cache(),
			'results': Results(self.options),
			'fingerprints': Fingerprints(),
			'matcher': Match(),
			'colorizer': c,
			'detected_cms': set(),
			'error_pages': set()
		}

	def run(self):
		
		########################################################################
		# PRE PROCESSING
		########################################################################

		# check if the input URL redirects to somewhere else
		dr = DiscoverRedirect(self.options)

		# make sure that the input is valid
		if dr.get_valid_url() is None:
			sys.exit(1)

		# if the hosts redirects, ask user if the redirection should be followed
		elif dr.is_redirected():
			hilight_host = self.data['colorizer'].format(dr.get_valid_url(), 'red', False)
			choice = input("Redirected to %s. Continue? [Y|n]:" % (hilight_host,))

			# if not, exit
			if choice in ['n', 'N']:
				sys.exit(1)
			# else update the host
			else:
				self.options['host'] = dr.get_valid_url()

		# timer started after the user interaction
		self.data['timer'] = time.time()

		# load cache if this is not disabled
		self.data['cache'].set_host(self.options['host'])
		if not self.options['no_cache_load']:
			self.data['cache'].load()

		# set a requester instance to use for all the requests
		self.data['requester'] = Requester(self.options, self.data)

		# find error pages
		find_error = DiscoverErrorPage(self.options, self.data)
		find_error.run()
		self.data['error_pages'] = find_error.get_error_pages()

		# create a matcher
		self.data['matcher'].set_404s(self.data['error_pages'])

		########################################################################
		# PROCESSING
		########################################################################
		cms_finder = DiscoverCMS(self.options, self.data)
		version_finder = DiscoverVersion(self.options, self.data)
		p = self.options['printer']

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

		# find interesting files
		DiscoverInteresting(self.options, self.data). run()
		DiscoverMore(self.options, self.data).run()
		ExtractHeaders(self.data).run()
		DiscoverJavaScript(self.options, self.data).run()
		DiscoverUrlLess(self.options, self.data).run()
		
		if self.options['match_all']:
			DiscoverAllCMS(self.data).run()

		DiscoverOS(self.options, self.data).run()

		if not self.options['no_cache_save']:
			self.data['cache'].save()
	
		########################################################################
		# RESULT PRINTING
		########################################################################
		self.data['runtime'] = time.time() - self.data['timer']
		self.data['url_count'] = self.data['cache'].get_num_urls()

		o = Output(self.options, self.data)
		print(o.get_results())


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
