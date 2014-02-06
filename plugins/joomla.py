from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqRegex

class JoomlaMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Joomla!"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/joomla.json"

class JoomlaRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Joomla!"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/joomla.json"


def get_instances(host, cache, results):
	return [
		JoomlaMD5(host, cache, results),
		JoomlaRegex(host, cache, results)
	]
