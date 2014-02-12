from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class MovableTypeMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "MovableType"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/movabletype.json"

class MovableTypeString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "MovableType"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/movabletype.json"

class MovableTypeRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "MovableType"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/movabletype.json"

def get_instances(host, cache, results):
	return [
		MovableTypeMD5(host, cache, results),
		MovableTypeString(host, cache, results),
		MovableTypeRegex(host, cache, results)
	]
