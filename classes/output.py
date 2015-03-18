from classes.color import Color
import re, json

class Output:

	def __init__(self, options, data):
		self.results = None
		self.color = data['colorizer']
		self.data = data
		self.options = options

		# calc the amount of fingerprints
		fps = data['fingerprints'].data
		num_fps_js		= sum([len(fps['js'][fp_type]['fps']) for fp_type in fps['js']])
		num_fps_os		= len(fps['os']['fps'])
		num_fps_cms		= sum([len(fps['cms'][fp_type]['fps']) for fp_type in fps['cms']])
		num_fps_plat	= sum([len(fps['platform'][fp_type]['fps']) for fp_type in fps['platform']])
		num_fps_vuln	= sum([len(fps['vulnerabilities'][source]['fps']) for source in fps['vulnerabilities']])
		self.num_fps = num_fps_js + num_fps_os + num_fps_cms + num_fps_plat + num_fps_vuln

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

		self.sections_names = [s['name'] for s in self.sections]

		self.seperator = ' | '
		self.seperator_color = self.color.format(self.seperator, 'blue', True)
		self.ip = self.title = self.cookies = None


	def replace_version_text(self, text):
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

	def find_section_index(self, section):
		index = 0
		for elm in self.sections:
			if elm['name'] == section: return index
			index += 1

		return None

	def update_stats(self):
		self.stats = {
			'runtime':		'Time: %.1f sec' % (self.data['runtime'], ),
			'url_count':	'Urls: %s' % (self.data['url_count'], ),
			'fp_count':		'Fingerprints: %s' % (self.num_fps, ),
		}

	def loop_results(self, section):
		versions = self.sections[self.find_section_index(section)]
		for item in versions['titles']:
			if item['category'] not in self.results: continue
			for software in sorted(self.results[item['category']]):
				version = self.results[item['category']][software]
				category = item['title']
				yield (category, software, version)





class OutputJSON(Output):
	def __init__(self, options, data):
		super().__init__(options, data)
		self.json_data = []
	
	def add_results(self):		

		self.results = self.data['results'].results
		site_info = self.data['results'].site_info

		site = {
			'statistics': {
				'start_time': self.data['timer'],
				'run_time': self.data['runtime'],
				'urls': self.data['url_count'],
				'fingerprints': self.num_fps
			},
			'site_info': {
				'url': self.options['url'],
				'title': site_info['title'],
				'cookies': [c for c in site_info['cookies']],
				'ip': site_info['ip']
			},
			'data': []
		}

		# add versions
		for section in self.sections_names:
			tmp = ''
			for result in self.loop_results(section):
				category, software, version = result

				if section == 'vulnerabilities':
					site['data'].append({
						'category': 'vulnerability',
						'name': software[0],
						'version': software[1],
						'link': version['col3'],
						'vulnerability_count': version['col2']
					})

				else:
					site['data'].append({
						'category': category,
						'name': software,
						'version': version
					})

		self.json_data.append(site)

	
	def add_error(self, msg):
		self.json_data.append({
			'site_info': {
				'url': self.options['url'],
				'error': msg
			}
		})



	def write_file(self):
		file_name = self.options['write_file']
		with open(file_name+ '.json', 'w') as fh:
			fh.write(json.dumps(self.json_data, sort_keys=True, indent=4, separators=(',', ': ')))





class OutputPrinter(Output):

	def __init__(self, options, data):
		super().__init__(options, data)
		self.col_widths =  {1: 0, 2: 0, 3: 0}


	def _set_col_1_width(self, results):
		self.col_widths[1] = 2 + max(
			max([len(i['headers'][1]['title']) for i in self.sections]),	# length of section header titles
			max([len(p) for c in results for p in results[c]] + [0]), 			# length of software name from results
			len(self.stats['runtime'])										# length of status bar (time)
		)


	def _set_col_2_width(self, results):		
		self.col_widths[2] = 2 + max(
			max([ len(i['headers'][2]['title']) for i in self.sections ]),							# length of section header titles
			max([ len(self.seperator.join(results[c][p])) for c in results for p in results[c] ] + [0]),	# length of version details from results
			len(self.stats['url_count'])															# length of status bar (urls)
		)
		

	def _set_col_3_width(self, results):
		self.col_widths[3] = max(
			max([len(i['title']) for s in self.sections for i in s['titles']]),	# length of titles
			len(self.stats['fp_count'])												# length of status bar (fps)
		)


	def create_header(self, section):
		section_index = self.find_section_index(section)
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
			v = [self.replace_version_text(i) for i in versions]
			out += self.seperator_color.join(v)
			out += ' ' * (self.col_widths[2] - len(self.seperator.join(v)))			
		else:
			v = self.replace_version_text(versions[0])
			out += v
			out += ' ' * (self.col_widths[2] - len(v))

		# col3
		out += category + '\n'

		return out


	def get_results(self):		

		self.results = self.data['results'].get_results()
		for category in self.results:
			for name in self.results[category]:
				versions = self.results[category][name]
				if len(versions) > 5:
					msg = '... (' + str(len(versions)-5) + ')'
					self.results[category][name] = versions[:5] + [msg]

		self.update_stats()
		self._set_col_1_width(self.results)
		self._set_col_2_width(self.results)
		self._set_col_3_width(self.results)

		ip = self.data['results'].site_info['ip']
		site_title = self.data['results'].site_info['title']
		cookies = self.data['results'].site_info['cookies']
		
		title  = '\n'
		title += self.color.format('TITLE    ', 'blue', True) + '\n' + site_title + '\n\n'
		
		if cookies:
			title += self.color.format('COOKIES  ', 'blue', True) + '\n' + ', '.join(list(cookies)) + '\n\n'
	
		title += self.color.format('IP       ', 'blue', True) + '\n' + ip + '\n'

		data = '\n'
		for section in self.sections_names:
			tmp = ''
			for result in self.loop_results(section):
				category, software, version = result
				# this is a crappy hack to support the special case of vulnerabilities
				# this needs to be redone!

				if section == 'vulnerabilities':
					col1 = ' '.join(list(software))
					col2 = [version['col2']]
					col3 = category % (version['col3'],)
				else:
					col1 = software
					col2 = version
					col3 = category

				tmp += self.create_line(col1, col2, col3)

			if not tmp == '':
				data += '\n'+ self.create_header(section) + tmp

		# status bar
		time = self.stats['runtime']   + ' ' * (self.col_widths[1] - len(self.stats['runtime']))
		urls = self.stats['url_count'] + ' ' * (self.col_widths[2] - len(self.stats['url_count'])) 
		fps  = self.stats['fp_count']

		status  = self.color.format('_'*sum(self.col_widths.values()), 'blue', True) + '\n'
		status += ''.join([ time, urls, fps ])

		return (title, data + status + '\n')
