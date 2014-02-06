from plugins.classes.specializedRequesters import CMSReqMD5

class phpBB(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "phpBB"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/phpbb.json"

def get_instances(host, cache, results):
	return [phpBB(host, cache, results)]
