

class Printer():
	def __init__(self, verbosity, color):
		self.verbosity = verbosity
		self.color = color

	def print(self, msg, verbosity_level=0, line_ending='\n'):
		if verbosity_level <= self.verbosity:

			if verbosity_level >= 2:
				color = 'yellow'
			else:
				color = 'normal'

			print(self.color.format(msg, color, bold=False), end=line_ending)


