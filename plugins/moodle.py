from plugins.classes.specializedRequesters import CMSReqMD5

class Moodle(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Moodle"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/moodle.json"

def get_instances(host, cache, results):
	return [Moodle(host, cache, results)]
