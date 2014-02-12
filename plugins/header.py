from classes.plugin import Plugin
from collections import Counter, defaultdict
import json, pprint

def get_instances(host, cache, results):
	return [Header(cache, results)]


class Header(Plugin):

	def __init__(self, cache, results):
		super().__init__(results)
		self.cache = cache
		self.results = results
		self.prefix = []
		self.header_name = []
		self.headers = defaultdict(set)
		self.use_profile = False

		self.category = "Server Info"
		
		for response in self.cache.get_responses():
			for header in response.headers:
				self.headers[header].add(response.headers[header])

		self.linehandlers = [
			ServerHeader(),
			PoweredBy()
		]

	def is_applicable(self, header):
		return header in [hn.lower() for hn in self.header_name]

	def run(self):
		for header_set in self.headers:
			for linehandler in self.linehandlers:
				if linehandler.is_applicable(header_set):
					for header in self.headers[header_set]:
						for res in linehandler.run(header):
							if res: self.add_results(res[0], res[1])


class ServerHeader(object):

	def __init__(self):
		self.header_name = ["Server"]

	def is_applicable(self, header):
		return header in [hn.lower() for hn in self.header_name]

	def split_server_line(self, line):
		if "(" in line:
			os = line[line.find('(')+1:line.find(')')]
			sh = line[:line.find('(')-1] + line[line.find(')')+1: ]
			return os, sh
		else:
			return False, line

	def run(self, header):
		os, line = self.split_server_line(header)
		
		out = []
		for part in line.split(" "):
				try:
					pkg,version = part.split('/')
					out.append([ 
						[{'version': version, 'count':1}] ,pkg 
					])
				except Exception as e:
					continue

		return out

class PoweredBy(object):
	def __init__(self):
		self.header_name = ["X-Powered-By"]

	def is_applicable(self, header):
		return header in [hn.lower() for hn in self.header_name]

	def run(self, line):
		try:
			pkg,version = line.split('/')
			return [[ [{'version': version, 'count':1}] ,pkg ]]

		except Exception as e:
			return []
