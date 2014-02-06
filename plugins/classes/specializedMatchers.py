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
			output = self.__check_single(r)
			if output:
				r['output'] = output
				matches.append(r)
		return matches

	def __extract_regex(self, item):
		text = item["response"].text
		regex = item["regex"]
		output = item["output"]

		matches = re.findall(regex, text)
		if len(matches):
			if not output == "":
				return output % (matches[0],)
			else:
				return True
		else:
			return False

	def __check_single(self, item):
		if self.error_check:
			if not self.check_page(item):
				return False
		
		return self.__extract_regex(item)