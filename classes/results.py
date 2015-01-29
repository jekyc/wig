from collections import defaultdict, Counter
from classes.color import Color
from classes.sitemap import Sitemap
import pprint


class Results(object):

	def __init__(self, options):
		self.width = None
		self.color = Color()
		self.printer = None

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

		self.sitemap = Sitemap()

		self.site_info = {
			'ip': '',
			'title': '',
			'cookies': ''
		}


	def set_printer(self, printer):
		self.printer = printer


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

		# add to the sitemap
		self.sitemap.add(url)

		# add note if present
		if 'note' in fp:
			url = fp['url']
			note = fp['note']
			self.printer.print('- %s: %s' % (note, url), 2)
			self.scores["Interesting"][url][note] += 1

		# if the type of the fingerprint is md5, then the we need 
		# to keep track of how many cms versions have been detected 
		# the a given URL, as this determines the weight score of
		# fingerprint match
		if fp['type'] == 'md5':
			self.md5_matches[url][cms].add(ver)
			matched = fp['md5']

		# if the type is either 'string' or 'regex' then the match show
		# should be summed with previous matches
		# if the version is '' add a weight of '0'. This will set the version
		# to the worst match 
		# else if the fingerprint has weights, then this should be used, 
		# else default to the value 1
		else:
			if 'string' in fp:
				matched = fp['string']
			elif 'regex' in fp:
				matched = fp['regex']


			if ver == '':
				self.scores['CMS'][cms][ver] += 0
			elif 'weight' in fp:
				self.scores['CMS'][cms][ver] += fp['weight']
			else:
				self.scores['CMS'][cms][ver] += 1

		self.printer.print('- Found match: %s - %s %s - %s: %s' % (url, cms, ver, fp['type'], matched), 5)
		

	
	def add(self, category, name, version=None, fingerprint=None, weight=1):
		matched = ''
		match_type = ''
		url = ''

		if fingerprint is not None:

			# overwrite weight if defined in fingerprint
			if 'weight' in fingerprint:
				weight = fingerprint['weight']

			if 'header' in fingerprint:
				matched = fingerprint['header'] + ': '
				match_type = 'header/'
			
			if 'string' in fingerprint:
				matched += fingerprint['string']
				match_type += 'string'
			elif 'regex' in fingerprint:
				matched += fingerprint['regex']
				match_type += 'regex'
			elif 'md5' in fingerprint:
				matched += fingerprint['md5']
				match_type += 'md5'

			# add to the sitemap
			if 'url' in fingerprint:
				self.sitemap.add(fingerprint['url'])
				url = fingerprint['url']
			else:
				url = ''

			# add note if present
			if 'note' in fingerprint:
				note = fingerprint['note']
				self.printer.print('- %s: %s' % (note, url), 2)
				self.scores["Interesting"][url][note] += weight

		self.printer.print('- Found match: %s - %s %s - %s: %s' % (url, name, version, match_type, matched), 5)

		# if there has been no version detection (interesting file discovery)
		# skip adding the versions to the scores
		if version == None:
			pass

		# if the version is blank or true, add '0' to 
		# set it to the worst match
		elif version == '' or version == True:
			self.scores[category][name][version] += 0

		# else add the weight
		else:
			self.scores[category][name][version] += weight


	def set_width(self, width):
		self.width = width


	def set_ip(self, ip):
		self.site_info['ip'] = ip


	def set_title(self, title):
		self.site_info['title'] = title


	def set_cookies(self, cookies):
		self.site_info['cookies'] = cookies


	def get_sitemap(self):
		return str(self.sitemap)


	def get_platform_results(self):
		return self.scores['Platform']


	def get_results(self):
		self._calc_md5_score()

		results = {}
		self.printer.print('Results:', 2)
		for category in self.scores:
			if category not in results: results[category] = {}
			
			for plugin in sorted(self.scores[category]):
				v = self.scores[category][plugin]

				versions = sorted(v.items(), key=lambda x:x[1], reverse=True)
				
				for i in versions:
					self.printer.print('- %s: %s - Version: %s [%s]' % (category, plugin, i[0], i[1]), 2)

				relevant = sorted(i[0] for i in versions if i[1] == versions[0][1])
				results[category][plugin] = relevant

		return results
