from plugins.classes.specializedRequesters import CMSReqMD5

class MediaWiki(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "MediaWiki"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/mediawiki.json"

def get_instances(host, cache, results):
	return [MediaWiki(host, cache, results)]
