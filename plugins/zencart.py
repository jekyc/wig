from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class ZenCartMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Zen-Cart"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/zencart.json"


class ZenCartString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Zen-Cart"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/zencart.json"	


def get_instances(host, cache, results):
	return [
		ZenCartMD5(host, cache, results),
		ZenCartString(host, cache, results),
	]
