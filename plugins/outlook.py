from plugins.classes.specializedRequesters import CMSReqMD5, CMSReqString, CMSReqRegex, CMSReqHeader

class OutlookMD5(CMSReqMD5):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name = "Microsoft Outlook Web Access"
		self.data_file = "data/cms/md5/outlook.json"

class OutlookString(CMSReqString):
	def __init__(self, host, cache, results):
		super().__init__(host, cache, results)
		self.name = "Microsoft Outlook Web Access"
		self.data_file = "data/cms/string/outlook.json"

def get_instances(host, cache, results):
	return [
		OutlookMD5(host,cache, results),
		OutlookString(host,cache, results),
	]