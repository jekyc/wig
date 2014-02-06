from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class DokuWikiMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DokuWiki"
		self.prefix	= ["/dokuwiki", ""]
		self.data_file	= "data/cms/md5/dokuwiki.json"

class DokuWikiString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DokuWiki"
		self.prefix	= ["/dokuwiki", ""]
		self.data_file	= "data/cms/string/dokuwiki.json"

class DokuWikiRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "DokuWiki"
		self.prefix	= ["/dokuwiki", ""]
		self.data_file	= "data/cms/regex/dokuwiki.json"


def get_instances(host, cache, results):
	return [
		DokuWikiMD5(host, cache, results),
		DokuWikiString(host, cache, results),
		DokuWikiRegex(host, cache, results),
	]
