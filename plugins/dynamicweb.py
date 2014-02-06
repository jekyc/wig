from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class DynamicWebMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DynamicWeb CMS"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/dynamicweb.json"


class DynamicWebString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DynamicWeb CMS"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/dynamicweb.json"


class DynamicWebRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DynamicWeb CMS"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/dynamicweb.json"


def get_instances(host, cache, results):
	return [
		DynamicWebMD5(host, cache, results),
		DynamicWebString(host, cache, results),
		DynamicWebRegex(host, cache, results)
	]