from plugins.classes.specializedRequesters import CMSReqMD5

class RoundCube(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "RoundCube"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/roundcube.json"

def get_instances(host, cache, results):
	return [RoundCube(host, cache, results)]
