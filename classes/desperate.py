from queue import Queue
from classes.specializedMatchers import DesperateMatcher
from classes.requesterThread import RequesterThread
from classes.plugin import Plugin
from collections import Counter
from collections import defaultdict
from html.parser import HTMLParser


class Desperate(object):
	# Desperate mode 
	# search the cache for requests that match any of the fingerprints 
	# in the supplied MD5 database 'fingerprints' 
	def __init__(self):
		self.fingerprints = []
		self.matcher = DesperateMatcher
		self.matches = defaultdict(Counter)

	def add_fingerprints(self, fingerprints):
		self.fingerprints.extend(fingerprints)

	def set_cache(self, cache):
		self.cache = cache

	def crawl(self):
		ps = PageScraper(self.cache.host, self.cache)
		ps.run()

	def run(self):
		self.crawl()

		matcher = self.matcher(self.cache, self.fingerprints)
		for match in matcher.get_matches():
			version = match['output']
			cms = match['cms']
			self.matches[cms][version] += 1

	def get_matches(self):
		out = []
		for cms in self.matches:
			for version in self.matches[cms]:
				out.append( (self.matches[cms][version], cms, version) )

		out.sort()
		out.reverse()
		return [{'cms': i[1], 'version': i[2], 'count': i[0] } for i in out]




class LinkExtractor(HTMLParser):
	def __init__(self, strict):
		super().__init__(strict=strict)
		self.results = set()

	def get_results(self):
		return self.results

	def handle_starttag(self, tag, attrs):
		try:
			url = ''
			if tag == 'script' or tag == 'img':
				for attr in attrs: 
					if attr[0] == 'src':  self.results.add(attr[1])
			if tag == 'link':
				for attr in attrs: 
					if attr[0] == 'href': self.results.add(attr[1])
		except:
			pass


class PageScraper(Plugin):
	def __init__(self, host, cache):
		self.parser = LinkExtractor(strict=False)
		self.host = host
		self.cache = cache
		self.queue = Queue()
		self.results = Queue()
		self.threads = 4
		self.workers = []

	def run(self):
		for req in self.cache.get_responses():
			# skip pages that do not set 'content-type'
			# these might be binaries
			if not 'content-tupe' in req.headers:
				continue

			# only scrape pages that can contain links/references
			if 'text/html' in req.headers['content-type']:
				self.parser.feed(str(req.content))
				
				for i in self.parser.get_results():
					
					# ensure that only ressources located on the domain /sub-domain is requested 
					if i.startswith('http'):
						parts = i.split('/')
						host = parts[2]

						# if the ressource is out side of the domain, skip it
						if not host in self.host.split('/')[2]:
							continue

						# else update the url so that it only contains the relative location
						else:
							i = '/'.join(parts[3:])

					self.queue.put( {"host": self.host, "url": i} )
				
		# add 'None' to queue - stops threads when no items are left
		for i in range(self.threads): self.queue.put( None )

		# start the threads
		for i in range(self.threads):
			w = RequesterThread(i, self.queue, self.cache, self.results)
			w.daemon = True
			self.workers.append(w)
			w.start()

		self.queue.join()




