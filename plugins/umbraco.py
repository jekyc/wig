from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class Umbraco(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Umbraco"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/umbraco.json"


def get_instances(host, cache, results):
	return [Umbraco(host, cache, results)]
