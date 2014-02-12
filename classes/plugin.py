import json
from collections import defaultdict


class Plugin(object):

	def __init__(self, results):
		self.__items = []
		self.prefix = []
		self.is_data_loaded = False

		# these should be set by classes inhereting this class
		self.data_file = ""
		self.category = ""
		self.name = ""
		self.use_weights = False
		self.use_profile = True

	def load_data(self):
		try:	
			with open(self.data_file) as f:
				self.__items = json.load(f)

			self.__add_prefixes()
			self.is_data_loaded = True
		except:
			raise Exception("No data file to open")

	def __add_prefixes(self):
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
		if self.use_profile:
			self.load_data()
			self.__items = profile.apply(self.__items)

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
			self.results.add(self.category, name, d, self.use_weights)
