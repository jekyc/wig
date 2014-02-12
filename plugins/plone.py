from classes.specializedRequesters import CMSReqMD5, CMSReqString

class PloneMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Plone"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/plone.json"

class PloneString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Plone"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/plone.json"


def get_instances(host, cache, results):
	return [
		PloneMD5(host, cache, results),
		PloneString(host, cache, results),
	]
