from collections import defaultdict
from classes.color import Color

class Results(object):

	def __init__(self):
		self.width = None
		self.color = Color()
		self.results = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
		#              ^Category           ^Plugin             ^Version    ^weight  

	def add(self, category, plugin, data, weight=False):
		v = data['version']
		dw = data['count']

		if type(v) == bool: v = ""

		if type(weight) == bool:
			w = 1.0/dw if weight else dw
			self.results[category][plugin][v] += w
		elif type(weight) == int or type(weight) == float:
			self.results[category][plugin][v] += weight
		else:
			pass

	def get_results(self):
		return self.results

	def set_width(self, width):
		self.width = width

	def __str__(self):
		out = "\n"
		o_cat = sorted([c for c in self.results])

		for category in o_cat:

			#out += "{0:<20}".format(category, )
			start = "___ " + self.color.format(category, 'red', False) + " "
			out +=	start + "_" * (self.width - (len(category) + 5)) + "\n"
			plugin_list = []

			o_plug = sorted([p for p in self.results[category]])
			for plugin in o_plug:
				v = self.results[category][plugin]

				# get only most relevant results
				# sort by weight
				versions = sorted(v.items(), key=lambda x:x[1], reverse=True)

				# pick only the first(s) element
				relevant = []
				for i in versions:
					# ugly temp hack
					if category == 'Desperate':
						relevant.append(i[0])

					elif i[1] == versions[0][1]:

						# do not append blank output strings
						if len(relevant) > 0  and i[0] == "":
							continue

						relevant.append(i[0])
					else:
						break	

				plug_str = "%s: " % (plugin, )
				ver_str =  ", ".join(relevant)

				plugin_list.append(plug_str + ver_str)
			
			out += "\n".join(plugin_list) + "\n\n"

		return out[:-1]
