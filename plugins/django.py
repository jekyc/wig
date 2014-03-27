from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex, CMSReqHeader

class DjangoString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Django"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/django.json"

class DjangoMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Django"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/django.json"

def get_instances(host, cache, results):
	return [
		DjangoString(host, cache, results),
		DjangoMD5(host, cache, results)
	]
