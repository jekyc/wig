from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class TomcatMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Tomcat"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/tomcat.json"

class TomcatRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Tomcat"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/tomcat.json"


def get_instances(host, cache, results):
	return [
		TomcatMD5(host, cache, results),
		TomcatRegex(host, cache, results)
	]
