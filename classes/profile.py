
class Profile(object):

	def __init__(self, profile):
		self.profiles = {
			1: {'name': 'OnlyOne',		'method': self.one_request},
			2: {'name': 'OnePerPlugin',	'method': self.one_request_per_plugin},
			3: {'name': 'OnePlugin',	'method': self.one_plugin},
			4: {'name': 'All',			'method': self.default},
		}

		if profile in self.profiles:
			self.name = self.profiles[profile]['name']
			self.profile = self.profiles[profile]['method']
		else:
			self.name = self.profiles[4]['name']
			self.profile = self.profiles[4]['method']


	def apply(self, items, plugin_name, filter_name):
		# 'plugin_name' is the name of the plugin to which the profile is being applied
		self.plugin_name = plugin_name

		# 'filter_name' is the name supplied by the user
		self.filter_name = filter_name

		return self.profile(items)


	def one_request(self, items):
		# only use fingerprints that apply to '/'
		return [fp for fp in items if fp['url'] == '/']


	def one_request_per_plugin(self, items):
		# only use one request per plugin. Search for the one that has
		# the most fingerprints.

		out = []
		# the structure use for this is:
		# {
		#	'url': {
		#		'counter':   *number of occurrences
		#		'versions':  *set of versions
		#	}
		# }
		#
		# in case of a tie, the number of versions will be the tie breaker

		# create dict for sorting
		sorting = {}
		for item in items:
			url = item['url']
			version = item['output']
			try:
				sorting[url]['count'] += 1
				sorting[url]['versions'].add(version)
			except:
				sorting[url] = {'count': 1, 'versions': set([version])}

		# order after the fingerprints' url count
		sorted_url = sorted(sorting.items(), key=lambda x:x[1]['count'], reverse=True)

		# find the maximum count
		max_count = sorted_url[0][1]['count']

		# extract urls with 'count' = 'max_count'
		best_urls = [i for i in sorted_url if i[1]['count'] == max_count]

		# tie breaker - extract the one with most versions
		best_url = sorted(best_urls, key=lambda x:len(x[1]['versions']))[0][0]

		# get all the fingerprints with the 'url' = 'best_url'
		out = [item for item in items if item['url']==best_url]

		return out


	def one_plugin(self, items):
		if self.plugin_name.lower() == self.filter_name.lower():
			return items
		else:
			return []

	def default(self, items):
		return items
