from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class EasyNetMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Easy Net CMS"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/easynet.json"

def get_instances(host, cache, results):
	return [
		EasyNetMD5(host, cache, results)
	]
