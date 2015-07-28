import re, json
from collections import defaultdict, namedtuple

class Output:
	def __init__(self, options, data):
		self.results = None
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

	def get_results_of_type(self, result_type):
		return [r for r in self.results if type(r).__name__ == result_type]

	def update_stats(self):
		self.stats = {
			'runtime':		'Time: %.1f sec' % (self.data['runtime'], ),
			'url_count':	'Urls: %s' % (self.data['url_count'], ),
			'fp_count':		'Fingerprints: %s' % (self.num_fps, ),
		}


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

		get = self.get_results_of_type

		# VERSIONS 
		for version in ['CMS', 'Platform', 'JavaScript', 'OS']:
			site['data'].extend([{'category': version, 'name': v.name, 'version': v.version} for v in get(version)])

		# SUBDOMAIN
		site['data'].extend([{'category': 'subdomain', 'hostname': sub.subdomain, 'title': sub.page_title, 'ip': sub.ip} for sub in get('Subdomain')])

		# INTERESTING
		site['data'].extend([{'category': 'Interesting', 'url': i.url, 'note': i.note} for i in get('Interesting')])

		# TOOLS
		site['data'].extend([{'category': 'Tool', 'name': t.tool_name, 'link': t.link, 'used_for': t.software} for t in get('Tool')])

		# VULNERABILITIES
		site['data'].extend([{'category': 'Vulnerability', 'name': v.software, 'version': v.version, 'link': v.link, 'num': v.num_vuln} for v in get('Vulnerability')])

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
		self.results = self.data['results'].results
		self.max_col_width = 60


	# Split the list of strings into a list of lists of strings
	# This is used to prevent very wide cols (e.g. when a precise version 
	# detection has not been possible and a long list of candidates is 
	# shown)
	def split_string(self, string_list):
		out, tmp = [], []

		while len(string_list):
			s = string_list.pop(0)
			if len(' | '.join(tmp + [s])) > self.max_col_width:
				out.append(' | '.join(tmp))
				tmp = [s]
			else:
				tmp.append(s)

		out.append(' | '.join(tmp))
		return out


	def print_results(self):
		_header = namedtuple('Header', ['title'])
		_caption = namedtuple('Caption', ['left', 'center', 'right'])
		_result = namedtuple('Result', ['left', 'center', 'right'])
		_space = namedtuple('Space', ['char'])
		_status = namedtuple('Status', ['runtime', 'urls', 'fingerprints'])
		_info = namedtuple('Info', ['left', 'span_rest'])


		p = self.data['printer']
		self.update_stats()

		output_lines = []
		
		# VERSION 
		for version in ['CMS', 'Platform', 'JavaScript', 'OS']:
			data = defaultdict(list)
			for result in self.get_results_of_type(version):
				data[result.name].append(self.replace_version_text(result.version))

			for result in data:
				version_list = self.split_string(sorted(data[result]))
				output_lines.append(_result(result, version_list[0] , version))
				output_lines.extend([_result('', v, '') for v in version_list[1:]])

		# SUBDOMAIN
		subdomains = self.get_results_of_type('Subdomain')
		if subdomains:
			output_lines.extend([_space(' '), _header('SUBDOMAINS'), _caption('Name', 'Page Title', 'IP')])
			output_lines.extend([_result(result.subdomain, result.page_title[:self.max_col_width], result.ip) for result in subdomains])

		# INTERESTING
		interesting = self.get_results_of_type('Interesting')
		if interesting:
			output_lines.extend([_space(' '), _header('INTERESTING'), _caption('URL', 'Note', 'Type')])
			output_lines.extend([_result(result.url, result.note, 'Interesting') for result in interesting])

		# PLATFORM NOTES
		platform_notes = sorted(self.get_results_of_type('PlatformNote'), key=lambda x: x.platform)
		if platform_notes:
			output_lines.extend([_space(' '), _header('PLATFORM OBSERVATIONS'), _caption('Platform', 'URL', 'Type')])
			output_lines.extend([_result(result.platform, result.url, 'Observation') for result in platform_notes])

		# TOOLS
		tools = self.get_results_of_type('Tool')
		if tools:
			output_lines.extend([_space(' '), _header('TOOLS'), _caption('Name', 'Link', 'Software')])
			output_lines.extend([_result(result.tool_name, result.link, result.software) for result in tools])

		# VULNERABILITES
		vulns = self.get_results_of_type('Vulnerability')
		if vulns:
			output_lines.extend([_space(' '), _header('VULNERABILITIES'), _caption('Affected', '#Vulns', 'Link')])
			output_lines.extend([_result(result.software + ' ' +result.version, result.num_vuln, result.link) for result in vulns])	

		# STATUS
		output_lines.append(_space(' '))
		output_lines.append(_space('_'))
		output_lines.append(_status(self.stats['runtime'], self.stats['url_count'], self.stats['fp_count']))

		# calculate the widths of the cols based on 'Results' and 'Status'
		widths = [max(map(len, col)) for col in zip(*[i for i in output_lines if type(i).__name__ in ['Result', 'Status']])]


		# prepend the site information
		# the site title will span 2 cols. It is added here to allow for calculation of the
		# actual width of the 2 last cols (instead of just setting the width to 2*self.max_col_width)
		intro = [
			_header('SITE INFO'),
			_caption('IP', 'Title', ''),
			_info(self.data['results'].site_info['ip'], self.data['results'].site_info['title'][:(widths[1] + widths[2])])
		]
		intro.extend([_space(' '), _header('VERSION'), _caption('Name', 'Versions', 'Type')])
		output_lines = intro + output_lines


		# the actual printing of the results
		for row in output_lines:
			if type(row).__name__ == 'Header':
				p.build_line((' ' + row.title + ' ').center(sum(widths)+4, '_'), 'blue', True)
			
			elif type(row).__name__ == 'Caption':
				p.build_line('  '.join((val.ljust(width) for val,width in zip(row, widths))), 'green', False)

			elif type(row).__name__ == 'Info':
				p.build_line('  '.join((val.ljust(width) for val,width in zip(row, [widths[0], widths[1]+widths[2]]))), 'normal', False)

			elif type(row).__name__ in ['Result', 'Status']:
				p.build_line('  '.join((val.ljust(width) for val,width in zip(row, widths))), 'normal', False)

			elif type(row).__name__ == 'Space':
				p.build_line(row.char*(sum(widths)+4), 'blue', True)

			p.print_built_line()


