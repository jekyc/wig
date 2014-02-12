from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class LotusMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Lotus Domino"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/lotusdomino.json"

class LotusString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Lotus Domino"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/lotusdomino.json"

class LotusRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Lotus Domino"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/lotusdomino.json"

def get_instances(host, cache, results):
	return [
		LotusRegex(host, cache, results),
		LotusString(host, cache, results),
		LotusMD5(host, cache, results)
	]
