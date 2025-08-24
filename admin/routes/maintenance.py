"""
admin.routes.maintenance

- Provides atomic, truthful maintenance mode toggle and status endpoints for the admin UI.
- All logic is config-driven and fail-fast.
"""

from flask import Blueprint, jsonify, request
from admin.admin_utils import maintenance

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/admin/api/maintenance', methods=['GET', 'POST'])
def maintenance_toggle():
    if request.method == 'GET':
        # Truthful status
        status = maintenance.is_maintenance_mode()
        return jsonify({"status": status})
    elif request.method == 'POST':
        data = request.get_json(force=True)
        enable = bool(data.get('enable'))
        ok = maintenance.set_maintenance_mode(enable)
        status = maintenance.is_maintenance_mode()  # Always re-check after action
        return jsonify({"success": ok, "status": status})
