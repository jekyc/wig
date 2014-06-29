from classes.specializedRequesters import CMSReqMD5

class phpPgAdmin(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "phpPgAdmin"
		self.prefix	= ["/phppgadmin", ""]
		self.data_file	= "data/cms/md5/phppgadmin.json"

def get_instances(host, cache, results):
	return [
		phpPgAdmin(host, cache, results),
	]
