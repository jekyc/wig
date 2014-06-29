from classes.specializedRequesters import CMSReqMD5, CMSReqString

class RoundCubeString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "RoundCube"
		self.prefix	= ["", "/webmail", "/mail", "/roundcube"]
		self.data_file	= "data/cms/string/roundcube.json"

class RoundCubeMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "RoundCube"
		self.prefix	= ["/webmail", "/mail", "/roundcube", ""]
		self.data_file	= "data/cms/md5/roundcube.json"

def get_instances(host, cache, results):
	return [
		RoundCubeMD5(host, cache, results),
		RoundCubeString(host, cache, results)
	]
