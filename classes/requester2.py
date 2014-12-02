import queue, threading, time, hashlib,sys, re
import urllib.request
from classes.cache import Cache
from classes.results import Results
from classes.request import PageFetcher, Request


class RequesterThread(threading.Thread):
	def __init__(self, id, queue, cache, requested):
		threading.Thread.__init__(self)
		self.id = id
		self.queue = queue
		self.cache = cache
		self.requested = requested
		self.kill = False

	def make_request(self, item):
		host = item['host']
		path = item['url']

		fetcher = PageFetcher(host + path)

		# check if the URLs has been requested before
		# if it has, don't make the request again, but fetch 
		# it from the cache

		if not fetcher.url in self.cache:
			try:
				# make the request, and add it to the cache
				request = fetcher.get()

				self.cache[fetcher.url] = request
				self.cache[request.get_url()] = request
				for r in request.history:
					self.cache[r.get_url()] = request

			except Exception as e:
				#print(e)
				request = None
		else:
			request = self.cache[fetcher.url]

		return request

	def run(self):
		while not self.kill:
			item = self.queue.get()
			if item is None:
				self.queue.task_done()
				break

			response = self.make_request(item)
			if response is None:
				self.queue.task_done()
				continue

			self.requested.put( (item['fps'], response ) )
			self.queue.task_done()



class Requester(object):
	def __init__(self, host, cache):
		self.threads = None
		self.workers = []
		self.host = host
		self.find_404s = False

		self.cache = cache
		self.results = Results()
		self.queue = queue.Queue()
		self.requested = queue.Queue()


	# set the fingerprints for the requester to get.	
	# fps should be a list of lists of fingerprints:
	# [ [fp, fp, fp], [fp, fp, ...], ...]
	# each fingerprinter in the innerlist must have the same URL
	# The number of elements in the outer list equals the number
	# of threads used
	def set_fingerprints(self, fps):
		self.fps = fps
		self.threads = len(fps)


	def set_find_404(self, find_404s):
		self.find_404s = find_404s

	def run(self):

		for fp_list in self.fps:
			self.queue.put({ "host": self.host, "url": fp_list[0]['url'], "fps": fp_list })

		# add 'None' to queue - stops threads when no items are left
		for i in range(self.threads): self.queue.put( None )

		# start the threads
		self.works = []
		for i in range(self.threads):
			w = RequesterThread(i, self.queue, self.cache, self.requested)
			w.daemon = True
			self.workers.append(w)
			w.start()

		# join when all work is done
		self.queue.join()

		# the define_404 should only be true during the 
		# preprocessing. 
		if not self.find_404s:
			return self.requested

		# if the define_404 flag is set, then the 
		# supplied URLs are to be used for identification of 404 
		# pages
		else:
			error_pages = queue.Queue()
			while self.requested.qsize() > 0:
				_,response = self.requested.get()
				error_pages.put(response.md5_404)

			return error_pages





