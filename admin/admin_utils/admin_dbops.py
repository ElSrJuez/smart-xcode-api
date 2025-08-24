"""
admin_utils.admin_dbops

Minimal TinyDB operations for the admin app.
- Loads DB path from config.ini via admin_config.
- Provides get_db() for use in admin features.
- No proxy code is imported or reused.
"""

from tinydb import TinyDB
from admin_utils import admin_config
import os

_DB_PATH = admin_config.get('db', 'discovery_db_path', str)

# Ensure DB directory exists
os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)

def get_db():
    """Return a TinyDB instance for admin use."""
    return TinyDB(_DB_PATH)
