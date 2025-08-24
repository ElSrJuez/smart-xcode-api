"""
routes.admin_home

Sample blueprint for the admin app.
- Registers a /hello route for demonstration.
- Can be expanded for modular admin features.
"""

from flask import Blueprint
from admin.admin_utils import admin_logging

admin_home_bp = Blueprint('admin_home', __name__)

@admin_home_bp.route('/hello')
def hello():
    admin_logging.log_message('info', "'/hello' route accessed.")
    return "Hello from the admin blueprint!"
