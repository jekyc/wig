from classes.specializedRequesters import CMSReqMD5

class PrestaShop(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "prestashop"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/prestashop.json"

def get_instances(host, cache, results):
	return [
		PrestaShop(host, cache, results),
	]
