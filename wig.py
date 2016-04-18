#!/usr/bin/env python3

import argparse
from wig.wig import Wig

def parse_args(url=None):
	parser = argparse.ArgumentParser(description='WebApp Information Gatherer')

	parser.add_argument('url', nargs='?', type=str, default=None,
		help='The url to scan e.g. http://example.com')

	parser.add_argument('-l', type=str, default=None, dest="input_file",
		help='File with urls, one per line.')

	parser.add_argument('-q', action='store_true', dest='quiet', default=False,
		help='Set wig to not prompt for user input during run')

	parser.add_argument('-n', type=int, default=1, dest="stop_after",
		help='Stop after this amount of CMSs have been detected. Default: 1')

	parser.add_argument('-a', action='store_true', dest='run_all', default=False,
		help='Do not stop after the first CMS is detected')

	parser.add_argument('-m', action='store_true', dest='match_all', default=False,
		help='Try harder to find a match without making more requests')

	parser.add_argument('-u', action='store_true', dest='user_agent',
		default='Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
		help='User-agent to use in the requests')

	parser.add_argument('-d', action='store_false', dest='subdomains', default=True,
		help='Disable the search for subdomains')

	parser.add_argument('-t', dest='threads', default=10, type=int,
		help='Number of threads to use')

	parser.add_argument('--no_cache_load', action='store_true', default=False,
		help='Do not load cached responses')

	parser.add_argument('--no_cache_save', action='store_true', default=False,
		help='Do not save the cache for later use')

	parser.add_argument('-N', action='store_true', dest='no_cache', default=False,
		help='Shortcut for --no_cache_load and --no_cache_save')

	parser.add_argument('--verbosity', '-v', action='count', default=0,
		help='Increase verbosity. Use multiple times for more info')

	parser.add_argument('--proxy', dest='proxy', default=None,
		help='Tunnel through a proxy (format: localhost:8080)')

	parser.add_argument('-w', dest='output_file', default=None,
		help='File to dump results into (JSON)')

	args = parser.parse_args()

	if url is not None:
		args.url = url

	if args.input_file is None and args.url is None:
		raise Exception('No target(s) specified')

	if args.no_cache:
		args.no_cache_load = True
		args.no_cache_save = True

	return args


# if called from the command line
if __name__ == '__main__':
	args = parse_args()

	try:
		wig = Wig(args)
		wig.run()
	except KeyboardInterrupt:
		raise
