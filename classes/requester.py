import requests, queue, threading, time, hashlib,sys
from classes.cache import Cache
from classes.results import Results


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
		url = item['url']

		if host.endswith('/') and url.startswith('/'):
			uri = host + url[1:]
		else:
			uri = host + url
		
		if not uri in self.cache:
			try:
				r = requests.get(uri, verify=False)
				self.cache[uri] = r

				self.cache[uri].md5 = hashlib.md5(r.content).hexdigest().lower()				
				r = self.cache[uri]
			except Exception as e:
				r = None
		else:
			r = self.cache[uri]

		return r


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
	def __init__(self, host, fps, cache):
		self.fps = fps
		self.threads = len(fps)
		self.workers = []
		self.host = host

		self.cache = cache
		self.results = Results()
		self.queue = queue.Queue()
		self.requested = queue.Queue()
		

	def run(self):

		for fp_list in self.fps:
			self.queue.put({ "host": self.host, "url": fp_list[0]['url'], "fps": fp_list })

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

		return self.requested
