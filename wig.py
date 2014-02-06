#!/usr/bin/python

import sys, time, argparse, requests
import plugins
from plugins.classes.results import Results
from plugins.classes.cache import Cache
from plugins.classes.color import Color

class Wig():

	def __init__(self, host):
		self.plugins = self.load_plugins()
		self.host = host
		self.results = Results()
		self.cache = Cache()
		self.redirect()
		self.colorizer = Color()


	def redirect(self):
		r = requests.get(self.host)
		if not r.url == self.host:
			self.host = r.url


	def load_plugins(self):
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
		for plugin in self.plugins:
			ps = plugin.get_instances(self.host, self.cache, self.results)
			num_plugins += len(ps)
			for p in ps:
				print(p.name, end="                                                \r")
				sys.stdout.flush()
				p.run()
				num_fps += p.get_num_fps()

		run_time = "%.1f" % (time.time() - t)
		num_urls = self.cache.get_num_urls()

		print(self.results)
		status = "Time: %s sec | Plugins: %s | Urls: %s | Fingerprints: %s" % (run_time, num_plugins, num_urls, num_fps)
		print("_"*len(status))
		print(status + "\n")


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='WebApp Information Gatherer')
	parser.add_argument('host', type=str, help='the host name of the target')
	args = parser.parse_args()

	try:
		wig = Wig(args.host)
		if not wig.host == args.host:
			hilight_host = wig.colorizer.format(wig.host, 'red', False)
			choice = input("Redirected to %s. Continue? [Y|n]:" %(hilight_host,))
			if choice in ['n', 'N']:
				sys.exit(0)

		wig.run()
	except KeyboardInterrupt:
		for w in wig.workers:
			w.kill = True
		raise
