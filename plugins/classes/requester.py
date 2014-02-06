import requests
import queue
from plugins.classes.plugin import Plugin
from plugins.classes.requesterThread import RequesterThread
from plugins.classes.cache import Cache

class Requester(Plugin):
	def __init__(self, host, cache, results):
		super().__init__(requests)
		self.threads = 10
		self.queue = queue.Queue()
		self.requested = queue.Queue()
		self.workers = []
		self.host = host

		# set cache
		if not cache:	self.cache = Cache()
		else: 			self.cache = cache

		# set results
		if not results:	self.results = Results()
		else:			self.results = results
		
	def request_uniq(self):
		if not self.is_data_loaded:
			self.load_data()

		# fill queue with only unique urls
		for i in self.get_unique_urls():
			self.queue.put( {"host": self.host, "url": i} )

		# add 'None' to queue - stops threads when no items are left
		for i in range(self.threads): self.queue.put( None )

		# start the threads
		for i in range(self.threads):
			w = RequesterThread(i, self.queue, self.cache, self.requested)
			w.daemon = True
			self.workers.append(w)
			w.start()

		# join when all work is done
		self.queue.join()

		# convert queue to list
		# pair items from self.get_all_items with the urls requested
		result_list = []
		all_items = self.get_all_items()
		while not self.requested.empty():
			url, response = self.requested.get()
			for item in all_items:
				if item['url'] == url:
					item["response"] = response
					result_list.append( item )
		
		return result_list