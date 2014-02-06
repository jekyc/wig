from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class JBossMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "JBoss"
		self.prefix	= [""]
		self.data_file	= "data/cms/md5/jboss.json"

class JBossString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "JBoss"
		self.prefix	= [""]
		self.data_file	= "data/cms/string/jboss.json"

class JBossRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "JBoss"
		self.prefix	= [""]
		self.data_file	= "data/cms/regex/jboss.json"


def get_instances(host, cache, results):
	return [
		JBossMD5(host, cache, results),
		JBossString(host, cache, results),
		JBossRegex(host, cache, results)
	]