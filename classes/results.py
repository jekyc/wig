from collections import defaultdict, Counter
from classes.color import Color
import pprint


class Results(object):

	def __init__(self):
		self.width = None
		self.color = Color()
		
		# the storage for 'string' and 'regex' matched fingerprints 
		# since these don't need extra processing they are added directly 
		# to the final scores
		self.scores = defaultdict(lambda: defaultdict(lambda: Counter()))
		#		      ^ Category          ^ Name              ^ Version           

		# md5 fingerprints are based on content that might not hav been changed 
		# across different versions of the cms. The score of a match is based on
		# the number of 'hits' for that URL. The finale score for a cms version will be:
		#  1 / number_of_hits
		#
		self.md5_matches = defaultdict(lambda: defaultdict(lambda: set()))
		#		           ^ Url               ^ cms               ^ versions



	def _calc_md5_score(self):

		# calculate the final scores for md5 fingerprints, and add
		# them to the final scores 
		for url in self.md5_matches:
			for cms in self.md5_matches[url]:

				# get the number of 'hits' for a specific CMS and URL
				number_of_hits = len(self.md5_matches[url][cms])

				# update the score for thencms version 
				for version in self.md5_matches[url][cms]:
					self.scores['CMS'][cms][version] += (1 / number_of_hits)



	def found_match(self,cms):
		in_scores = cms in self.scores['CMS']
		in_md5 = cms in set([cms for url in self.md5_matches for cms in self.md5_matches[url]])
		return in_scores or in_md5


	def add_cms(self, fp):
		url = fp['url']
		cms = fp['cms']
		ver = fp['output']

		# if the type of the fingerprint is md5, then the we need 
		# to keep track of how many cms versions have been detected 
		# the a given URL, as this determines the weight score of
		# fingerprint match
		if fp['type'] == 'md5':
			self.md5_matches[url][cms].add(ver)

		# if the type is either 'string' or 'regex' then the match show
		# should be summed with previous matches
		# if the version is '' add a weight of '0'. This will set the version
		# to the worst match 
		# else if the fingerprint has weights, then this should be used, 
		# else default to the value 1
		else:
			if ver == '':
				self.scores['CMS'][cms][ver] += 0
			elif 'weight' in fp:
				self.scores['CMS'][cms][ver] += fp['weight']
			else:
				self.scores['CMS'][cms][ver] += 1

	
	def add(self, category, name, version, weight=1):
		# if the version is blank or true, add '0' to 
		# set it to the worst match
		if version == '' or version == True:
			self.scores[category][name][version] += 0

		# else add the weight
		else:
			self.scores[category][name][version] += weight



	def set_width(self, width):
		self.width = width


	def __str__(self):

		self._calc_md5_score()
		out = "\n"
		o_cat = sorted([c for c in self.scores])

		for category in o_cat:

			#out += "{0:<20}".format(category, )
			start = "___ " + self.color.format(category, 'red', False) + " "
			out +=	start + "_" * (self.width - (len(category) + 5)) + "\n"
			plugin_list = []

			o_plug = sorted([p for p in self.scores[category]])
			for plugin in o_plug:
				v = self.scores[category][plugin]

				# get only most relevant results
				# sort by weight
				versions = sorted(v.items(), key=lambda x:x[1], reverse=True)

				# pick only the first(s) element
				relevant = [i[0] for i in versions if i[1] == versions[0][1]]

				plug_str = "%s: " % (plugin, )
				ver_str =  ", ".join(relevant)

				plugin_list.append(plug_str + ver_str)
			
			out += "\n".join(plugin_list) + "\n\n"

		return out[:-1]
