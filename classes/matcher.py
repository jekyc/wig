import re

class Match(object):
	def __init__(self):
		pass
		
	def __http_code_match(self, item):
		code = 200 if "code" not in item else item["code"]
		return item["response"].status_code == code


	def __is_error_page(self, item): 
		# change this at some point
		# only checks for status code
		# should compare to the response of actual error pages
		return not item["response"].status_code == 200 
	
	
	def __check_page(self, item):
		if not self.__http_code_match(item): return False
		if self.__is_error_page(item): return False
		return True

	
	def get_result(self, fingerprints, response):
		# find the matching method to use
		matches = []

		for fingerprint in fingerprints:
			if fingerprint['type'] == 'md5':
				matches.append(self.md5(fingerprint, response))
			
			elif fingerprint['type'] == 'string':
				matches.append(self.string(fingerprint, response))
			
			elif fingerprint['type'] == 'regex':
				matches.append(self.regex(fingerprint, response))

			else:
				# fingerprint type is not supported yet
				matches.append(None)

		matches = [fp for fp in matches if fp is not None]

		return matches

	
	def md5(self, fingerprint, response):
		if fingerprint["md5"] == response.md5:
			return fingerprint
		else:
			return None

	def string(self, fingerprint, response):
		if fingerprint["string"] in response.text:
			return fingerprint
		else:
			return None

	
	def regex(self, fingerprint, response):
		# create copy of fingerprint
		copy = {key:fingerprint[key] for key in fingerprint}

		body = response.text
		regex = copy["regex"]
		output = copy["output"]

		matches = re.findall(regex, body)
		if len(matches):
			if not output == "":
				copy['output'] = output % matches[0]
			
			return copy
		else:
			return None




















