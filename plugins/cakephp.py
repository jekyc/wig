from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex, CMSReqHeader

class CakePHPString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "CakePHP"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/cakephp.json"


class CakePHPHeader(CMSReqHeader):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name = "CakePHP"
		self.data_file = "data/cms/header/cakephp.json"

def get_instances(host, cache, results):
	return [
		CakePHPString(host, cache, results),
		CakePHPHeader(host, cache, results),
	]
