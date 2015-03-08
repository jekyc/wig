from classes.color import Color
import re

class Output(object):

	def __init__(self, options, data):
		self.results = None
		self.color = data['colorizer']
		self.data = data

		# calc the amount of fingerprints
		fps = data['fingerprints'].data
		num_fps_js		= sum([len(fps['js'][fp_type]['fps']) for fp_type in fps['js']])
		num_fps_os		= len(fps['os']['fps'])
		num_fps_cms		= sum([len(fps['cms'][fp_type]['fps']) for fp_type in fps['cms']])
		num_fps_plat	= sum([len(fps['platform'][fp_type]['fps']) for fp_type in fps['platform']])
		num_fps_vuln	= sum([len(fps['vulnerabilities'][source]['fps']) for source in fps['vulnerabilities']])
		num_fps = num_fps_js + num_fps_os + num_fps_cms + num_fps_plat + num_fps_vuln


		self.stats = {
			'runtime':		'Time: %.1f sec' % (data['runtime'], ),
			'url_count':	'Urls: %s' % (data['url_count'], ),
			'fp_count':		'Fingerprints: %s' % (num_fps, ),
		}

		self.col_widths =  {1: 0, 2: 0, 3: 0}


		self.sections = [
			{
				'name': 'version',
				'headers': {
					1: {'title': 'SOFTWARE', 'color': 'blue', 'bold': True},
					2: {'title': 'VERSION',  'color': 'blue', 'bold': True},
					3: {'title': 'CATEGORY',  'color': 'blue', 'bold': True}
				},
				'titles': [
					{'category': 'cms',					'title': 'CMS'},
					{'category': 'js',					'title': 'JavaScript'},
					{'category': 'platform',			'title': 'Platform'},
					{'category': 'os',					'title': 'Operating System'},
				]
			},
			{
				'name': 'vulnerabilities',
				'headers': {
					1: {'title': 'SOFTWARE',        'color': 'blue', 'bold': True},
					2: {'title': 'VULNERABILITIES', 'color': 'blue', 'bold': True},
					3: {'title': 'LINK',            'color': 'blue', 'bold': True}
				},
				'titles': [
					{'category': 'vulnerability',          'title': '%s'},
				]
			},
			{
				'name': 'tool',
				'headers': {
					1: {'title': 'SOFTWARE',        'color': 'blue', 'bold': True},
					2: {'title': 'TOOL',            'color': 'blue', 'bold': True},
					3: {'title': 'LINK',            'color': 'blue', 'bold': True}
				},
				'titles': [
					{'category': 'tool',             'title': '%s'},
				]
			},
			{
				'name': 'interesting',
				'headers':{
					1: {'title': 'URL',      'color': 'blue', 'bold': True},
					2: {'title': 'NOTE',     'color': 'blue', 'bold': True},
					3: {'title': 'CATEGORY', 'color': 'blue', 'bold': True}
				},
				'titles': [
					{'category': 'interesting',          'title': 'Interesting URL'},
				]
			}
		]

		self.seperator = ' | '
		self.seperator_color = self.color.format(self.seperator, 'blue', True)
		self.ip = self.title = self.cookies = None


	def _replace_version_text(self, text):
		# replace text in version output with something else
		# (most likely an emtpy string) to improve output
		text = re.sub('^wmf/', '', text)
		text = re.sub('^develsnap_', '', text)
		text = re.sub('^release_candidate_', '', text)
		text = re.sub('^release_stable_', '', text)
		text = re.sub('^release[-|_]', '', text, flags=re.IGNORECASE)	# Umbraco, phpmyadmin
		text = re.sub('^[R|r][E|e][L|l]_', '', text)				
		text = re.sub('^mt', '', text)				# Movable Type
		text = re.sub('^mybb_', '', text)			# myBB
		return text


	def _update(self):
		self.data['results'].update()
		self.results = self.data['results'].get_results()
		
		self._set_col_1_width(self.results)
		self._set_col_2_width(self.results)
		self._set_col_3_width(self.results)

		self.ip = self.data['results'].site_info['ip']
		self.title = self.data['results'].site_info['title']
		self.cookies = self.data['results'].site_info['cookies']


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
			v = [self._replace_version_text(i) for i in versions]
			out += self.seperator_color.join(v)
			out += ' ' * (self.col_widths[2] - len(self.seperator.join(v)))			
		else:
			v = self._replace_version_text(versions[0])
			out += v
			out += ' ' * (self.col_widths[2] - len(v))

		# col3
		out += category + '\n'

		return out


	def get_results(self):
		
		self._update()

		title  = '\n'
		title += self.color.format('TITLE    ', 'blue', True) + '\n' + self.title + '\n\n'
		
		if self.cookies:
			title += self.color.format('COOKIES  ', 'blue', True) + '\n' + ', '.join(list(self.cookies)) + '\n\n'
	
		title += self.color.format('IP       ', 'blue', True) + '\n' + self.ip + '\n'

		data = '\n'
		for section in ['version', 'vulnerabilities', 'tool', 'interesting']:
			tmp = ''
			versions = self.sections[self._find_section_index(section)]
			for item in versions['titles']:
				if item['category'] not in self.results: continue
				for plugin in sorted(self.results[item['category']]):
					
					# if the name is a dict (used for vulnerabilities) extract the 
					# items, and replace the '%' in 'title'.
					# this is a crappy hack to support the special case of vulnerabilities
					# this needs to be redone!
					if type(self.results[item['category']][plugin]) == dict:
						col2 = [self.results[item['category']][plugin]['col2']]
						col3 = item['title'] % (self.results[item['category']][plugin]['col3'],)
					else:
						col2 = self.results[item['category']][plugin]
						col3 = item['title']

					tmp += self.create_line(plugin, col2, col3)

			if not tmp == '':
				data += '\n'+ self.create_header(section) + tmp

		# status bar
		time = self.stats['runtime']   + ' ' * (self.col_widths[1] - len(self.stats['runtime']))
		urls = self.stats['url_count'] + ' ' * (self.col_widths[2] - len(self.stats['url_count'])) 
		fps  = self.stats['fp_count']

		status  = self.color.format('_'*sum(self.col_widths.values()), 'blue', True) + '\n'
		status += ''.join([ time, urls, fps ])

		return (title, data + status + '\n')
