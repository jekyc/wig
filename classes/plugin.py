import json
from collections import defaultdict


class Plugin(object):

	def __init__(self, results):
		self.__items = []
		self.prefix = []
		self.is_data_loaded = False

		######################################################
		# these should be set by classes inhereting this class
		#

		# the file to load fingerprints from
		self.data_file = ""

		# used to group plugins and is displayed in the output 
		self.category = ""

		# the name of the plugin
		self.name = ""

		# if multiple matches are found for a given url,
		# should this count against the match score
		self.use_weights = False

		# should the plugin be affected by the profile chosen
		self.use_profile = True

		# log object 
		self.log = defaultdict(lambda: defaultdict(set))
		#          ^ url               ^ category  ^ version 
	
	def load_data(self):
		# load the fingeprints from the json file
		# add prifixes if these are defined
		try:	
			with open(self.data_file) as f:
				self.__items = json.load(f)

			self.__add_prefixes()
			self.is_data_loaded = True
		except:
			raise Exception("No data file to open")

	def __add_prefixes(self):
		# actually add the prefixes to each fingerprint
		for prefix in self.prefix:
			if prefix == "": continue
			t = [self.__update_url(i, prefix) for i in self.__items]
			self.__items.extend(t)
	
	def __update_url(self, element, prefix):
		e = dict(element) # makes a copy, not a reference
		e["url"] = prefix + e["url"]
		return e

	def set_items(self, items):
		self.__items = items

	def set_profile(self, profile):
		# the exposed method for applying a profile
		if self.use_profile:
			self.load_data()
			self.__items = profile.apply(self.__items)

	def get_logs(self):
		return self.log

	def get_all_items(self):
		return self.__items

	def get_num_fps(self):
		return len(self.__items)

	def get_unique_urls(self):
		return list(set([i["url"] for i in self.__items]))

	def add_results(self, data, name=None):
		# 'data' should be a list of dicts:
		# [{'url': bla, 'version': bla, 'count': 23}, {...}]
		if name == None: name = self.name
		for d in data:
			url = d['url'] if 'url' in d else '/'

			self.log[url][name].add(d['version'])
			self.results.add(self.category, name, d, self.use_weights)
