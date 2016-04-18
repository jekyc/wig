class Sitemap(object):

	def __init__(self):
		self.sitemap = {}
		self.urls = []

	def __str__(self):
		#self.create_tree()
		#self._recurse(self.sitemap, '')

		return '\n'.join(sorted(list(set(self.urls)))) 

	def add(self, url):
		self.urls.append(url)

	def create_tree(self):
		for url in [i.split('/') for i in list(set(self.urls))]:
			current_level = self.sitemap
			for part in url[1:]:
				if part not in current_level:
					current_level[part] = {}
		
				current_level = current_level[part]


	def _recurse(self, dictionary, space):
		for key in dictionary:
			if key == '': continue
			print(space + key)

			if not dictionary[key] == {}:
				self._recurse(dictionary[key], space + '  ')