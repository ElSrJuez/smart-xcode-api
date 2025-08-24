"""
admin_utils.admin_logging

Minimal logging utility for the admin app.
- Uses config from config.ini via admin_config.
- Provides a canonical log_message(level, msg) function.
- Log file and level are determined by config.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from admin.admin_utils import admin_config

_LOG_PATH = admin_config.get('admin.admin_app', 'logging_admin_log_path')
_LOG_LEVEL = admin_config.get('admin.admin_app', 'logging_admin_app_log_level', str).upper()
_LOG_FORMAT = '%(asctime)s %(levelname)s [%(module)s] %(message)s'

_logger = None

def _get_logger():
    global _logger
    if _logger is None:
        os.makedirs(_LOG_PATH, exist_ok=True)
        log_file = os.path.join(_LOG_PATH, 'admin_app.log')
        logger = logging.getLogger('admin_app')
        logger.setLevel(getattr(logging, _LOG_LEVEL, logging.INFO))
        if not logger.handlers:
            handler = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8')
            handler.setFormatter(logging.Formatter(_LOG_FORMAT))
            logger.addHandler(handler)
        _logger = logger
    return _logger

def log_message(level, msg, *args, **kwargs):
    logger = _get_logger()
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(msg, *args, **kwargs)
