import queue
import threading
import time
import hashlib
import sys
import re
import string
import random
import urllib.request

from collections import namedtuple
from classes.cache import Cache
from classes.results import Results


def _clean_page(page):
	# this the same method nmap's http.lua uses for error page detection
	# nselib/http.lua: clean_404
	# remove information from the page that might not be static
	
	# time
	page = re.sub(b'(\d?\d:?){2,3}', b'',page)
	page = re.sub(b'AM', b'',page, flags=re.IGNORECASE)
	page = re.sub(b'PM', b'',page, flags=re.IGNORECASE)

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

	R.set_body(body)
	R.protocol = response_info.scheme
	R.host = response_info.netloc
	R.url = url
	R.status = {'code': response.code, 'text': response.reason}
	R.headers = {pair[0].lower():pair[1] for pair in response.getheaders()}
	R.md5 = hashlib.md5(body).hexdigest().lower()
	R.md5_404 = _clean_page(body)

	return(R)


#######################################################################
#
# Override urllib.request classes
#
#######################################################################

class OutOfScopeException(Exception):
	def __init__(self, org_url, new_url):
		self.original_netloc = org_url
		self.new_netloc = new_url

	def __str__(self):
		return repr( "%s is not in scope %s" % (self.new_netloc, self.original_netloc)  )


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
			new_url = urllib.request.urlparse(headers['location'])
			org_url = urllib.request.urlparse(req.get_full_url())

			if new_url.netloc is not org_url.netloc:
				raise OutOfScopeException(org_url.netloc, new_url.netloc)

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

		self.md5 = ''
		self.md5_404 = ''
		self.should_be_error_page = False

		chars = string.ascii_uppercase + string.digits
		self.id = ''.join(random.choice(chars) for _ in range(16))


	def get_url(self):
		return self.protocol + '://' + self.host + self.url


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
			string = r.protocol + '://' + r.host + r.url + '\n'
			string += '%s %s\n' %(r.status['code'], r.status['text'])
			string += '\n'.join([header +': '+ r.headers[header] for header in r.headers])
			string += '\n\n'
			string += 'MD5:            ' + self.md5 + '\n'
			string += 'MD5 Error page: ' + self.md5_404 + '\n'
			return string 

		return get_string(self)
		


class RequesterThread(threading.Thread):
	def __init__(self, id, data, opener):
		threading.Thread.__init__(self)
		self.id = id
		self.kill = False
		self.queue = data['queue']
		self.cache = data['cache']
		self.requested = data['requested']
		self.opener = opener


	def make_request(self, item):
		url = item['url']
		R = None

		if not url in self.cache:
			try:
				request = urllib.request.Request(url)
				response = self.opener.open(request)

				R = _create_response(response)

				self.cache[url] = R
				self.cache[response.geturl()] = R

			except Exception as e:
				# print(e)
				pass
		else:
			R = self.cache[url]

		return R


	def run(self):
		while not self.kill:
			item = self.queue.get()

			if item is None:
				self.queue.task_done()
				break

			response = self.make_request(item)
			if response is None:
				self.queue.task_done()
				continue

			self.requested.put( (item['fps'], response ) )
			self.queue.task_done()



class Requester:
	def __init__(self, options, data):
		self.threads = None
		self.workers = []
		self.is_redirected = False

		self.url_data = urllib.request.urlparse(options['url'])
		if options['prefix']:
			self.url_data.path = options['prefix'] + self.url_data.path
		self.url = urllib.request.urlunparse(self.url_data)

		self.find_404s = False

		self.data = data
		self.cache = data['cache']
		self.queue = data['queue']
		self.requested = data['requested']
		self.printer = data['printer']

		self.proxy = options['proxy']
		self.user_agent = options['user_agent']

	
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


	# set the fingerprints for the requester to get.	
	# fps should be a list of lists of fingerprints:
	# [ [fp, fp, fp], [fp, fp, ...], ...]
	# each fingerprinter in the innerlist must have the same URL
	# The number of elements in the outer list equals the number
	# of threads used
	def set_fingerprints(self, fps):
		self.fps = fps
		self.threads = len(fps)


	def set_find_404(self, find_404s):
		self.find_404s = find_404s


	def set_url(self, url):
		self.url = url


	def detect_redirect(self):
		parse = urllib.request.urlparse

		# the original url
		org_url = self.url_data

		# get an opener doing redirections 
		opener = self._create_fetcher(redirect_handler=False)
		response = opener.open(self.url)

		# the new url
		new_url = parse(response.geturl())

		# detect a redirection
		new_loc = new_url.scheme + '://' + new_url.netloc
		org_loc = org_url.scheme + '://' + org_url.netloc
		self.is_redirected = not(new_loc == org_loc)

		if self.is_redirected:
			self.printer.print('%s redirects to %s\n' % (org_loc, new_loc), 2, '')
		else:
			self.printer.print('%s does not redirect\n' % (org_loc, ), 2, '')

		# create an response object and add it to the cache
		R = _create_response(response)
		self.cache[response.geturl()] = R
		self.cache[self.url] = R

		return (self.is_redirected, response.geturl())


	def run(self):

		for fp_list in self.fps:
			self.queue.put({ "url": self.url + fp_list[0]['url'], "fps": fp_list })

		# add 'None' to queue - stops threads when no items are left
		for i in range(self.threads): self.queue.put( None )

		# start the threads
		self.works = []
		for i in range(self.threads):
			w = RequesterThread(i, self.data, self._create_fetcher())
			w.daemon = True
			self.workers.append(w)
			w.start()

		# join when all work is done
		self.queue.join()

		# the define_404 should only be true during the 
		# preprocessing. 
		if not self.find_404s:
			return self.requested

		# if the define_404 flag is set, then the 
		# supplied URLs are to be used for identification of 404 
		# pages
		else:
			error_pages = queue.Queue()
			while self.requested.qsize() > 0:
				_,response = self.requested.get()
				error_pages.put((response.md5_404, response.url))

			return error_pages