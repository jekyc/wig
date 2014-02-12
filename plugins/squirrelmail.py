from classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex

class SquirrelMailMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "SquirrelMail"
		self.prefix	= ["", "/mail", "/webmail", "/squirrelmail"]
		self.data_file	= "data/cms/md5/squirrelmail.json"

class SquirrelMailString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "SquirrelMail"
		self.prefix	= ["", "/mail", "/webmail", "/squirrelmail"]
		self.data_file	= "data/cms/string/squirrelmail.json"

class SquirrelMailRegex(CMSReqRegex):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name	= "SquirrelMail"
		self.prefix	= ["", "/mail", "/webmail", "/squirrelmail"]
		self.data_file	= "data/cms/regex/squirrelmail.json"


def get_instances(host, cache, results):
	return [
		SquirrelMailMD5(host, cache, results),
		SquirrelMailString(host, cache, results),
		SquirrelMailRegex(host, cache, results),
	]
