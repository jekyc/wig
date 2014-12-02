import http.client, hashlib, re, string, random

class Request(object):
	def __init__(self):
		self.url = ''
		self.protocol = ''
		self.host = ''
		self.status = {}
		self.headers = {}
		self.body = ''
		self.history = []

		self.md5 = ''
		self.md5_404 = ''
		self.should_be_error_page = False

		chars=string.ascii_uppercase + string.digits
		self.id = ''.join(random.choice(chars) for _ in range(16))


	def get_url(self):
		return self.protocol + '://' + self.host + self.url

	def set_body(self, body):
		# check if the encoding is specified in the http header
		content_type = 'Content-Type'.lower()

		if not content_type in self.headers:
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

		string = ''
		for r in self.history:
			string += get_string(r)

		return string + get_string(self)
		

class PageFetcher(object):
	
	def __init__(self, address, user_agent=None):
		# init the host and protocol
		self.host = None
		self.protocol = 'http' # default to http
		self.path = ''
		self.proto, self.host, self.path = self.get_parts(address)
		self.url = self.proto + '://' + self.host + self.path

		if user_agent == None:
			self.user_agent = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'
		else:
			self.user_agent = user_agent


	def check_out_of_scope(self, host):
		if not (host == self.host or self.host == None):
			# check if the host starts with www
			prefix = 'www.'+host == self.host or host == 'www.' + self.host
			if prefix:
				self.host = host
			else:
				raise Exception("Host is out of scope: %s is not %s" % (host, self.host))

	
	def get_parts(self, address):
		# the address has protocol
		if '://' in address:
			if len(address.split('://')) > 2:
				parts = address.split('://')
				proto = parts[0]
				url = '://'.join(parts[1:])
			else:
				proto, url = address.split('://')
			
			self.protocol = proto

			parts = url.split('/')
			host = parts[0]
			self.check_out_of_scope(host)

			path = '/'.join(parts[1:])
			path = '/' + path if not path.startswith('/') else path

		# the address is relative
		elif address.startswith('/'):
			proto = self.protocol
			host = self.host
			path = address

		# the address starts with the host name with out protocol
		else:
			proto = self.protocol
			parts = address.split('/')
			host = parts[0]

			self.check_out_of_scope(host)

			path = '/'.join(parts[1:])
			path = '/' + path if not path.startswith('/') else path

		if host.endswith('/'): host = host[:-1]

		return (proto, host, path)


	def _clean_page_404(self, page):
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


	def request(self, protocol, host, path):
		
		http_con  = http.client.HTTPConnection
		https_con = http.client.HTTPSConnection

		# create correct Connection
		conn = http_con(host) if protocol == 'http' else https_con(host)
		conn.request("GET", path)
		r1 = conn.getresponse()

		R = Request()

		R.protocol = protocol
		R.host = host
		R.url = path
		R.status = {'code': r1.status, 'text': r1.reason}
		R.headers = {pair[0].lower():pair[1] for pair in r1.getheaders()}
	
		body = r1.read()

		R.set_body(body)
		R.md5 = hashlib.md5(body).hexdigest().lower()
		R.md5_404 = self._clean_page_404(body)

		conn.close()

		return R 


	def get(self):
		r = self.request(self.protocol, self.host, self.path)
		hist = [r]

		location = 'Location'.lower()
		while location in r.headers:
			address = r.headers[location]
			protocol, host, path = self.get_parts(address)
			
			r = self.request(protocol, host, path)
			hist.append(r)

		r.history = hist[:-1]

		return r