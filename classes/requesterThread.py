import threading, time
import hashlib
import requests

class RequesterThread(threading.Thread):
	def __init__(self, id, queue, cache, requested):
		threading.Thread.__init__(self)
		self.id = id
		self.queue = queue
		self.cache = cache
		self.requested = requested
		self.kill = False

	def make_request(self, item):
		if item['host'].endswith('/') and item['url'].startswith('/'):
			uri = item['host'] + item['url'][1:]
		else:
			uri = item["host"] + item["url"]
		

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

			self.requested.put( (item["url"], response) )
			self.queue.task_done()
