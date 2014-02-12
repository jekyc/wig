from classes.specializedRequesters import CMSReqMD5

class dotCMS(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "dotCMS"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/dotcms.json"

def get_instances(host, cache, results):
	return [dotCMS(host, cache, results)]
