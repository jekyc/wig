from classes.color import Color

class Output(object):

	def __init__(self, results, runtime, url_count, fp_count):
		self.results = results
		self.color = Color()

		self.stats = {
			'runtime':		'Time: %.1f sec' % (runtime, ),
			'url_count':	'Urls: %s' % (url_count, ),
			'fp_count':		'Fingerprints: %s' % (fp_count, ),
		}

		self.col_widths =  {1: 0, 2: 0, 3: 0}


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

		self._set_col_1_width(results)
		self._set_col_2_width(results)
		self._set_col_3_width(results)




	def _find_section_index(self, section):
		index = 0
		for elm in self.sections:
			if elm['name'] == section: return index
			index += 1

		return None


	def _set_col_1_width(self, results):
		self.col_widths[1] = 2 + max(
			max([len(i['headers'][1]['title']) for i in self.sections]),	# length of section header titles
			max([len(p) for c in results for p in results[c]] + [0]), 			# length of software name from results
			len(self.stats['runtime'])										# length of status bar (time)
		)


	def _set_col_2_width(self, results):		
		self.col_widths[2] = 2 + max(
			max([ len(i['headers'][2]['title']) for i in self.sections ]),							# length of section header titles
			max([ len(self.seperator.join(results[c][p])) for c in results for p in results[c]] + [0]),	# length of version details from results
			len(self.stats['url_count'])															# length of status bar (urls)
		)
		

	def _set_col_3_width(self, results):
		self.col_widths[3] = max(
			max([len(i['title']) for s in self.sections for i in s['titles']]),	# length of titles
			len(self.stats['fp_count'])												# length of status bar (fps)
		)


	def create_header(self, section):
		section_index = self._find_section_index(section)
		headers = self.sections[section_index]['headers']
		out  = ''

		# col 1
		out += self.color.format(headers[1]['title'], headers[1]['color'], headers[1]['bold'])
		out += ' ' * (self.col_widths[1] - len(headers[1]['title']))

		# col 2
		out += self.color.format(headers[2]['title'], headers[2]['color'], headers[2]['bold'])
		out += ' ' * (self.col_widths[2] - len(headers[2]['title']))

		# col 3
		out += self.color.format(headers[3]['title'], headers[3]['color'], headers[3]['bold'])
		out += '\n'

		return out


	def create_line(self, software, versions, category):

		# col 1
		out  = software
		out += ' ' * (self.col_widths[1] - len(software))
		
		#col 2
		if len(versions) > 1:
			out += self.seperator_color.join(versions)
			out += ' ' * (self.col_widths[2] - len(self.seperator.join(versions)))			
		else:
			out += versions[0]
			out += ' ' * (self.col_widths[2] - len(versions[0]))

		# col3
		out += category 
		out += '\n'

		return out

	
	def get_results(self):
		
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


		# status bar
		time = self.stats['runtime']   + ' ' * (self.col_widths[1] - len(self.stats['runtime']))
		urls = self.stats['url_count'] + ' ' * (self.col_widths[2] - len(self.stats['url_count'])) 
		fps  = self.stats['fp_count']

		status  = self.color.format('_'*sum(self.col_widths.values()), 'blue', True) + '\n'
		status += ''.join([ time, urls, fps ])

		return out + status + '\n'
