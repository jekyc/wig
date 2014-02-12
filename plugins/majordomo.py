from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class MajordomoString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Majordomo2 Mailing List"
		self.prefix	= ["", "/majordomo"]
		self.data_file	= "data/cms/string/majordomo.json"

class MajordomoRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Majordomo2 Mailing List"
		self.prefix	= ["", "/majordomo"]
		self.data_file	= "data/cms/regex/majordomo.json"

def get_instances(host, cache, results):
	return [
		MajordomoRegex(host, cache, results),
		MajordomoString(host, cache, results),
	]
