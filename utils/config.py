# Strict config loader: loads all required config values from config.ini, fails fast if missing, exposes as constants

# the config strategy only reads configuration when the respective calling module
import configparser
import os
import sys

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config = configparser.ConfigParser()
read_files = config.read(CONFIG_PATH)
if not read_files:
	sys.exit(f"FATAL: config.ini not found at {CONFIG_PATH}")

def require(section, key, cast=None):
	try:
		value = config[section][key]
		if cast:
			return cast(value)
		return value
	except KeyError:
		sys.exit(f"FATAL: Missing required config value: [{section}] {key}")
	except ValueError:
		sys.exit(f"FATAL: Invalid value for [{section}] {key}: {value}")


# API backend
API_BACKEND_URL = require('api_backend', 'target_url')
API_BACKEND_USERNAME = require('api_backend', 'target_username')
API_BACKEND_PASSWORD = require('api_backend', 'target_password')
API_OVERRIDE_CREDS = require('api_backend', 'override_creds', lambda v: v.lower() == 'true')

# API log phase
API_LOGGING_PHASE = require('api_log', 'logging_phase').lower()

# API settings and paths
API_FORCE_NON_GZIP = require('api', 'fiddling_force_non_gzip', lambda v: v.lower() == 'true')
API_PORT = require('api', 'port', int)
API_LOG_FILE = require('api', 'api_log_file')
API_RAW_PATH = require('api', 'api_raw_path')
API_DISCOVER_LOG_PATH = require('api', 'api_discover_log_path')

# Admin
ADMIN_PORT = require('admin', 'port', int)
ADMIN_LOGGING = require('admin', 'logging').upper()
ADMIN_LOG_PATH = require('admin', 'admin_log_path')

# Global
GLOBAL_HOST = require('global', 'host')
GLOBAL_LOGGING_FORMAT = require('global_logging', 'logging_format')
GLOBAL_COMMON_LOG_FILE = require('global_logging', 'common_log_file')

# this is the one and only canonical config module