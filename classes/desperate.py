from classes.specializedMatchers import DesperateMatcher
from collections import Counter
from collections import defaultdict

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

	def run(self):
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