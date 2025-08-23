
"""
Canonical logging setup for the project.

Principles:
- Self-initializes on import so that calling modules keep concerns separated and simple.
- Clear distinction between public and private functions and variables.
- Simplicity and separation of concerns: modules do not import or configure logging directly.

Design Parameters:
1. Minimize imports in other modules: provide a single canonical log function.
2. Support separate log files/handlers for API and admin features, as configured in config.ini.
3. Avoid file locking issues by managing handlers centrally and using per-module or rotating handlers.
4. All logging format, file, and level configuration is deterministic and comes from config.ini.
5. Automatically detects and reports calling module in the resulting log entries.
"""



import logging
import os
import inspect
from logging.handlers import RotatingFileHandler


from utils import config


# Preload all config values needed for logging into private variables
_ADMIN_LOG_PATH = config.get('admin.admin_app', 'logging_admin_log_path')
_API_LOG_FILE = config.get('api.apipxy', 'logging_api_log_file')
_COMMON_LOG_FILE = config.get('app', 'logging_common_log_file')
_ADMIN_LOG_LEVEL = config.get('admin.admin_app', 'logging_admin_app_log_level', str).upper()
_COMMON_LOG_LEVEL = config.get('app', 'logging_common_level', str).upper()
_LOG_FORMAT = config.get('utils.logging', 'format')


# Private: logger cache to avoid duplicate handlers
_loggers = {}

def _get_log_file_for_caller():
	"""Determine log file path based on calling module context."""
	stack = inspect.stack()
	for frame in stack[1:]:
		mod = frame.filename.replace('\\', '/').lower()
		if 'admin' in mod:
			return _ADMIN_LOG_PATH
		if 'api' in mod:
			return _API_LOG_FILE
	return _COMMON_LOG_FILE

def _get_logger():
	log_file = _get_log_file_for_caller()
	if log_file not in _loggers:
		logger = logging.getLogger(log_file)
		# Use admin level if admin, else fallback to app level, else WARNING
		if log_file == _ADMIN_LOG_PATH:
			level = getattr(logging, _ADMIN_LOG_LEVEL, logging.WARNING)
		else:
			level = getattr(logging, _COMMON_LOG_LEVEL, logging.WARNING)
		logger.setLevel(level)
		# Avoid duplicate handlers
		if not logger.handlers:
			os.makedirs(os.path.dirname(log_file), exist_ok=True)
			handler = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8')
			handler.setFormatter(logging.Formatter(_LOG_FORMAT))
			logger.addHandler(handler)
		_loggers[log_file] = logger
	return _loggers[log_file]

def log_message(level, msg, *args, **kwargs):
	"""
	Canonical logging function. Usage: log_message('info', 'message')
	Level: 'debug', 'info', 'warning', 'error', 'critical'
	"""
	logger = _get_logger()
	log_func = getattr(logger, level.lower(), logger.info)
	log_func(msg, *args, **kwargs)