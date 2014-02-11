from plugins.classes.matcher import Match
import re


class MD5Matcher(Match):
	def __init__(self, requested, check_for_error_page=False):
		self.requested = requested
		self.error_check = check_for_error_page
	
	def get_matches(self):
		matches = []
		for r in self.requested:
			if self.__check_single(r):
				matches.append(r)
		return matches

	def __check_single(self, item):
		if self.error_check:
			if not self.check_page(item):
				return False
		
		return item["md5"] == item["response"].md5


class StringMatcher(Match):
	def __init__(self, requested, check_for_error_page=False):
		self.requested = requested
		self.error_check = check_for_error_page
	
	def get_matches(self):
		matches = []
		for r in self.requested:
			if self.__check_single(r):
				matches.append(r)
		return matches

	def __check_single(self, item):
		if self.error_check:
			if not self.check_page(item):
				return False
		
		return item["string"] in item["response"].text


class RegexMatcher(Match):
	def __init__(self, requested, check_for_error_page=False):
		self.requested = requested
		self.error_check = check_for_error_page
			
	def get_matches(self):
		matches = []
		for r in self.requested:

			output = self.__regex_body(r)
			if output:
				r['output'] = output
				matches.append(r)
		return matches


	def __regex_body(self, item):
		if self.error_check:
			if not self.check_page(item):
				return False

		body = item["response"].text
		regex = item["regex"]
		output = item["output"]

		matches = re.findall(regex, body)
		if len(matches):
			if not output == "":
				return output % matches[0]
			else:
				return True
		else:
			return False



class HeaderMatcher(Match):
	def __init__(self, requested, check_for_error_page=False):
		self.requested = requested
		self.error_check = check_for_error_page
			
	def get_matches(self):
		matches = []
		for r in self.requested:

			output = self.__regex_header(r)
			if output:
				r['output'] = output
				matches.append(r)
		return matches

	def __regex_header(self, item):
		if self.error_check:
			if not self.check_page(item):
				return False

		headers = item["response"].headers
		regex = item["regex"]
		header = item["header"]
		output = item["output"]

		# check if the header is in the page headers
		if header in headers:
			matches = re.findall(regex, headers[header])
			
			# check if there is a match
			if len(matches):
				# if a match is found and 'output' has a replacement string
				# return the replaced string
				if not output == "":
					return output % matches[0]

				# if a match was found but there is no specific data to return
				# return True to indicate that the header exists
				else:
					return True
			else:
				return False
		else:
			return False






