#!/usr/bin/python

import sys, time, argparse, requests
import plugins
from collections import defaultdict
from classes.results import Results
from classes.cache import Cache
from classes.color import Color
from classes.profile import Profile
from classes.log import Log
from classes.desperate import Desperate

class Wig():

	def __init__(self, host, profile, verbose, desperate):
		self.plugins = self.load_plugins()
		self.host = host
		self.results = Results()
		self.cache = Cache()
		self.profile = Profile(profile)
		self.check_url()
		self.redirect()
		self.colorizer = Color()
		self.logs = Log()
		self.verbose = verbose

		if desperate:
			self.desperate = Desperate()
		else:
			self.desperate = None


	def redirect(self):
		# detects redirection if this happend
		r = requests.get(self.host, verify=False)
		if not r.url == self.host:

			# ensure that sub-folders and files are removed
			parts = r.url.split('//')
			http, url = parts[0:2]

			# remove subfolders and/or files
			# http://example.com/test -> http://example.com/
			if '/' in url:
				redirected = http + '//' + url.split('/')[0] + '/'
			else:
				redirected = http + '//' + url + '/'

			self.host = redirected

	
	def check_url(self):
		# adds http:// to input if not present
		if not self.host.startswith("http"):
			self.host = "http://" + self.host


	def load_plugins(self):
		# load all the plugins listed in plugins/__init__.py
		all_plugins = []
		for p in plugins.__all__:
			plugin_path = "plugins." + p
			__import__(plugin_path)
			all_plugins.append(sys.modules[plugin_path])

		return all_plugins


	def run(self):
		t = time.time()
		num_fps = 0
		num_plugins = 0
		# loops over all the plugins loaded
		for plugin in self.plugins:

			# a loaded plugin might have more than one plugin, so 'ps' is a list
			ps = plugin.get_instances(self.host, self.cache, self.results)
			num_plugins += len(ps)
			for p in ps:

				# give a status of which plugin is run
				print(p.name, end="                                                \r")
				sys.stdout.flush()

				# applies the choosen profile by removing fingerprints from the 
				# fingerprint set if these do not match the choosen profile
				p.set_profile(self.profile)

				# the main plugin method
				p.run()
				num_fps += p.get_num_fps()

				# check if running desperate mode.
				if self.desperate:
					# add the plugins fingerprints to the global fingerprint database
					self.desperate.add_fingerprints(p.get_items_for_desperate_mode())

				# add logs
				self.logs.add( p.get_logs() )


		run_time = "%.1f" % (time.time() - t)
		num_urls = self.cache.get_num_urls()

		if self.desperate:
			self.desperate.set_cache(self.cache)
			self.desperate.run()
			for i in self.desperate.get_matches():
				self.results.add('Desperate', i['cms'], i, i['count'])


		status = "Time: %s sec | Plugins: %s | Urls: %s | Fingerprints: %s" % (run_time, num_plugins, num_urls, num_fps)
		bar = "_"*len(status)
		self.results.set_width(len(status))

		print(self.results)
		print(bar)
		print(status + "\n")

		if self.verbose:
			print(bar)
			print(self.logs)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='WebApp Information Gatherer')
	parser.add_argument('host', type=str,	help='the host name of the target')
	parser.add_argument('-v', action="store_const", dest="loglevel",  const=True, help="list all the urls where matches have been found")
	parser.add_argument('-d', action="store_const", dest="desperate", const=True, help="Desperate mode - this will try to match fingerprints across plugins. Can generate false positives")

	parser.add_argument('-p',
		type=int,
		default=4, 
		choices=[1,2,4],
		dest='profile',
		help='select a profile:  1) Make only one request  2) Make one request per plugin  4) All (default)')


	args = parser.parse_args()

	try:
		wig = Wig(args.host, args.profile, args.loglevel, args.desperate)
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
