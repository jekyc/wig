import concurrent.futures
import hashlib
import re
import string
import random
import urllib.request
import urllib.parse
from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
	def __init__(self):
		self.reset()
		self.strict = False
		self.convert_charrefs = True
		self.tagtext = []
	def handle_data(self, d):
		self.tagtext.append(d)
	def get_tagtext(self):
		return ''.join(self.tagtext)


def _clean_page(page):
	# this the same method nmap's http.lua uses for error page detection
	# nselib/http.lua: clean_404
	# remove information from the page that might not be static
	
	# time
	page = re.sub(b'(\d?\d:?){2,3}', b'',page)
	page = re.sub(b'AM', b'',page, flags=re.IGNORECASE)
	page = re.sub(b'PM', b'',page, flags=re.IGNORECASE)
	page = re.sub(b'(\d){13}', b'', page) # timestamp

	# date with 4 digit year
	page = re.sub(b'(\d){8}', '',page)
	page = re.sub(b'\d{4}-\d{2}-\d{2}', b'',page)
	page = re.sub(b'\d{4}/\d{2}/\d{2}', b'',page)
	page = re.sub(b'\d{2}-\d{2}-\d{4}', b'',page)
	page = re.sub(b'\d{2}/\d{2}/\d{4}', b'',page)

	# date with 2 digit year
	page = re.sub( b'(\d){6}', '',page)
	page = re.sub( b'\d{2}-\d{2}-\d{2}', b'',page)
	page = re.sub( b'\d{2}/\d{2}/\d{2}', b'',page)
	
	# links and paths
	page = re.sub( b'/[^ ]+',  b'', page)
	page = re.sub( b'[a-zA-Z]:\\[^ ]+',  b'', page)

	# return the fingerprint of the stripped page 
	return hashlib.md5(page).hexdigest().lower()


def _create_response(response):
	R = Response()

	url = response.geturl()
	response_info = urllib.request.urlparse(url)
	body = response.read()

	# get the page text only
	parser = HTMLStripper()
	parser.feed(body.decode('utf-8', 'ignore'))
	page_text = parser.get_tagtext()

	R.set_body(body)
	R.protocol = response_info.scheme
	R.host = response_info.netloc
	R.url = url
	R.status = {'code': response.code, 'text': response.reason}
	R.headers = {pair[0].lower():pair[1] for pair in response.getheaders()}
	R.md5 = hashlib.md5(body).hexdigest().lower()
	R.md5_404 = _clean_page(body)
	R.md5_404_text = _clean_page(page_text.encode('utf-8', 'ignore'))

	return(R)


#######################################################################
#
# Override urllib.request classes
#
#######################################################################

class OutOfScopeException(Exception):
	def __init__(self, org_url, new_url):
		self.original_netloc = org_url.netloc
		self.new_netloc = new_url.netloc

	def __str__(self):
		return repr( "%s is not in scope %s" % (self.new_netloc, self.original_netloc)  )


class UnknownHostName(Exception):
	def __init__(self, url):
		self.url = url

	def __str__(self):
		return "Unknown host: %s" % (self.url,)


class ErrorHandler(urllib.request.HTTPDefaultErrorHandler):
	def http_error_default(self, req, fp, code, msg, hdrs):
		return(fp)


class RedirectHandler(urllib.request.HTTPRedirectHandler):
	"""
	This currently only checks if the redirection netloc is 
	the same as the the netloc for the request.

	NOTE: this is very strict, as it will not allow redirections
	      from 'example.com' to 'www.example.com' 
	"""

	def http_error_302(self, req, fp, code, msg, headers):
		if 'location' in headers:
			org_url = urllib.request.urlparse(req.get_full_url())
			new_url = urllib.request.urlparse(headers['location'])

			# if the location starts with '/' the path is relative
			if headers['location'].startswith('/'):
				new_url = new_url._replace(scheme=org_url.scheme, netloc=org_url.netloc)

			if not new_url.netloc == org_url.netloc:
				raise OutOfScopeException(org_url, new_url)

		# call python's built-in redirection handler
		return urllib.request.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)

	http_error_301 = http_error_303 = http_error_307 = http_error_302


#######################################################################
#
# Custom request and response classes
#
#######################################################################

class Response:
	"""
	This is object is used to store response information

	The normal http.client.HTTPResponse cannot be pickled
	which is used in the caching process
	"""

	def __init__(self):
		self.url = ''
		self.protocol = ''
		self.host = ''
		self.status = {}
		self.headers = {}
		self.body = ''

		self.md5 = None
		self.md5_404 = None
		self.should_be_error_page = False

		self.crawled_response = False

		chars = string.ascii_uppercase + string.digits
		self.id = ''.join(random.choice(chars) for _ in range(16))


	def get_url(self):
		url_data =  urllib.request.urlparse(self.url)

		if url_data.scheme == '': url_data._replace(scheme=self.protocol)
		if url_data.netloc == '': url_data._replace(netloc=self.host)

		return url_data.geturl()


	def set_body(self, body):
		# check if the encoding is specified in the http header
		content_type = 'Content-Type'.lower()

		if content_type not in self.headers:
			self.body = str(body, errors='replace')

		else:
			# find content-type definitions
			content_types = {'text': False, 'charset': None}
			
			for item in self.headers[content_type].split(';'):
				if 'text' in item:
					content_types['text'] = True

				if 'charset' in item:
					content_types['charset'] = item.split('=')[1]

			# set the encoding to use
			if content_types['charset'] is not None:
				self.body = str(body, content_types['charset'], errors='replace')
			elif content_types['text']:
				self.body = str(body, 'ISO-8859-1', errors='replace')
			else:
				self.body = str(body, errors='replace')
		

	def __repr__(self):
		def get_string(r):
			string = r.url + '\n'
			string += '%s %s\n' %(r.status['code'], r.status['text'])
			string += '\n'.join([header +': '+ r.headers[header] for header in r.headers])
			string += '\n\n'
			string += 'MD5:            ' + self.md5 + '\n'
			string += 'MD5 Error page: ' + self.md5_404 + '\n'
			return string 

		return get_string(self)
		

class Requester:
	def __init__(self, options, data):
		self.threads = options['threads']
		self.proxy = options['proxy']
		self.user_agent = options['user_agent']

		self.data = data
		self.cache = data['cache']
		self.requested = data['requested']
		self.printer = data['printer']

		self.is_redirected = False
		self.find_404s = False
		self.fingerprintQueue = None

		self.url_data = urllib.request.urlparse(options['url'])
		if options['prefix']:
			self.url_data.path = options['prefix'] + self.url_data.path
		self.url = urllib.request.urlunparse(self.url_data)

	def _create_fetcher(self, redirect_handler=True):
		args = [ErrorHandler]
		if self.proxy == None:
			args.append(urllib.request.ProxyHandler({}))
		elif not self.proxy == False:
			protocol = self.url_data.scheme
			args.append(urllib.request.ProxyHandler({protocol: self.proxy}))

		if redirect_handler:
			args.append(RedirectHandler)
		
		opener = urllib.request.build_opener(*args)
		opener.addheaders = [('User-agent', self.user_agent)]
		return opener

	def detect_redirect(self):
		parse = urllib.request.urlparse

		# the original url
		org_url = self.url_data

		# get an opener doing redirections 
		try:
			opener = self._create_fetcher(redirect_handler=False)
			response = opener.open(self.url)
		except:
			raise UnknownHostName(self.url)	

		# the new url
		new_url = parse(response.geturl())

		# detect a redirection
		new_loc = new_url.scheme + '://' + new_url.netloc
		org_loc = org_url.scheme + '://' + org_url.netloc

		self.is_redirected = not(new_loc == org_loc)

		if self.is_redirected:
			self.printer.print_debug_line('%s redirects to %s' % (org_loc, new_loc),2)
		else:
			self.printer.print_debug_line('%s does not redirect' % (org_loc, ), 2)

		# create an response object and add it to the cache
		R = _create_response(response)
		self.cache[new_loc] = R
		self.cache[self.url] = R

		return (self.is_redirected, new_loc)

	def do_request(self, url, run_type=None, method='GET'):
		opener = self._create_fetcher()
		request = urllib.request.Request(url, method=method)
		response = opener.open(request)
		R = _create_response(response)
		
		if run_type == 'DiscoverMore':
			R.crawled_response = True	

		self.cache[url] = R
		self.cache[response.geturl()] = R

		return response


	def request(self, fp_list, run_type):
		url = fp_list[0]['url']
		complete_url = urllib.parse.urljoin(self.url, url)

		R = None

		# check if the url is out of scope
		url_data = urllib.parse.urlparse(complete_url)
		host_data = urllib.parse.urlparse(self.url)
		
		# check if it is possible to use 'HEAD' instead of 'GET'
		# this should be possible for all fingerprints, that do not
		# have a specified a 'code' or 'code' is '200'.
		# if 'code' is 'any' or something other than '200', the 
		# resource should be fetched.
		can_use_head = True
		for fp in fp_list:
			if 'code' in fp and (fp['code'] == 'any' or fp['code'] != 200):
				can_use_head = False

		if not url_data.netloc == host_data.netloc:
			pass

		elif not complete_url in self.cache:
			try:
				# if it is possible to use 'HEAD', use it. If the result is 
				# a '200', request the resource with a 'GET'
				get_resource = True
				if can_use_head:
					response = self.do_request(complete_url, run_type, method='HEAD')
					if not response.code == 200:
						get_resource = False

				# Fetch the ressource if the resource exists or 
				# if the fingerprint requires any response
				if get_resource:
					self.do_request(complete_url, run_type, method='GET')
					R = self.cache[complete_url]
			
			except Exception as e:
				pass
		else:
			R = self.cache[complete_url]

		return (fp_list, R)


	def run(self, run_type=None, fp_lists=[]):
		with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
			future_list = []

			for fp_list in fp_lists:
				future_list.append(executor.submit(self.request, fp_list, run_type))
				
			for future in concurrent.futures.as_completed(future_list):
				self.requested.put(future.result())

		return self.requested