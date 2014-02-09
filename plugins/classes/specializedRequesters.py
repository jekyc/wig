from plugins.classes.requester import Requester
from plugins.classes.specializedMatchers import MD5Matcher, StringMatcher, RegexMatcher


class CMSReq(Requester):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.category = "CMS"
		self.match_class = None
		self.use_weights = False

	def prepare_results(self, matches):
		data = []
		for m in matches:
			url = m['response'].url
			version = m['output']
			
			for d in data:
				if d['url'] == url:
					d['count'] += 1
					break
			else:
				data.append( {'url': url, 'count': 1, 'version': version} )

		return data

	def run(self):
		# make requests
		requested = self.request_uniq()

		# find matches
		matcher = self.match_class(requested)
		matches = matcher.get_matches()

		# add to results
		intermediate_results = self.prepare_results(matches)
		self.add_results(intermediate_results)



class CMSReqMD5(CMSReq):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.match_class = MD5Matcher
		self.use_weights = True


class CMSReqString(CMSReq):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.match_class = StringMatcher


class CMSReqRegex(CMSReq):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.match_class = RegexMatcher