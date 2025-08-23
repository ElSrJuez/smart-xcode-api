"""
Config module for smart-xcode-api.

Usage:
	from utils import config
	_MY_SETTING = config.get('api.apipxy', 'target_url')
	_MY_INT = config.get('api.apipxy', 'api_port', int)

Principles:
- Absolutely no in-code defaults, hardcoded values, or fail-/fall-backs are permitted.
- All configuration is loaded from config.ini. If a config value is missing, an error is raised and the app gracefully stops.
- No global ALL_CAPS variables; each module loads its own _PRIVATE_VARIABLES as needed.
- Deterministic: fails fast if a required value is missing or invalid.
- Section/key names match config.ini structure.

TODO:
- Add optional DEBUG-mode logging of all config.get() requests (log section/key/stacktrace if enabled).
"""


import configparser
import os
import sys

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
_config = configparser.ConfigParser(interpolation=None)
_read_files = _config.read(_CONFIG_PATH)
if not _read_files:
	print(f"FATAL: config.ini not found at {_CONFIG_PATH}\nPlease ensure the file exists and is readable.")
	sys.exit(1)

def get(section, key, cast=None):
	"""
	TODO: In the future, use canonical logging for all config errors.
	"""
	try:
		value = _config[section][key]
		if cast:
			try:
				return cast(value)
			except ValueError:
				print(f"FATAL: Invalid value for [{section}] {key}: {value}\nCheck your config.ini for correct types.")
				sys.exit(1)
		return value
	except KeyError:
		print(f"FATAL: Missing required config value: [{section}] {key}\nPlease add this setting to your config.ini under the correct section.")
		sys.exit(1)