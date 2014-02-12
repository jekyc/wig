from collections import Counter
from classes.plugin import Plugin
import json

class OperatingSystem(Plugin):

	def __init__(self, data_file, cache, results):
		super().__init__(results)
		self.cache = cache
		self.results = results

		self.data_file = data_file
		self.category = "Operating System"
		self.os = Counter()
		self.packages = Counter()
		self.oss = []
		self.use_profile = False


	def load_extra_data(self, extra_file):
		all_items = self.get_all_items()

		with open(extra_file) as f:
			items = json.load(f)
			for package in items:
				for version in items[package]:
					os_list = items[package][version]
					if package in all_items:
						if version in all_items[package]:
							all_items[package][version].extend(os_list)
						else:
							all_items[package][version] = os_list
					else:
						all_items[package] = {version: os_list}

		self.set_items(all_items)


	def find_match(self, response):
		headers = response.headers

		if 'server' in headers:
			line = headers['server']

			if "(" in line:
				os = line[line.find('(')+1:line.find(')')]
				line = line[:line.find('(')-1] + line[line.find(')')+1: ]
			else:
				os = False

			if os: self.oss.append(os.lower())

			for part in line.split(" "):
				try:
					pkg,version = part.split('/')
					self.packages[pkg] += 1
					os_list = self.db[pkg][version]
					for i in os_list:
						os, version = i
						self.os[(os, version)] += 1

				except Exception as e:
					continue

	def search_results(self):
		# search for results found in "X-Powered-By" header
		# which is added by the 'header' plugin
		res = self.results.get_results()
		if not "Server Info" in res:
			return []

		serverinfo = res["Server Info"]
		pkg_serverinfo = set(serverinfo.keys())
		pkg_packages = set(self.packages.keys())

		diff = pkg_serverinfo - pkg_packages
		out = []
		for pkg in diff:
			try:
				for ver in serverinfo[pkg]:
					count = serverinfo[pkg][ver]
					os_list = self.db[pkg][ver]
					for i in os_list:
						print(i)
						os, version = i
						out.append( {'version': version, 'os': os, 'count': count} )
			except:
				pass

		return out


	def find_results(self, results):
		if len(results) == 0: return

		prio = sorted(results, key=lambda x:x['count'], reverse=True)
		max_count = prio[0]['count']
		relevant = []
		for i in prio:
			if i['count'] == max_count:
				if len(relevant) > 0  and i[0] == "": continue
				self.add_results([{'version': i['version'], 'count': i['count']}], i['os'])
			else:
				break

	def finalize(self):
		# if an os string 'self.oss' has been found in the header
		# prioritize the identified os's in self.os

		# iterate over the list of os strings found
		for os in self.oss:
			# iterate over the fingerprinted os's
			for key in self.os:
				if os in key[0].lower():
					self.os[key] += 100

		# add OS to results: self.os: {(os, version): weight, ...}
		r = self.search_results()
		for p in self.os:
			r.append({'version': p[1], 'os': p[0], 'count': self.os[p]})

		self.find_results(r)
		

	def run(self):
		self.load_data()
		self.load_extra_data("data/os/os_fingerprints_static.json")
		self.db = self.get_all_items()

		responses = self.cache.get_responses()
		for response in responses:
			self.find_match(response)

		self.finalize()
		self.search_results()

def get_instances(host, cache, results):
	return [
		OperatingSystem("data/os/os_fingerprints.json", cache, results)
	]
