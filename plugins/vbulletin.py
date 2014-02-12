from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class vBulletinRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "vBulletin"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/vbulletin.json"


class vBulletinString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "vBulletin"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/vbulletin.json"	


def get_instances(host, cache, results):
	return [
		vBulletinRegex(host, cache, results),
		vBulletinString(host, cache, results),
	]
