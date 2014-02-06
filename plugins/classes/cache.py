import queue

class Cache(queue.Queue):
	def _init(self, maxsize):
		self.queue = dict()

	def __getitem__(self, path):
		return self.queue[path]

	def __setitem__(self, path, response):
		with self.mutex:
			self.queue[path] = response

	def __contains__(self, item):
		with self.mutex:
			return item in self.queue

	def get_num_urls(self):
		return len(self.queue.keys())

	def get_responses(self):
		items = []
		for item in self.queue:
			items.append(self.queue[item])
		return items
