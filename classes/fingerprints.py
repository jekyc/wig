import json,os, sys, pprint, re
from collections import defaultdict


class Fingerprints(object):

	def __init__(self):
		
		# Dictionaries in python3.3 use a random hashing algorithm,
		# which means that the order items in i dict is not consistent
		# when iterating over over the dict.
		# For this reason fingerprints are not stored in a dict

		# the number of cms fingerprints
		self.count = 0

		# operating system fingerprints
		#                      _ Software          _ Version   _ set of tuples (OS, version)
		self.os_fingerprints = defaultdict(lambda: defaultdict(set))
	
		self.all = []				# the list used for storing cms fingerprints
		self.ordered = []			# an ordered list of cms fingerprints. See 'create_ordered_list'
		self._cms_names = []		# a list of cms names
		self.interesting = []		# generic interesting files
		self.js_fingerprints = []	# javascript fingerprints
		self.url_less = []			# fingerprints that don't have an url specified
		self.translator = {}		# dict containing file name mappings


		# load fingerprints
		self._load_dictionary()
		self._load()
		self._load_os()
		self._load_js()	
		self._load_interesting()
		self._load_error()
		
		self.create_ordered_list()
		

	def _replace_version_text(self, text):
		# replace text in version output with something else
		# (most likely an emtpy string) to improve output
		text = re.sub('^wmf/', '', text)
		text = re.sub('^develsnap_', '', text)
		text = re.sub('^release_candidate_', '', text)
		text = re.sub('^release_stable_', '', text)
		text = re.sub('^(?i)release[-|_]', '', text)	# Umbraco, phpmyadmin
		text = re.sub('^[R|r][E|e][L|l]_', '', text)				
		text = re.sub('^mt', '', text)				# Movable Type
		text = re.sub('^mybb_', '', text)			# myBB

		return text


	def _load_dictionary(self):
		path = 'data/dictionary.json'
		with open(path) as fh:
			self.translator = json.load(fh)


	def _load_error(self):
		path = 'data/error_pages.json'
		with open(path) as fh:
			self.error_pages = json.load(fh)


	def _load_interesting(self):
		path = 'data/interesting.json'
		category = 'Interesting'

		with open(path) as fh:
			for fp in json.load(fh):
				fp_type = 'string' if 'string' in fp else 'regex'
				fp['category'] = category

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


	def _load(self):
		paths = {'CMS': 'data/cms/', 'Platform': 'data/platform/'}
		types = ['md5', 'regex', 'string', 'header']
		
		for category in paths:
			path =  paths[category]
			dirs = [path + t for t in types]

			for data_dir in types:
				for f in os.listdir(path + data_dir):
					data_file = path + '/' + data_dir +'/'+ f

					try:
						# exit if not json file
						if not len(f.split('.')) == 2: continue
						name,ext = f.split('.')
						if not ext == 'json': continue
						
						# add the fingerprints to the fingerprint storage
						name = self.translator[name]
						with open(data_file) as fh:
							json_data = json.load(fh) 
							for fp in json_data:
								fp['output'] = self._replace_version_text(fp['output'])

								fp['type'] = data_dir
								fp['cms']  = name
								fp['category'] = category
								
								self.count += 1

								if 'url' in fp:
									self.all.append(fp)
								else:
									# if the fingerprint does not have the 'url' key
									# it should be added to the list of fingerprints
									# that are checked during post-processing 
									self.url_less.append(fp)
								
								if not name in self._cms_names:
									self._cms_names.append(name)

					except Exception as e:
						continue


	def _load_os(self):
		path = 'data/os'

		for f in os.listdir(path):
			try:
				# only load json files
				if not len(f.split('.')) == 2: continue
				_,ext = f.split('.')
				if not ext == 'json': continue

				with open(path +'/'+ f) as fh:
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
					del item

			except Exception as e:
				continue


	def _load_js(self):
		paths = {'md5': 'data/js/md5', 'regex':'data/js/regex'}
		category = 'JavaScript Libraries'

		for fp_type in paths:
			path = paths[fp_type]
			for f in os.listdir(path):
				try:
					# only load json files
					if not len(f.split('.')) == 2: continue
					name,ext = f.split('.')
					if not ext == 'json': continue

					name = self.translator[name]
					with open(os.path.join(path, f)) as fh:
						items = json.load(fh)
						for item in items:
							self.count += 1
							item['name'], item['type'] = name, fp_type
							item['category'] = category
							self.js_fingerprints.append(item)
							self.url_less.append(item)
								
				except Exception as e:
					continue


	def create_ordered_list(self):
		
		seen_urls = set()
		fp_unique_urls = []
		for fp in self.all: 
			if fp['url'] not in seen_urls:
				fp_unique_urls.append(fp)
				seen_urls.add(fp['url'])

		del seen_urls

		# count the max number of urls for the cms
		count = defaultdict(set)
		for fp in fp_unique_urls: 
			count[fp['cms']].add( fp['url'] )

		max_number_urls = max( [len(count[i]) for i in count] )
		del count

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

		del matrix

		# collect all urls for each fp
		# crappy O(n^2) implementation - should be redone at some point
		out = []
		for fp in self.ordered:
			url = fp['url']
			out.append( [fp for fp in self.all if fp['url'] == url] )

		self.ordered = out
		del out


	# this returns the raw list of fingerprints
	# mainly used for the crawler 
	def get_all(self):
		return self.all

	# get all the fingerprints that don't have an url
	def get_url_less(self):
		return self.url_less


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


