class Match(object):
	def __init__(self):
		pass
		
	def __http_code_match(self, item):
		code = 200 if "code" not in item else item["code"]
		return item["response"].status_code == code

	# change this at some point
	# only checks for status code
	# should compare to the response of actual error pages
	def __is_error_page(self, item): 
		return not item["response"].status_code == 200 
	
	def check_page(self, item):
		if not self.__http_code_match(item):
			return False
	
		if self.__is_error_page(item):
			return False
		
		return True
