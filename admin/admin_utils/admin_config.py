"""
admin_utils.admin_config

Minimal config loader for the admin app.
- Loads config.ini from project root.
- Fails fast if config or value is missing.
- No proxy code is imported or reused.
- Usage: from admin_utils import admin_config; value = admin_config.get('section', 'key', cast)
"""

import configparser
import os
import sys

_CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini'))
_config = configparser.ConfigParser(interpolation=None)
_read_files = _config.read(_CONFIG_PATH)
if not _read_files:
    print(f"FATAL: config.ini not found at {_CONFIG_PATH}\nPlease ensure the file exists and is readable.")
    sys.exit(1)

def get(section, key, cast=None):
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
