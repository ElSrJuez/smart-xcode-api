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
_config = configparser.ConfigParser()
_read_files = _config.read(_CONFIG_PATH)
if not _read_files:
	sys.exit(f"FATAL: config.ini not found at {_CONFIG_PATH}")

def get(section, key, cast=None):
	try:
		value = _config[section][key]
		if cast:
			try:
				return cast(value)
			except ValueError:
				sys.exit(f"FATAL: Invalid value for [{section}] {key}: {value}")
		return value
	except KeyError:
		sys.exit(f"FATAL: Missing required config value: [{section}] {key}")