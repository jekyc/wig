from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class DemandWareString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Demandware"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/demandware.json"

def get_instances(host, cache, results):
	return [
		DemandWareString(host, cache, results),
	]