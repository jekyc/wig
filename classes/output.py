from classes.color import Color

class Output(object):

	def __init__(self, results):
		self.results = results
		self.color = Color()
		self.col_widths =  { 1: 0, 2: 0, 3: 0, 0: 0}

		self.sections = [
			{
				'name': 'version',
				'headers': {
					1: {'title': 'SOFTWARE', 'color': 'blue', 'bold': True},
					2: {'title': 'VERSION',  'color': 'blue', 'bold': True},
					3: {'title': 'COMMENT',  'color': 'blue', 'bold': True}
				},
				'titles': [
					{'category': 'CMS',                  'title': 'CMS'},
					{'category': 'JavaScript Libraries', 'title': 'JavaScript'},
					{'category': 'Platform',             'title': 'Platform'},
					{'category': 'Operating System',     'title': 'Operating System'},
				]
			},
			{
				'name': 'interesting',
				'headers':{
					1: {'title': 'URL',     'color': 'blue', 'bold': True},
					2: {'title': 'NOTE',    'color': 'blue', 'bold': True},
					3: {'title': 'COMMENT', 'color': 'blue', 'bold': True}
				},
				'titles': [
					{'category': 'Interesting',          'title': 'Interesting URL'},
				]
			}
		]

		self.seperator = ' | '
		self.seperator_color = self.color.format(self.seperator, 'blue', True)

		self.stats = {
			'runtime': None,
			'number_of_urls': None,
			'number_of_fps': None,
		}


		self._set_col_1_width(results)
		self._set_col_2_width(results)
		self._set_col_3_width(results)


	def _find_section_index(self, section):
		index = 0
		for elm in self.sections:
			if elm['name'] == section: return index
			index += 1

		return None

	def _update_col_0(self):
		self.col_widths[0] = self.col_widths[1] + self.col_widths[2] + self.col_widths[3]


	def _set_col_1_width(self, results):
		title_len = max([len(i['headers'][1]['title']) for i in self.sections])
		self.col_widths[1] = max(max([len(p) for c in results for p in results[c]]), title_len) + 2
		self._update_col_0()


	def _set_col_2_width(self, results):
		width = max([ len(i['headers'][2]['title']) for i in self.sections])
		for c in results:
			for p in results[c]:
				width = max(len(self.seperator.join(results[c][p])), width)

		self.col_widths[2] = width + 2
		self._update_col_0()
		

	def _set_col_3_width(self, results):
		self.col_widths[3] = max([len(i['title']) for s in self.sections for i in s['titles']]) 
		self._update_col_0()


	def set_number_urls(self, num_urls): self.stats['number_of_urls'] = num_urls
	def set_runtime(self, runtime):      self.stats['runtime'] = "%.1f" % (runtime,)
	def set_number_fps(self, num_fps):   self.stats['number_of_fps'] = num_fps


	def create_header(self, section):
		section_index = self._find_section_index(section)
		headers = self.sections[section_index]['headers']
		
		out  = ''
		for i in range(1,4):
			out += self.color.format(headers[i]['title'], headers[i]['color'], headers[i]['bold']) 
			out += ' ' * (self.col_widths[i] - len(headers[i]['title']))
		out += '\n'

		return out


	def create_line(self, software, versions, category):
		out  = software
		out += ' ' * (self.col_widths[1] - len(software))
		
		if len(versions) > 1:
			out += self.seperator_color.join(versions)
			out += ' ' * (self.col_widths[2] - len(self.seperator.join(versions)))			
		else:
			out += versions[0]
			out += ' ' * (self.col_widths[2] - len(versions[0]))

		out += category 
		out += ' ' * (self.col_widths[3] - len(category))
		out += '\n'

		return out


	def get_status(self):
		time = 'Time: %s sec' % (self.stats['runtime'], )
		urls = 'Urls: %s' % (self.stats['number_of_urls'], )
		fps  = 'Fingerprints: %s' % (self.stats['number_of_fps'], )

		# if the current width of the output is smaller that the 
		# width of the status bar, extend the width of column 2
		min_width = len('  '.join([ time, urls, fps ]))

		if min_width > self.col_widths[0]:
			self.col_widths[2] = min_width - (self.col_widths[1] + self.col_widths[3])
			self._update_col_0()
		else:
			time = time + ' ' * (self.col_widths[1] - len(time) - 2 )
			urls = urls + ' ' * (self.col_widths[2] - len(urls) - 5 ) 
			fps  = ' ' * (self.col_widths[3] - len(fps)) + fps

		# generate the status bar
		status  = self.color.format('_'*self.col_widths[0], 'blue', True) + '\n'
		status += '  '.join([ time, urls, fps ])
		return status

	
	def get_results(self):
		status_bar = self.get_status()

		out = ''
		for section in ['version', 'interesting']:

			tmp = ''
			versions = self.sections[self._find_section_index(section)]
			for item in versions['titles']:
				if item['category'] not in self.results: continue
				for plugin in sorted(self.results[item['category']]):
					tmp += self.create_line(plugin, self.results[item['category']][plugin], item['title'])

			if not tmp == '':
				out += '\n'
				out += self.create_header(section)
				out += tmp

		return out + status_bar + '\n'
