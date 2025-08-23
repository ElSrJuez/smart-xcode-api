
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
from utils.config import (
	ADMIN_LOGGING, ADMIN_LOG_PATH, API_LOG_FILE, API_DISCOVER_LOG_PATH, API_RAW_PATH,
	GLOBAL_LOGGING_FORMAT, GLOBAL_COMMON_LOG_FILE
)

# Private: logger cache to avoid duplicate handlers
_loggers = {}

def _get_log_file_for_caller():
	"""Determine log file path based on calling module context."""
	stack = inspect.stack()
	for frame in stack[1:]:
		mod = frame.filename.replace('\\', '/').lower()
		if 'admin' in mod:
			return ADMIN_LOG_PATH
		if 'api' in mod:
			return API_LOG_FILE
	return GLOBAL_COMMON_LOG_FILE

def _get_logger():
	log_file = _get_log_file_for_caller()
	if log_file not in _loggers:
		logger = logging.getLogger(log_file)
		logger.setLevel(getattr(logging, ADMIN_LOGGING, logging.WARNING))
		# Avoid duplicate handlers
		if not logger.handlers:
			os.makedirs(os.path.dirname(log_file), exist_ok=True)
			handler = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8')
			handler.setFormatter(logging.Formatter(GLOBAL_LOGGING_FORMAT))
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