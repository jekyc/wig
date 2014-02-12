from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

"""class Typo3MD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Typo3"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/typo3.json"
"""

class Typo3String(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Typo3"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/typo3.json"	


class Typo3Regex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "Typo3"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/typo3.json"


def get_instances(host, cache, results):
	return [
#		Typo3MD5(host, cache, results),
		Typo3String(host, cache, results),
		Typo3Regex(host, cache, results)
	]
