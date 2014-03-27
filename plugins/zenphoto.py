from classes.specializedRequesters import CMSReqMD5

class ZenPhoto(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "ZenPhoto"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/zenphoto.json"

def get_instances(host, cache, results):
	return [ZenPhoto(host, cache, results)]
