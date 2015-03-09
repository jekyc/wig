import queue, pickle, os, time, hashlib, re

# wig - Cache
#
# wig uses a cache to store the requests and responses made during a scan. 
# This helps limit the amount of requests that it makes, as a request for 
# resource is only made once.
# To further limit the amount of requests, wig saves a copy of the cache
# and will reuse it for scans run within 24 hours.
#
# NOTE: The pickle module is used to save and load the cache. This has the
#       side effect, that the extra variables which are added to a an 
#       instance of Requests are not kept. Currently 2 variables are added:
#       md5 and md5_404. These values have to be recalculated when loading 
#       a pickled cache. Ideally, a custom object should be created for 
#       the modified requests, so this is on the TODO.


class Cache(queue.Queue):
	def _init(self, maxsize):
		self.queue = dict()
		self.host = None
		self.cache_dir = './cache/'
		self.now = str(time.time()).split('.')[0]

		# only load cache data that is new than this
		# (currently this is set for 24 hours)
		self.cache_ttl = 60*60*24

		# check if cache dir exists - create if not
		self._check_or_create_cache()

		# check if there are caches that are older than ttl
		self._remove_old_caches()


	def __getitem__(self, path):
		return self.queue[path]


	def __setitem__(self, path, response):
		with self.mutex:
			self.queue[path] = response


	def __contains__(self, url):
		with self.mutex:
			return url in self.queue


	def _check_or_create_cache(self):
		if not os.path.exists(self.cache_dir):
			os.makedirs(self.cache_dir)


	def _remove_old_caches(self):
		# remove caches that are too old
		
		# bail if the directory does not exist
		if not os.path.exists(self.cache_dir): return None

		# iterate over the cache files
		for cache_file in os.listdir(self.cache_dir):
			
			# skip the file if it's not a cache file
			if not cache_file.endswith('.cache'):
				continue

			# check if the cache is for the host
			hostname, time_ext = cache_file.split('_-_')
			save_time,_ = time_ext.split('.')

			# check the age of the cache, and remove it if older than
			# ttl
			age = int(self.now) - int(save_time)
			if age > self.cache_ttl:
				file_name = os.path.join(self.cache_dir, cache_file)
				os.remove(file_name)


	def _get_name_for_cache_file(self):
		# check if there already is an older version of the cache
		# if there is, return the name of this file, such that,
		# it will be overwritten
		if not os.path.exists(self.cache_dir):
			os.makedirs(self.cache_dir)

		for cache_file in os.listdir(self.cache_dir):
			# skip the file if it's not a cache file
			if not cache_file.endswith('.cache'):
				continue
			
			# check if the cache is for the host
			hostname,_ = cache_file.split('_-_')
			if hostname == self.cache_name.split('_-_')[0]:
				return os.path.join(self.cache_dir, cache_file)

		# if there aren't any previous cache files, generate a 
		# new name for the cache
		return os.path.join(self.cache_dir, self.cache_name)


	def set_host(self, host):
		self.host = host
		self.cache_name = self.host.replace('/','').replace(':','..') + '_-_' + self.now + '.cache'


	def get_num_urls(self):
		return len(set([self.queue[key].id for key in self.queue]))


	def get_urls(self):
		return [k for k in self.queue]

	def get_responses(self):
		return [self.queue[key] for key in self.queue]


	def save(self):
		# save the queue for later use
		# this will help limit the amount of requests made
		# when scanning the same site multiple times
		with self.mutex:		
			file_name = self._get_name_for_cache_file()
			with open(file_name, 'wb') as cache_file:
				try:
					pickle.dump(self.queue, cache_file)
				except:
					print('Error saving cache: ' + file_name)
	
	def load(self):
		# loads previously saved cache for the host

		# bail if the host is not set
		if self.host is None: return None

		# search the cache dir
		for cache_file in os.listdir(self.cache_dir):

			# skip the file if it's not a cache file
			if not cache_file.endswith('.cache'):
				continue

			# check if the cache is for the host
			hostname, time_ext = cache_file.split('_-_')
			save_time,_ = time_ext.split('.') 

			# calc the age of the cache
			age = int(self.now) - int(save_time)

			# overwrite the current queue if it's for the host and the cache is not too old
			if hostname == self.cache_name.split('_-_')[0] and age < self.cache_ttl:
				file_name = os.path.join(self.cache_dir, cache_file)
				try:
					with open(file_name, 'rb') as f:
						data = pickle.load(f)
						for path in data:
							self.__setitem__(path, data[path])
				except:
					print('Error loading cache: ' +  file_name)
