import json,os, sys, pprint
from collections import defaultdict


class Fingerprints(object):

	def __init__(self):
		
		# Dictionaries in python3.3 use a random hashing algorithm,
		# which means that the order items in i dict is not consistent
		# when iterating over over the dict.
		# For this reason fingerprints are not stored in a dict

		# the list used for storing cms fingerprints
		self.all = []

		# a list of cms names
		self._cms_names = []

		# a list of cms types
		self._cms_types = []
		self._cms_type_index = []

		# operating system fingerprints
		#                      _ Software          _ Version   _ set of tuples (OS, version)
		self.os_fingerprints = defaultdict(lambda: defaultdict(set))
	
		# javascript fingerprints
		self.js_fingerprints = []

		# generic interesting files
		self.interesting = []

		# the number of cms fingerprints
		self.count = 0

		# an ordered list of cms fingerprints. See 'create_ordered_list'
		self.ordered = []

		# cms types
		self.types = ['md5', 'regex', 'string']

		# load the cms fingerprints and create the ordered list
		self._load('cms', 'data/cms/')
		self.create_ordered_list()

		# load the operating system fingerprints
		self._load('os', 'data/os')

		# load error pages
		with open('data/error_pages.json') as fh:
			self.error_pages = json.load(fh)

		# load JavaScript
		self._load('js', 'data/js/md5')	

		# load interesting files
		self._load_interesting()


	def _load_interesting(self):
		path = 'data/interesting.json'
		with open(path) as fh:
			for fp in json.load(fh):
				if 'string' in fp:
					fp_type = 'string'
				elif 'regex' in fp:
					fp_type = 'regex'

				if 'ext' in fp:
					for ext in fp['ext']:
						self.interesting.append([{
							'url': fp['url'] + '.' + ext,
							'note': fp['note'],
							'string': fp['string'],
							'type': fp_type
						}])
				else:
					fp['type'] = fp_type
					self.interesting.append([fp])


	def _load(self, fp_type, data_dir):
		
		def add_cms(cms, data_file):
			fp_type = data_file.split('/')[2]
			# add the fingerprints to the fingerprint storage
			with open(data_file) as fh:
				for fp in json.load(fh):
					fp['type'] = fp_type
					fp['cms'] = cms
					self.count += 1
					self.all.append(fp)


		def add_os(data_file):
			with open(data_file) as fh:
				item = json.load(fh)
				for sw in item:
					for ver in item[sw]:
						for data in item[sw][ver]:
							self.count += 1
							self.os_fingerprints[sw.lower()][ver].add(( 
								data[0],
								data[1],
								1 if len(data) == 2 else data[2]
							))


		def add_js(data_file):
			name = data_file.split('/')[-1].split('.')[0]
			fp_type = data_file.split('/')[-2]
			with open(data_file) as fh:
				items = json.load(fh)
				for item in items:
					self.count += 1
					item['name'] = name
					item['type'] = fp_type
					self.js_fingerprints.append(item)


		if fp_type == 'cms':
			dirs = [data_dir + t for t in self.types]
		else:
			dirs = [data_dir]
		
		for data_dir in dirs:
			for f in os.listdir(data_dir):
				try:
					# only load json files
					if not len(f.split('.')) == 2: continue
					name,ext = f.split('.')
					if not ext == 'json': continue

					data_file = data_dir +'/'+ f

					if fp_type == 'cms':
						add_cms(name, data_file)
						if not name in self._cms_names:
							self._cms_names.append(name)
					
					elif fp_type == 'os':
						add_os(data_file)
					
					elif fp_type == 'js':
						add_js(data_file)


				except Exception as e:
					continue
		

	def create_ordered_list(self):
		
		# list of fp with unique urls
		seen_urls = set()
		fp_unique_urls = []
		for fp in self.all: 
			if fp['url'] not in seen_urls:
				fp_unique_urls.append(fp)
				seen_urls.add(fp['url'])

		# count the max number of urls for the cms
		count = defaultdict(set)
		for fp in fp_unique_urls: 
			count[fp['cms']].add( fp['url'] )

		max_number_urls = max( [len(count[i]) for i in count] )

		# create a matrix of names vs fps
		# [
		#   [fp1, fp2, fp3],        <--- cms 1
		#   [fp4, fp5],             <--- cms 2
		#   [fp6, fp7, fp8, fp8]    <--- cms 3
		# ]
		matrix = [[] for _ in self._cms_names]
		for fp in fp_unique_urls:
			name_index = self._cms_names.index(fp['cms'])
			matrix[name_index].append(fp)


		# flatten the matrix to a single list
		for fp_index in range(0, max_number_urls):
			for cms in self._cms_names:
				try:
					index = self._cms_names.index(cms)
					fp = matrix[index][fp_index]
					self.ordered.append(fp)
				except:
					pass

		# collect all urls for each fp
		# crappy O(n^2) implementation - should be redone at some point
		out = []
		for fp in self.ordered:
			url = fp['url']
			out.append( [fp for fp in self.all if fp['url'] == url] )

		self.ordered = out


	# this returns the raw list of fingerprints
	# mainly used for the crawler 
	def get_all(self):
		return self.all


	# get the URLs that should produce an error page
	def get_error_urls(self):
		return self.error_pages


	# get the fingerprints used for Operating System detection
	def get_os_fingerprints(self):
		return self.os_fingerprints


	# a list of fingerprints that is sorted based on the CMS to
	# which the fingerprint belongs. Instead of testing all fingerprints
	# for a single CMS sequencially, the fingerprints for the CMS
	# is spread out.
	def get_ordered_list(self):
		return self.ordered


	# the number of fingerprints in the database
	def get_size(self):
		return self.count


	# get fingerprints for a specific cms
	# used for version detection of a single
	# cms - DiscoverVersion()
	def get_fingerprints_for_cms(self, cms):
		fps = defaultdict(list)
		for fp in self.all:
			if fp['cms'] == cms:
				fps[fp['url']].append(fp)

		return [ fps[i] for i in fps ]


	# fingerprints used for JavaScript detection
	def get_js_fingerprints(self):
		return self.js_fingerprints


	# get fingerprints used to search for interesting files
	def get_interesting_fingerprints(self):
		return self.interesting


