from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class XOOPSMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "XOOPS"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/xoops.json"


class XOOPSString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "XOOPS"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/xoops.json"	


def get_instances(host, cache, results):
	return [
		XOOPSMD5(host, cache, results),
		XOOPSString(host, cache, results),
	]
