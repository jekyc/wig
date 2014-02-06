from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class WordPressMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "WordPress"
		self.prefix	= ["/wp", "/wordpress", ""]
		self.data_file	= "data/cms/md5/wordpress.json"


class WordPressString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "WordPress"
		self.prefix	= ["/wp", "/wordpress", ""]
		self.data_file	= "data/cms/string/wordpress.json"	


class WordPressRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "WordPress"
		self.prefix	= ["/wp", "/wordpress", ""]
		self.data_file	= "data/cms/regex/wordpress.json"


def get_instances(host, cache, results):
	return [
		WordPressMD5(host, cache, results),
		WordPressString(host, cache, results),
		WordPressRegex(host, cache, results)
	]