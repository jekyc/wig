from plugins.classes.specializedRequesters import CMSReqMD5

class myBB(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "myBB"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/mybb.json"

def get_instances(host, cache, results):
	return [myBB(host, cache, results)]
