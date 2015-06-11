import os


class Printer:
	def __init__(self, global_verbosity):
		self.verbosity = global_verbosity

		self.verbosity_colors = [
			{'verbosity_level': 0, 'name': 'red', 'code': '31'},
			{'verbosity_level': 1, 'name': 'yellow', 'code': '33'},
			{'verbosity_level': 2, 'name': 'cyan', 'code': '36'},
			{'verbosity_level': 3, 'name': 'blue', 'code': '34'},
			{'verbosity_level': 4, 'name': 'green', 'code': '32'},
			{'verbosity_level': 5, 'name': 'magenta', 'code': '35'},
			{'verbosity_level': 6, 'name': 'normal', 'code': None},
		]

		self.current_line = ''

	def _find_color_by_name(self, name):
		for color in self.verbosity_colors:
			if color['name'] == name: return color['code']
		else:
			return None

	def _find_color_by_verbosity(self, verbosity):
		for color in self.verbosity_colors:
			if color['verbosity_level'] == verbosity: return color['code']
		else:
			return None

	def _format(self, string, color_code=None, bold=False):
		attr = []

		# bail if OS is windows
		# note: cygwin show be detected as 'posix'
		if os.name == 'nt': return string

		attr = [color_code] if color_code is not None else []

		if bold: attr.append('1')
		
		return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)		

	def build_line(self, text, color='normal', bold=False):
		color_code = self._find_color_by_name(color)
		self.current_line += self._format(text, color_code, bold)
	
	def print_built_line(self):
		try:
			if self.verbosity >= 0:
				if not self.current_line == '':
					print(self.current_line)
				self.current_line = ''
		except Exception as e:
			self.current_line = ''
			pass

	def print_debug_line(self, text, verbosity, bold=False):
		if self.verbosity >= verbosity:
			color = self._find_color_by_verbosity(verbosity)
			print(self._format(text, color, bold))

	def print_logo(self):
		logo = """\nwig - WebApp Information Gatherer\n\n"""
		if self.verbosity >= 0:
			print(logo)
