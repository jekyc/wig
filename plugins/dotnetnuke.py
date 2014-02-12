from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class DotNetNukeMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DotNetNuke"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/dotnetnuke.json"

class DotNetNukeString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DotNetNuke"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/dotnetnuke.json"	

def get_instances(host, cache, results):
	return [
		DotNetNukeMD5(host, cache, results),
		DotNetNukeString(host, cache, results)
	]
