"""
Collection of classes to extract information from the site.

"""

import re
import socket
import urllib
import urllib.request
from collections import Counter, defaultdict
from html.parser import HTMLParser

class DiscoverAllCMS:
	"""
	Match all fingerprints against all responses
	this might generate false positives
	"""
	def __init__(self, data):
		self.cache = data['cache']
		self.results = data['results']
		self.matcher = data['matcher']
		self.fps = data['fingerprints']
		self.printer = data['printer']

		# only used for pretty printing of debugging info
		self.tmp_set = set()

	def run(self):
		self.printer.print_debug_line('Checking for more matches in cache (option -a)  ...', 1)

		# find matches for all the responses in the cache
		for fp_category in ['cms', 'platform']:
			for fp_type in self.fps.data[fp_category]:
				fps = self.fps.data[fp_category][fp_type]['fps']

				for response in self.cache.get_responses():
					matches = self.matcher.get_result(fps, response)
					for fp in matches:
						self.results.add_version(fp_category, fp['name'], fp['output'], fp)

						if (fp['name'], fp['output']) not in self.tmp_set:
							self.printer.print_debug_line('- Found match: %s %s' % (fp['name'], fp['output']), 2)

						self.tmp_set.add((fp['name'], fp['output']))


class DiscoverCMS:
	"""
	Search for the CMS and its version.

	It searches for a CMS match by splitting the fingerprints
	into batches of the given size (options['batch_size']).
	One a batch of fingerprints urls have been requested, the
	responses are checked for CMS matches. If a match is found,
	all the URLs for that CMS are requested in order to determine
	the version. If options['run_all'] is set, this continues until
	all fingerprints are checked (this is not the default).

	"""
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
			for _ in range(self.batch_size):
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
				tmp_list, out_list = [], []

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
		self.printer.print_debug_line('Determining CMS type ...', 1)

		detected_cms = []
		stop_searching = len(detected_cms) >= self.num_cms_to_find

		while (not stop_searching or self.find_all_cms) and (not len(self.queue) == 0):
			self.printer.print_debug_line('Checking fingerprint group no. %s ...' % (batch_no, ), 3)

			# set the requester queue
			results = self.requester.run('CMS', self.get_queue())

			# search for CMS matches
			cms_matches = []
			while not results.empty():
				fingerprints, response = results.get()

				for fp in self.matcher.get_result(fingerprints, response):
					self.result.add_version('cms', fp['name'], fp['output'], fp)
					cms_matches.append(fp['name'])

			# search for the found CMS versions
			for cms in cms_matches:

				# skip checking the cms, if it has already been detected
				if cms in detected_cms: continue

				if cms not in self.tmp_set:
					self.tmp_set.add(cms)
					self.printer.print_debug_line('- Found CMS match: %s' % (cms, ), 2)

				# set the requester queue with only fingerprints for the cms
				results = self.requester.run('CMS_version', self.get_queue(cms))

				# find the results
				self.printer.print_debug_line('Determining CMS version ...', 1)
				while results.qsize() > 0:
					res_fps, response = results.get()
					for fp in self.matcher.get_result(res_fps, response):
						self.result.add_version('cms', fp['name'], fp['output'], fp)

						if (fp['name'], fp['output']) not in self.tmp_set:
							self.tmp_set.add((fp['name'], fp['output']))
							self.printer.print_debug_line('- Found version: %s %s' % (fp['name'], fp['output']), 2)

				# update the stop criteria
				detected_cms.append(cms)

			stop_searching = (len(detected_cms) >= self.num_cms_to_find) or len(self.queue) == 0
			batch_no += 1



class DiscoverCookies(object):
	"""
	Check if the site sets any cookies.

	It checks the results in the cache, and therefore
	it should be run last.
	"""
	def __init__(self, data):
		self.data = data
		self.printer = data['printer']

	def run(self):
		self.printer.print_debug_line('Checking for cookies ...', 1)

		cookies = set()
		for r in self.data['cache'].get_responses():
			try:
				c = r.headers['set-cookie'].strip().split('=')[0]
				if c not in cookies:
					self.printer.print_debug_line('- Found cookie: %s' % (c, ), 2)

				cookies.add(c)

			except:
				pass

		self.data['results'].site_info['cookies'] = cookies


class DiscoverSubdomains:
	"""
	Search for sub-domains.

	The current implementation does not wig's requester class
	which means that proxy, threads, user-agent, etc are not
	used. This should implemented, but it should be ensured
	that the cache is not used, as this might impact the results
	of the version detection.
	"""

	def __init__(self, options, data):
		self.data = data
		self.options = options

		self.results = data['results']
		self.subdomains = data['fingerprints'].data['subdomains']['fps']
		self.url = options['url']
		self.printer = data['printer']

		self.domain = urllib.request.urlparse(self.url).netloc
		self.domain = '.'.join(self.domain.split(':')[0].split('.')[-2:])

		self.random_domain = 'random98f092f0b7'
		self.scheme_sets = set([('http', '80'),('https', '443')])

	def check_subdomain(self, subdomain, scheme, port):
		domain = subdomain + '.' + self.domain
		
		try:
			# lookup the IP of the domain
			ip = socket.gethostbyname(domain)
			
			# try to get the title of the site hosted on the domain
			try:
				req = urllib.request.Request(url=scheme + '://' + domain)
				with urllib.request.urlopen(req, timeout=1) as f:
					data = f.read().decode('utf-8')
					title = re.findall(r'<title>\s*(.*)\s*</title>', data)[0].strip()
					result = (scheme + '://' + domain + ":" + port, title, ip)
			except:
				result = None
		except:
			result = None

		return result

	def run(self):
		self.printer.print_debug_line('Searching for sub domains ...', 1)
		
		# check if the site accepts all sub-domains
		control_set = set()
		for scheme, port in self.scheme_sets:
			domain_test = self.check_subdomain(self.random_domain, scheme, port)
			if domain_test:
				control_set.add((domain_test[1], domain_test[2]))

		# check all sub domains
		for subdomain in self.subdomains:
			for scheme, port in self.scheme_sets:
				result = self.check_subdomain(subdomain, scheme, port)
				if result:
					# compare the current results to the control
					if not (result[1], result[2]) in control_set:
						self.results.add_subdomain(*result)


class DiscoverErrorPage:
	"""
	Find error pages on the site.

	The requester has a built-in list of items and patterns
	to remove before calculating a checksum of pages that
	should not exists
	"""
	def __init__(self, options, data):
		self.host = options['url']
		self.fps = data['fingerprints'].data['error_pages']['fps']
		self.requester = data['requester']
		self.printer = data['printer']


	def run(self):
		self.requester.find_404s = True

		self.printer.print_debug_line('Error page detection ...', 1)

		queue = [[fp] for fp in self.fps]
		results = self.requester.run('ErrorPages', queue)

		error_pages = set()
		while results.qsize() > 0:
			fp, response = results.get()
			if response is not None:
				error_pages.add(response.md5_404)
				error_pages.add(response.md5_404_text)
				error_tuple = (response.md5_404, response.md5_404_text, fp[0]['url'])
				self.printer.print_debug_line('- Error page fingerprint: %s, %s - %s' % error_tuple, 2)

		self.requester.find_404s = False

		return error_pages


class DiscoverInteresting(object):
	"""
	Search for commonly interesting files and folders
	"""

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
		self.printer.print_debug_line('Detecting interesting files ...', 1)

		# process the results
		results = self.requester.run('Interesting', list(self.queue.values()))

		while results.qsize() > 0:
			fps, response = results.get()

			# if the response includes a 404 md5, check if the response
			# is a redirection to a known error page
			# this is a fix for https://github.com/jekyc/wig/issues/7
			if response is not None:
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
				self.result.add_version(self.category, None, None, fp, weight=1)
				try:
					self.printer.print_debug_line('- Found file: %s (%s)' % (fp['url'], fp['note']), 2)
				except:
					pass



class DiscoverIP(object):
	"""
	Get the IP address of the host
	"""

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
	"""
	Search for JavaScript
	"""

	def __init__(self, options, data):
		self.printer = data['printer']
		self.cache = data['cache']
		self.matcher = data['matcher']
		self.result = data['results']

		self.fingerprints = []
		for fp_type in data['fingerprints'].data['js']:
			self.fingerprints.extend(data['fingerprints'].data['js'][fp_type]['fps'])


	def run(self):
		self.printer.print_debug_line('Detecting Javascript ...', 1)
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
					self.result.add_version('js', fp['name'], fp['output'], fingerprint=fp, weight=1)
					self.printer.print_debug_line('- Found JavaScript: %s %s' % (fp['name'], fp['output']), 2)



# Used by the DiscoverMore crawler
class LinkExtractor(HTMLParser):
	"""
	Helper class that extracts linked ressources

	Only checks for img, script, and link tags
	"""

	def __init__(self, strict):
		super().__init__(strict=strict)
		self.results = set()

	def get_results(self):
		return self.results

	def handle_starttag(self, tag, attrs):
		try:
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
	"""
	Crawls host to discover more items

	This searches to responses for more items to test.
	This could help detect CMS and version if the default
	paths have been changed. However, it does increase the
	amount of requests send to host
	"""

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
		regexes = ['src="(.+?)"', "src='(.+?)'"]

		urls = set()
		for regex in regexes:
			for match in re.findall(regex, response.body):
				urls.add(match)

		return urls


	def run(self):
		self.printer.print_debug_line('Detecting links ...', 1)
		resources = set()
		parser = LinkExtractor(strict=False)

		for req in self.cache.get_responses():
			# skip pages that do not set 'content-type'
			# these might be binaries
			if not 'content-type' in req.headers:
				continue

			# skip responses that have been discovered
			# with 'DiscoverMore'
			if req.crawled_response:
				continue

			# only scrape pages that can contain links/references
			if 'text/html' in req.headers['content-type']:
				tmp = self._get_urls(req)
				parser.feed(req.body)
				tmp = tmp.union(parser.get_results())

				for i in tmp:
					url_data = urllib.request.urlparse(i)

					# skip data urls
					if url_data.path.startswith('data:'): continue

					resources.add(i)

		# the items in the resource set should mimic a list of fingerprints:
		# a fingerprint is a dict with at least an URL key
		self.printer.print_debug_line('- Discovered %s new resources' % (len(resources), ), 2)

		# prepare the urls
		queue = defaultdict(list)
		for url in resources:
			queue[url].append({'url': url})

		# fetch'em
		results = self.requester.run('DiscoverMore', list(queue.values()))


class DiscoverOS:
	"""
	Try to determine the OS used on the host

	Often Linux/GNU web servers send software package name and version
	in the HTTP header 'server'. These are compared to a database of
	Linux/GNU distributions and their versions.

	ASP.NET is also matched.
	"""

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

			pkg_name_match = fp['pkg_name'].lower() == pkg_name.lower()
			pkg_version_match = fp['pkg_version'].lower() == pkg_version.lower()

			if pkg_name_match and pkg_version_match:
				weight = 1 if not 'weight' in fp else fp['weight']

				if not type(fp['os_version']) == type([]):
					fp['os_version'] = [fp['os_version']]

				for os_version in fp['os_version']:
					if fp['os_name'].lower() in self.os_family_list:
						self.printer.print_debug_line('- Prioritizing fingerprints for OS: %s' % (fp['os_name'], ), 7)
						self.os[(fp['os_name'], os_version)] += weight * 100
					else:
						self.os[(fp['os_name'], os_version)] += weight


	def find_match_in_headers(self, response):
		headers = response.headers
		if 'server' in headers:
			line = headers['server']

			if "(" in line:
				os = line[line.find('(')+1:line.find(')')]

				# hack for RHEL
				if os == 'Red Hat':
					os = 'Red Hat Enterprise Linux'

				line = line[:line.find('(')-1] + line[line.find(')')+1: ]
			else:
				os = None

			if os is not None:
				self.os_family_list[os.lower()] += 1

			for part in line.split(" "):
				try:
					pkg, version = list(map(str.lower, part.split('/')))
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

		prio = sorted(results, key=lambda x: x['count'], reverse=True)
		max_count = prio[0]['count']
		for i in prio:
			if i['count'] == max_count:
				self.results.add_version('os', i['os'], i['version'], weight=i['count'])
				self.printer.print_debug_line('- Found OS: %s %s' % (i['os'], i['version']), 2)
			else:
				break


	def run(self):
		self.printer.print_debug_line('Detecting OS ...', 1)
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
		self.cache = data['cache']
		self.translator = data['fingerprints'].data['translator']['dictionary']

		for fp_type in data['fingerprints'].data['platform']:
			for fp in data['fingerprints'].data['platform'][fp_type]['fps']:
				self.queue[fp['url']].append(fp)

		# only used for pretty printing of debugging info
		self.tmp_set = set()
		self.detected_platforms = defaultdict(lambda: defaultdict(set))


	def run(self):
		self.printer.print_debug_line('Detecting platform ...', 1)

		# search for platform information using the platform fingerprints
		while len(self.queue) > 0:
			queue = []
			for i in range(self.batch_size):
				try:
					url, fp_list = self.queue.popitem()
					queue.append(fp_list)
				except KeyError:
					break

			results = self.requester.run('Plaform', queue)

			# search for Platform matches
			while not results.empty():
				fingerprints, response = results.get()
				matches = self.matcher.get_result(fingerprints, response)

				for fp in matches:
					self.result.add_version('platform', fp['name'], fp['output'], fp)

					if (fp['name'], fp['output']) not in self.tmp_set:
						self.printer.print_debug_line('- Found platform %s %s' % (fp['name'], fp['output']), 2)

					self.tmp_set.add((fp['name'], fp['output']))


		# Look for data in all the response headers ('server') in the cache
		for response in self.cache.get_responses():
			headers = response.headers
			if 'server' not in headers:
				continue

			server_line = headers['server']

			# remove ' (something other)'
			if '(' in server_line:
				server_line = server_line[:server_line.find('(')-1] + server_line[server_line.find(')')+1:]

			for part in server_line.split(" "):
				
				pkg_version = list(map(str.lower, part.split('/')))

				# Example: 'Server: nginx'
				if len(pkg_version) == 1:
					pkg, version = pkg_version[0], ''

				# Example: 'Server: Apache/2.2.12'
				elif len(pkg_version) == 2:
					pkg, version = pkg_version

				# Don't know how to parse this - bailing
				else:
					continue

				# check if the detected software is in the dictionary
				if pkg in self.translator:
					pkg = self.translator[pkg]['name']

				# add the results to the platform results
				self.result.add_version('platform', pkg, version, {'url': response.url, 'type': 'dummy'})



class DiscoverTitle:
	"""
	Get the site title.
	"""

	def __init__(self, options, data):
		self.data = data
		self.url = options['url']
		self.printer = data['printer']

	def run(self):
		self.printer.print_debug_line('Getting title ...', 1)
		self.data['requester'].run('Title', [[{'url': '/'}]])
		front_page = self.data['cache'][self.url]

		try:
			title = re.findall(r'<title>\s*(.*)\s*</title>', front_page.body)[0]
			title = title.strip()
		except:
			title = ''

		try:
			self.printer.print_debug_line('- Found title: %s' % (title, ), 2)
		except:
			pass

		return title


class DiscoverTools:
	"""
	Lists tools that can be used for further information gathering.
	"""

	def __init__(self, data):
		self.translator = data['fingerprints'].data['translator']['dictionary']
		self.results = data['results']
		self.printer = data['printer']

	def run(self):
		self.printer.print_debug_line('Searching for tools ...', 1)

		cms_set = set()

		# loop over the cms' in the results
		for result_object in self.results.results:
			if not type(result_object).__name__ == 'CMS': continue
			cms_set.add(result_object.name)

		for detected_cms in cms_set:
			# loop over all the translations
			for cms_name in self.translator:
				# check if the translated name is the same as the cms
				if self.translator[cms_name]['name'] == detected_cms and 'tool' in self.translator[cms_name]:
					for tool in self.translator[cms_name]['tool']:
						self.results.add_tool(detected_cms, tool['name'], tool['link'])
						self.printer.print_debug_line('- Found tool: %s (%s)' % (tool['name'], tool['link']), 2)


class DiscoverUrlLess:
	"""
	Test fingerprints that don't have a URL.
	"""

	def __init__(self, options, data):
		self.printer = data['printer']
		self.cache = data['cache']
		self.results = data['results']
		self.matcher = data['matcher']
		self.fingerprints = data['fingerprints']


	def run(self):
		self.printer.print_debug_line('Matching urlless fingerprints...', 1)

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
								self.results.add_version(fp_category, fp['name'], fp['output'], fingerprint=fp, weight=1)

						else:
							self.printer.print_debug_line('- Found fingerprint: %s %s' % (fp['name'], fp['output']), 2)
							self.results.add_version(fp_category, fp['name'], fp['output'], fingerprint=fp, weight=1)

						tmp_set.add((fp['name'], fp['output']))


class DiscoverVulnerabilities:
	"""
	Search the database for known vulnerabilities in the
	detected CMS version
	"""

	def __init__(self, data):
		self.printer = data['printer']
		self.results = data['results']
		self.fps = []

		vuln_sources = data['fingerprints'].data['vulnerabilities']

		for source in vuln_sources:
			self.fps.extend(data['fingerprints'].data['vulnerabilities'][source]['fps'])


	def run(self):
		self.printer.print_debug_line('Searching for vulnerabilities ...', 1)


		# if there are more than 5 results,
		# skip displaying vuln count, as the
		# results are unreliable
		for result_object in self.results.results:
			if not type(result_object).__name__ == 'CMS': continue
			cms, version = result_object

			try:
				for fp in self.fps:
					if fp['name'] == cms and fp['version'] == version:
						self.results.add_vulnerabilities(cms, version, fp['num_vulns'], fp['link'])
						error = (cms, version, fp['num_vulns'])
						self.printer.print_debug_line('- Found vulnerability: %s %s: %s' % error, 2)

			except Exception as e:
				print(e)
				pass
