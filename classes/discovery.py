import re, hashlib, pprint, socket, urllib, time
import urllib.request
from queue import Queue
from collections import Counter, deque, defaultdict
from html.parser import HTMLParser
from classes.fingerprints import Fingerprints
#from classes.requester2 import Requester
from classes.matcher import Match
from classes.request2 import Response, Requester
from classes.printer import Printer

class DiscoverAllCMS(object):
	# match all fingerprints against all responses
	# this might generate false positives

	def __init__(self, data):
		self.cache = data['cache']
		self.results = data['results']
		self.matcher = data['matcher']
		self.fps = data['fingerprints']
		self.printer = data['printer']

		# only used for pretty printing of debugging info
		self.tmp_set = set()

	def run(self):
		self.printer.print('Checking for more matches in cache (option -a)  ...', 1)

		# find matches for all the responses in the cache
		for fp_category in ['cms', 'platform']:
			for fp_type in self.fps.data[fp_category]:
				fps = self.fps.data[fp_category][fp_type]['fps']

				for response in self.cache.get_responses():
					matches = self.matcher.get_result(fps, response)
					for fp in matches:
						self.results.add( fp_category, fp['name'], fp['output'], fp )

						if (fp['name'], fp['output']) not in self.tmp_set:
							self.printer.print('- Found match: %s %s' % (fp['name'], fp['output']) , 2)

						self.tmp_set.add((fp['name'], fp['output']))


class DiscoverCMS(object):

	def __init__(self, options, data):
		self.printer = data['printer']
		self.matcher = data['matcher']
		self.requester = data['requester']
		self.result = data['results']
		self.printer = data['printer']

		self.batch_size = options['batch_size']
		self.num_cms_to_find = options['stop_after']
		self.find_all_cms = options['run_all']

		# only used for pretty printing of debugging info
		self.tmp_set = set()

		self.queue = defaultdict(list)
		for fp_type in data['fingerprints'].data['cms']:
			for fp in data['fingerprints'].data['cms'][fp_type]['fps']:
				self.queue[fp['url']].append(fp)



	def get_queue(self, cms=None):
		queue = []
		if cms is None:
			for i in range(self.batch_size):
				try:
					url, fp_list = self.queue.popitem()
					queue.append(fp_list)
				except KeyError:
					break
		else:
			# the following procedure is *not* optimal
			# the self.queue dict is completely destroyed and 
			# and rebuilt each time this procedure is called :(

			# create a temp queue dict
			tmp_queue = defaultdict(list)
			
			# remove elements from the dict until it is empty
			while len(self.queue) > 0:
				url, fp_list = self.queue.popitem()

				# remove all the elements of a queue entry's list
				# one-by-one and check if the fingerprints are
				# belong to the specified 'cms'
				tmp_list = []
				out_list = []
				
				while len(fp_list) > 0:
					# remove the fingerprint
					fp = fp_list.pop()

					# if the fingerprint matches the cms, add it to the 
					# out_list for the current url
					# otherwise add it to the tmp_list
					if fp['name'] == cms: 
						out_list.append(fp)
					else:
						tmp_list.append(fp)

				# if there are elements in tmp_list (the new list of fps that
				# that do *not* match the 'cms'), add it to the tmp_queue's entry
				# for the current url
				if len(tmp_list) > 0:
					tmp_queue[url].extend(tmp_list)

				# if matches for the specified cms have been found, add the list
				# to the fingerprintQueue for the requester
				if len(out_list) > 0:
					queue.append(out_list)

			# replace the queue with the tmp queue
			self.queue = tmp_queue

		return queue



	def run(self):
		batch_no = 0
		self.printer.print('Determining CMS type ...', 1)

		detected_cms = []
		stop_searching = len(detected_cms) >= self.num_cms_to_find

		while (not stop_searching or self.find_all_cms) and (not len(self.queue) == 0):
			self.printer.print('Checking fingerprint group no. %s ...' % (batch_no, ) , 3)

			# set the requester queue
			results = self.requester.run('CMS', self.get_queue())
			
			# search for CMS matches
			cms_matches = []
			while not results.empty():
				fingerprints, response = results.get()

				for fp in self.matcher.get_result(fingerprints, response):
					self.result.add( 'cms', fp['name'], fp['output'], fp)
					cms_matches.append(fp['name'])
		
			# search for the found CMS versions
			for cms in cms_matches:

				# skip checking the cms, if it has already been detected
				if cms in detected_cms: continue

				if cms not in self.tmp_set:
					self.tmp_set.add(cms)
					self.printer.print('- Found CMS match: %s' % (cms, ) , 2)

				# set the requester queue with only fingerprints for the cms
				results = self.requester.run('CMS_version', self.get_queue(cms))

				# find the results
				self.printer.print('Determining CMS version ...', 1)
				while results.qsize() > 0:
					res_fps,response = results.get()
					for fp in self.matcher.get_result(res_fps, response):
						self.result.add( 'cms', fp['name'], fp['output'], fp)

						if (fp['name'], fp['output']) not in self.tmp_set:
							self.tmp_set.add((fp['name'], fp['output']))
							self.printer.print('- Found version: %s %s' % (fp['name'], fp['output']) , 2)


				# update the stop criteria
				detected_cms.append(cms)
			
			stop_searching = (len(detected_cms) >= self.num_cms_to_find) or len(self.queue) == 0
			batch_no += 1



class DiscoverCookies(object):

	def __init__(self, data):
		self.data = data
		self.printer = data['printer']

	def run(self):
		self.printer.print('Checking for cookies ...' , 1)

		cookies = set()
		for r in self.data['cache'].get_responses():
			try:
				c = r.headers['set-cookie'].strip().split('=')[0]
				if c not in cookies:
					self.printer.print('- Found cookie: %s' % (c,) , 2)
				
				cookies.add(c)

			except:
				pass

		self.data['results'].site_info['cookies'] = cookies


class DiscoverErrorPage:
	# find error pages on the site
	# the requester has a built-in list of items and patterns
	# to remove before calculating a checksum of pages that
	# should not exists

	def __init__(self, options, data):
		self.host = options['url']
		self.fps = data['fingerprints'].data['error_pages']['fps']
		self.requester = data['requester']
		self.printer = data['printer']


	def run(self):
		self.requester.find_404s = True

		self.printer.print('Error page detection ...', 1)

		queue = [[fp] for fp in self.fps]
		results = self.requester.run('ErrorPages', queue)

		error_pages = set()
		while results.qsize() > 0:
			fp, response = results.get()
			if response is not None:
				error_pages.add(response.md5_404)
				error_pages.add(response.md5_404_text)
				self.printer.print('- Error page fingerprint: %s, %s - %s' % (response.md5_404, response.md5_404_text, fp[0]['url']), 2)

		self.requester.find_404s = False

		return error_pages

		
class DiscoverInteresting(object):
	def __init__(self, options, data):
		self.url = options['url']
		self.printer = data['printer']
		self.requester = data['requester']
		self.matcher = data['matcher']
		self.result = data['results']
		self.error_pages = data['error_pages']
		self.cache = data['cache']
		self.category = "interesting"

		# add the fingerprints to the queue, ensuring that
		# all fps with the same url, are collected in a list
		self.queue = defaultdict(list)
		for fp in data['fingerprints'].data['interesting']['fps']:
			self.queue[fp['url']].append(fp)


	def run(self):
		self.printer.print('Detecting interesting files ...', 1)

		# process the results
		results = self.requester.run('Interesting', list(self.queue.values()))
		
		while results.qsize() > 0:
			fps,response = results.get()
			
			# if the response includes a 404 md5, check if the response
			# is a redirection to a known error page
			# this is a fix for https://github.com/jekyc/wig/issues/7
			if response.md5_404 is not None:
				redirected = response.md5_404 in self.error_pages
				redirected = redirected or (response.md5_404_text in self.error_pages)
				redirected = redirected or (response.md5_404_text == self.cache[self.url].md5_404_text)

				# if it is an error page, skip it
				if redirected: continue

			# if the response does not have a 404 md5, something most have gone wrong
			# skip checking the page
			else:
				continue

			for fp in self.matcher.get_result(fps, response):
				self.result.add( self.category, None, None, fp, weight=1)
				try:
					self.printer.print('- Found file: %s (%s)' % (fp['url'], fp['note'] ), 2)
				except:
					pass


class DiscoverIP(object):

	def __init__(self, path):
		self.path = path

	def run(self):

		try:
			hostname = self.path.split('//')[1]
			hostname = hostname.split('/')[0]
			ip = socket.gethostbyname(hostname)
		except Exception as e:
			#print(e)
			ip = 'Unknown'

		return ip


class DiscoverJavaScript(object):
	def __init__(self, options, data):
		self.printer = data['printer']
		self.cache = data['cache']
		self.matcher = data['matcher']
		self.result = data['results']

		self.fingerprints = []
		for fp_type in data['fingerprints'].data['js']:
			self.fingerprints.extend(data['fingerprints'].data['js'][fp_type]['fps'])


	def run(self):
		self.printer.print('Detecting Javascript ...', 1)
		for response in self.cache.get_responses():
			
			# match only if the response is JavaScript
			#  check content type
			content_type = response.headers['content-type'] if 'content-type' in response.headers else ''
			# and extension
			is_js = 'javascript' in content_type or '.js' in response.url.split('.')[-1]

			# if the response is JavaScript try to match it to the known fingerprints 
			if is_js:
				matches = self.matcher.get_result(self.fingerprints, response)
				for fp in matches:
					self.result.add( 'js', fp['name'], fp['output'], fingerprint=fp, weight=1)
			
					self.printer.print('- Found JavaScript: %s %s' % (fp['name'], fp['output']), 2)



# Used by the DiscoverMore crawler
# The
class LinkExtractor(HTMLParser):
	def __init__(self, strict):
		super().__init__(strict=strict)
		self.results = set()

	def get_results(self):
		return self.results

	def handle_starttag(self, tag, attrs):
		try:
			url = ''
			if tag == 'script' or tag == 'img':
				for attr in attrs: 
					if attr[0] == 'src':  
						self.results.add(attr[1])
			if tag == 'link':
				for attr in attrs: 
					if attr[0] == 'href': 
						self.results.add(attr[1])
		except:
			pass



class DiscoverMore(object):

	def __init__(self, options, data):
		self.host = options['url']
		self.threads = options['threads']
		self.printer = data['printer']
		self.cache = data['cache']
		self.result = data['results']
		self.matcher = data['matcher']
		self.requester = data['requester']
		self.fingerprints = data['fingerprints']


	def _get_urls(self, response):
		# only get urls from elements that use 'src' to avoid 
		# fetching resources provided by <a>-tags, as this could
		# lead to the crawling of the whole application
		regexes = [ 'src="(.+?)"', "src='(.+?)'"]

		urls = set()
		for regex in regexes:
			for match in re.findall(regex, response.body):
				urls.add( match )

		return urls

	
	def run(self):
		self.printer.print('Detecting links ...', 1)
		resources = set()
		parser = LinkExtractor(strict=False)

		for req in self.cache.get_responses():
			# skip pages that do not set 'content-type'
			# these might be binaries
			if not 'content-type' in req.headers:
				continue

			# only scrape pages that can contain links/references
			if 'text/html' in req.headers['content-type']:
				tmp = self._get_urls(req)

				parser.feed(req.body)
				tmp = tmp.union( parser.get_results())

				for i in tmp:
					url_data = urllib.request.urlparse(i)

					# skip data urls
					if url_data.path.startswith('data:'): continue

					resources.add( i )

		# the items in the resource set should mimic a list of fingerprints:
		# a fingerprint is a dict with at least an URL key
		self.printer.print('- Discovered %s new resources' % (len(resources), ), 2)

		# prepare the urls
		queue = defaultdict(list)
		for url in resources: 
			queue[url].append({'url': url})

		
		# fetch'em
		results = self.requester.run('DiscoverMore', list(queue.values()))


class DiscoverOS:
	def __init__(self, options, data):
		self.printer = data['printer']
		self.cache = data['cache']
		self.results = data['results']
		self.fingerprints = data['fingerprints'].data['os']['fps']

		self.os = Counter()
		self.os_family_list = Counter()
		self.matched_packages = set()

	
	def search_and_prioritize_os(self, pkg_name, pkg_version):
		for fp in self.fingerprints:
			if fp['pkg_name'] == pkg_name and fp['pkg_version'] == pkg_version:
				weight = 1 if not 'weight' in fp else fp['weight']

				if not type(fp['os_version']) == type([]):
					fp['os_version'] = [fp['os_version']]

				for os_version in fp['os_version']:
					if fp['os_name'].lower() in self.os_family_list:
						self.printer.print('- Prioritizing fingerprints for OS: %s' % (fp['os_name'], ), 7)
						self.os[ (fp['os_name'], os_version) ] += weight * 100
					else:
						self.os[ (fp['os_name'], os_version) ] += weight


	def find_match_in_headers(self, response):
		headers = response.headers
		if 'server' in headers:
			line = headers['server']
			
			if "(" in line:
				os = line[line.find('(')+1:line.find(')')]
				line = line[:line.find('(')-1] + line[line.find(')')+1: ]
			else:
				os = None

			if os is not None:
				self.os_family_list[os.lower()] += 1

			for part in line.split(" "):
				try:
					pkg,version = list(map(str.lower, part.split('/')))
					self.search_and_prioritize_os(pkg, version)

				except Exception as e:
					continue

	
	def find_match_in_results(self):
		platforms = self.results.scores['platform']
		
		for pkg in platforms:
			for version in platforms[pkg]:
				# hack for asp.net
				if pkg == 'ASP.NET':
					version = version[:3] if not version.startswith("4.5") else version[:5]

				self.search_and_prioritize_os(pkg, version)


	def finalize(self):
		# add OS to results: self.os: {(os, version): weight, ...}
		results = []
		for p in self.os:
			results.append({'version': p[1], 'os': p[0], 'count': self.os[p]})

		if len(results) == 0: return

		prio = sorted(results, key=lambda x:x['count'], reverse=True)
		max_count = prio[0]['count']
		for i in prio:
			if i['count'] == max_count:
				self.results.add('os', i['os'], i['version'], weight=i['count'])
				self.printer.print('- Found OS: %s %s' % (i['os'], i['version']), 2)
			else:
				break


	def run(self):
		self.printer.print('Detecting OS ...', 1)
		headers = set()
		responses = self.cache.get_responses()
		
		# find matches in the header
		for response in responses:
			self.find_match_in_headers(response)

		# find match in current results
		self.find_match_in_results()

		# do some house keeping
		self.finalize()




class DiscoverPlatform:

	def __init__(self, options, data):
		self.printer = data['printer']
		self.requester = data['requester']
		self.matcher = data['matcher']
		self.result = data['results']
		self.printer = data['printer']

		self.threads = options['threads']
		self.batch_size = options['batch_size']
		
		self.queue = defaultdict(list)
		for fp_type in data['fingerprints'].data['platform']:
			for fp in data['fingerprints'].data['platform'][fp_type]['fps']:
				self.queue[fp['url']].append(fp)

		# only used for pretty printing of debugging info
		self.tmp_set = set()
			
	def run(self):
		self.printer.print('Detecting platform ...', 1)
		
		while len(self.queue) > 0:
			queue = []
			for i in range(self.batch_size):
				try:
					url, fp_list = self.queue.popitem()
					queue.append(fp_list)
				except KeyError:
					break

			results = self.requester.run('Plaform', queue)
			
			# search for CMS matches
			while not results.empty():
				fingerprints, response = results.get()
				matches = self.matcher.get_result(fingerprints, response)
				for fp in matches:
					self.result.add('platform', fp['name'], fp['output'], fp)

					if (fp['name'], fp['output']) not in self.tmp_set:
						self.printer.print('- Found platform %s %s' % (fp['name'], fp['output']), 2)

					self.tmp_set.add((fp['name'], fp['output']))



class DiscoverTitle:

	def __init__(self, options, data):
		self.data = data
		self.url = options['url']
		self.printer = data['printer']

	def run(self):
		self.printer.print('Getting title ...', 1)

		r = self.data['requester'].run('Title', [[{'url': '/'}]])

		front_page = self.data['cache'][self.url]

		try:
			title = re.findall('<title>\s*(.*)\s*</title>', front_page.body)[0]
			title = title.strip()
		except:
			title = ''

		try:
			self.printer.print('- Found title: %s' % (title, ), 2)
		except:
			pass

		return title


class DiscoverTools:
	def __init__(self, data):
		self.fps = data['fingerprints']
		self.results = data['results']
		self.printer = data['printer']


	def run(self):
		self.printer.print('Searching for tools ...', 1)
		cms_results = self.results.get_versions()

		# loop over the cms' in the results
		for cms,_ in cms_results:
			# loop over all the translations
			for fn in self.fps.translator:
				# check if the translated name is the same as the cms
				if self.fps.translator[fn]['name'] == cms and 'tool' in self.fps.translator[fn]:
					for tool in self.fps.translator[fn]['tool']:
						self.results.add_tool(cms, tool['name'], tool['link'])
						self.printer.print('- Found tool: %s (%s)' % (tool['name'], tool['link']), 2)



class DiscoverUrlLess(object):
	def __init__(self, options, data):
		self.printer = data['printer']
		self.cache = data['cache']
		self.results = data['results']
		self.matcher = data['matcher']
		self.fingerprints = data['fingerprints']


	def run(self):
		self.printer.print('Matching urlless fingerprints...', 1)
		
		# only used for pretty printing of debugging info
		tmp_set = set()

		for fp_category in ['cms', 'platform']:
			for fp_type in self.fingerprints.data[fp_category]:
				fps = self.fingerprints.data[fp_category][fp_type]['fps']
				fps = [fp for fp in fps if fp['url'] == '']

				# find matches for all the responses in the cache
				for response in self.cache.get_responses():
					matches = self.matcher.get_result(fps, response)
					for fp in matches:
						
						url_data = urllib.request.urlparse(response.get_url())
						fp['url'] = url_data.path
							

						show_all_detections = True
						if 'show_all_detections' in fp:
							show_all_detections = fp['show_all_detections']

						if (fp['name'], fp['output']) in tmp_set:
							if show_all_detections:
								self.results.add(fp_category, fp['name'], fp['output'], fingerprint=fp, weight=1)

						else:
							self.printer.print('- Found fingerprint: %s %s' % (fp['name'], fp['output']), 2)
							self.results.add(fp_category, fp['name'], fp['output'], fingerprint=fp, weight=1)
						
						tmp_set.add((fp['name'], fp['output']))


	

class DiscoverVulnerabilities:
	def __init__(self, data):
		self.printer = data['printer']
		self.results = data['results']
		self.fps = []

		vuln_sources = data['fingerprints'].data['vulnerabilities']

		for source in vuln_sources:
			self.fps.extend(data['fingerprints'].data['vulnerabilities'][source]['fps'])


	def run(self):
		self.printer.print('Searching for vulnerabilities ...', 1)

		cms_results = self.results.get_versions()

		vendors = Counter()
		for r in cms_results: vendors[r[0]] += 1

		# if there are more than 5 results,
		# skip displaying vuln count, as the 
		# results are unreliable
		for cms, version in cms_results:
			if vendors[cms] > 5: continue

			try:
				for fp in self.fps:
					if fp['name'] == cms and fp['version'] == version:
						self.results.add_vulnerabilities(cms, version, fp['num_vulns'], fp['link'])
						self.printer.print('- Found vulnerability: %s %s: %s' % (cms, version, fp['num_vulns']), 2)

			except Exception as e:
				print(e)
				pass
