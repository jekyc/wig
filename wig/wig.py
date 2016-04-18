#!/usr/bin/env python3
"""
wig - WebApp Information Gatherer

https://github.com/jekyc/wig

wig is a web application information gathering tool, which
can identify numerous Content Management Systems and other
administrative applications.

The application fingerprinting is based on checksums and
string matching of known files for different versions of
CMSes. This results in a score being calculated for each
detected CMS and its versions. Each detected CMS is
displayed along with the most probable version(s) of it.
The score calculation is based on weights and the amount of
"hits" for a given checksum.

wig also tries to guess the operating system on the server
based on the 'server' and 'x-powered-by' headers. A
database containing known header values for different
operating systems is included in wig, which allows wig to
guess Microsoft Windows versions and Linux distribution
and version.

"""


import time, queue, sys
from wig.classes.cache import Cache
from wig.classes.results import Results
from wig.classes.fingerprints import Fingerprints
from wig.classes.discovery import *
from wig.classes.matcher import Match
from wig.classes.printer import Printer
from wig.classes.output import OutputPrinter, OutputJSON
from wig.classes.request2 import Requester, UnknownHostName



class Wig(object):
	def __init__(self, args):
		urls = None
		if args.input_file is not None:
			args.quiet = True

			with open(args.input_file, 'r') as input_file:
				urls = []
				for url in input_file.readlines():
					url = url.strip()
					urls.append(url if '://' in url else 'http://'+url)

		else:
			args.url = args.url.lower()
			if '://' not in args.url:
				args.url = 'http://' + args.url

		text_printer = Printer(args.verbosity)
		cache = Cache()
		cache.printer = text_printer

		self.options = {
			'url': args.url,
			'urls': urls,
			'quiet': args.quiet,
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
			'write_file': args.output_file,
			'subdomains': args.subdomains
		}

		self.data = {
			'cache': cache,
			'results': Results(self.options),
			'fingerprints': Fingerprints(),
			'matcher': Match(),
			'printer': text_printer,
			'detected_cms': set(),
			'error_pages': set(),
			'requested': queue.Queue()
		}

		if self.options['write_file'] is not None:
			self.json_outputter = OutputJSON(self.options, self.data)

		self.data['printer'].print_logo()

		self.results = None

	def scan_site(self):
		self.data['results'].printer = self.data['printer']
		self.data['requester'] = Requester(self.options, self.data)

		#
		# --- DETECT REDIRECTION ----------------
		#
		try:
			is_redirected, new_url = self.data['requester'].detect_redirect()
		except UnknownHostName as err:
			self.data['printer'].print_debug_line(err, 1)

			# fix for issue 8: https://github.com/jekyc/wig/issues/8
			# Terminate gracefully if the url is not
			# resolvable
			if self.options['write_file'] is not None:
				self.json_outputter.add_error(str(err))

			return

		if is_redirected:
			if not self.options['quiet']:
				self.data['printer'].build_line("Redirected to ")
				self.data['printer'].build_line(new_url, color='red')
				self.data['printer'].print_built_line()
				choice = input("Continue? [Y|n]:")
			else:
				choice = 'Y'

			# if not, exit
			if choice in ['n', 'N']:
				sys.exit(1)
			# else update the host
			else:
				self.options['url'] = new_url
				self.data['requester'].url = new_url


		#
		# --- PREP ------------------------------
		#
		msg = 'Scanning %s...' % (self.options['url'])
		self.data['printer'].print_debug_line(msg, 0, bold=True)

		# load cache if this is not disabled
		self.data['cache'].set_host(self.options['url'])
		if not self.options['no_cache_load']:
			self.data['cache'].load()

		# timer started after the user interaction
		self.data['timer'] = time.time()


		#
		# --- GET SITE INFO ---------------------
		#
		# get the title
		title = DiscoverTitle(self.options, self.data).run()
		self.data['results'].site_info['title'] = title

		# get the IP of the domain
		# issue 19: changed DiscoverIP to return a list of IPs
		self.data['results'].site_info['ip'] = DiscoverIP(self.options['url']).run()


		#
		# --- DETECT ERROR PAGES ----------------
		#
		# find error pages
		self.data['error_pages'] = DiscoverErrorPage(self.options, self.data).run()

		# set matcher error pages
		self.data['matcher'].error_pages = self.data['error_pages']


		#
		# --- VERSION DETECTION -----------------
		#
		# Search for the first CMS
		DiscoverCMS(self.options, self.data).run()

		# find Platform
		DiscoverPlatform(self.options, self.data).run()

		#
		# --- GET MORE DATA FROM THE SITE -------
		#
		# find interesting files
		DiscoverInteresting(self.options, self.data).run()

		# find and request links to static files on the pages
		DiscoverMore(self.options, self.data).run()


		#
		# --- SEARCH FOR JAVASCRIPT LIBS --------
		#
		# do this after 'DiscoverMore' has been run, to detect JS libs
		# located in places not covered by the fingerprints
		DiscoverJavaScript(self.options, self.data).run()


		#
		# --- SEARCH THE CACHE ------------------
		#
		# some fingerprints do not have urls - search the cache
		# for matches
		DiscoverUrlLess(self.options, self.data).run()

		# search for cookies
		DiscoverCookies(self.data).run()

		# search for indications of the used operating system
		DiscoverOS(self.options, self.data).run()

		# search for all CMS if specified by the user
		if self.options['match_all']:
			DiscoverAllCMS(self.data).run()

		#
		# --- SEARCH FOR SUBDOMAINS --------
		#
		if self.options['subdomains']:
			DiscoverSubdomains(self.options, self.data).run()

		# mark the end of the run
		self.data['results'].update()

		#
		# --- SEARCH FOR TOOLS --------
		#
		DiscoverTools(self.data).run()

		#
		# --- SEARCH FOR VULNERABILITIES --------
		#
		# search the vulnerability fingerprints for matches
		DiscoverVulnerabilities(self.data).run()

		#
		# --- SAVE THE CACHE --------------------
		#
		if not self.options['no_cache_save']:
			self.data['cache'].save()

		#
		# --- PRINT RESULTS ---------------------
		#
		# calc an set run time
		self.data['runtime'] = time.time() - self.data['timer']

		# update the URL count
		self.data['url_count'] = self.data['cache'].get_num_urls()

		# Create outputter and get results
		if self.options['write_file'] is not None:
			self.json_outputter.add_results()

		outputter = OutputPrinter(self.options, self.data)
		outputter.print_results()


	def get_results(self):
		return self.data['results'].results


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


def wig(**kwargs):
	"""
		Use this to call wig from python:

		>>>> from wig import wig
		>>>> w = wig(url='example.com')
		>>>> w.run()
		>>>> results = w.get_results()
	"""

	# the url parameter must be supplied
	if 'url' not in kwargs:
		raise Exception('url parameter not supplied')
	args = parse_args(kwargs['url'])

	# set all other parameters supplied in the function call
	for setting in kwargs:
		if setting not in args:
			raise Exception('Unknown keyword supplied: %s' % (setting, ))
		setattr(args, setting, kwargs[setting])

	# need to be set in order to silence wig
	args.verbosity = -1
	args.quiet = True

	# return an instance of wig
	return Wig(args)