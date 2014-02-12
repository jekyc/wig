from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class SitecoreMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Sitecore"
		self.prefix	= ["", "/sitecore"]
		self.data_file	= "data/cms/md5/sitecore.json"

class SitecoreString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Sitecore"
		self.prefix	= ["", "/sitecore"]
		self.data_file	= "data/cms/string/sitecore.json"

class SitecoreRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Sitecore"
		self.prefix	= ["", "/sitecore"]
		self.data_file	= "data/cms/regex/sitecore.json"


def get_instances(host, cache, results):
	return [
		SitecoreMD5(host, cache, results),
		SitecoreString(host, cache, results),
		SitecoreRegex(host, cache, results),
	]
