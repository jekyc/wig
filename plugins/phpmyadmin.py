from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqRegex, CMSReqString

class phpMyAdminMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "phpMyAdmin"
		self.prefix	= ["/phpmyadmin", "/pma", ""]
		self.data_file	= "data/cms/md5/phpmyadmin.json"

class phpMyAdminRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "phpMyAdmin"
		self.prefix	= ["/phpmyadmin", "/pma", ""]
		self.data_file	= "data/cms/regex/phpmyadmin.json"

class phpMyAdminString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "phpMyAdmin"
		self.prefix	= ["/phpmyadmin", "/pma", ""]
		self.data_file	= "data/cms/string/phpmyadmin.json"

def get_instances(host, cache, results):
	return [
		phpMyAdminMD5(host, cache, results),
		phpMyAdminRegex(host, cache, results),
		phpMyAdminString(host, cache, results),
	]
