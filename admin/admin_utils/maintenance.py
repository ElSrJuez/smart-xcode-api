import os
from admin.admin_utils import admin_config

# Get the lock file path from config.ini
_LOCK_FILE_PATH = admin_config.get('app', 'maintenance_flag_filename')

def set_maintenance_mode(enabled: bool) -> bool:
    """
    Atomically create or delete the maintenance lock file.
    Returns True on success, False on failure.
    """
    try:
        if enabled:
            # Create the lock file atomically
            with open(_LOCK_FILE_PATH, 'w') as f:
                f.write('locked')
        else:
            if os.path.exists(_LOCK_FILE_PATH):
                os.remove(_LOCK_FILE_PATH)
        return True
    except Exception as e:
        # Optionally log the error here
        print(f"[maintenance] Error setting maintenance mode: {e}")
        return False

def is_maintenance_mode() -> bool:
    """
    Returns True if the maintenance lock file exists, else False.
    """
    return os.path.exists(_LOCK_FILE_PATH)
