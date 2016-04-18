from collections import defaultdict
from wig.classes.color import Color

class Log(object):
	def __init__(self):
		self.logs = defaultdict(lambda: defaultdict(set))
		self.colorizer = Color()

	def __str__(self):
		out = ""

		for url in self.logs:
			out += "Url: " + url
			for cms in self.logs[url]:
				lst = self.colorizer.format("[" + ", ".join(self.logs[url][cms]) + "]", 'red', False)
				out += "  %s: %s" % (cms, lst)
			out +=  "\n"

		return out

	def add(self, logs):
		for url in logs:
			for cms in logs[url]:
				for version in logs[url][cms]:
					self.logs[url][cms].add(str(version))

