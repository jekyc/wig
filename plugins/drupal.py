from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex, CMSReqHeader

class DrupalMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name = "Drupal CMS"
		self.data_file = "data/cms/md5/drupal.json"

class DrupalString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name = "Drupal CMS"
		self.data_file = "data/cms/string/drupal.json"

class DrupalRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name = "Drupal CMS"
		self.data_file = "data/cms/regex/drupal.json"

class DrupalHeader(CMSReqHeader):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name = "Drupal CMS"
		self.data_file = "data/cms/header/drupal.json"


def get_instances(host, cache, results):
	return [
		DrupalMD5(host,cache, results),
		DrupalString(host,cache, results),
		DrupalRegex(host,cache, results),
		DrupalHeader(host,cache, results),
	]
