from classes.specializedRequesters import CMSReqMD5

class Concrete5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Concrete5"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/concrete5.json"

def get_instances(host, cache, results):
	return [Concrete5(host, cache, results)]
