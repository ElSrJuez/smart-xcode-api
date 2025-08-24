"""
admin.routes.category

- Provides a truthful, schema-driven endpoint for category/channel hierarchy data for the admin UI.
"""


from flask import Blueprint, jsonify, request
from admin.admin_utils import admin_dbops

category_bp = Blueprint('category', __name__)


@category_bp.route('/admin/api/category/<category_group_id>', methods=['GET', 'POST'])
def category_detail(category_group_id):
    cat = admin_dbops.get_category_hierarchy_by_id(category_group_id)
    if not cat:
        return jsonify({"error": "Category not found"}), 404

    # POST: Enable/disable moderation
    if request.method == 'POST':
        data = request.get_json(force=True)
        enable = bool(data.get('include'))
        admin_dbops.update_category_group(cat['category_group_id'], {'include': enable})
        # Re-fetch to ensure truthfulness
        cat = admin_dbops.get_category_hierarchy_by_id(category_group_id)
        if not cat:
            return jsonify({"error": "Category not found after update"}), 404

    # Compute stats
    channels = cat.get('channels', [])
    num_channels = len(channels)
    num_streams = sum(len(ch.get('streams', [])) for ch in channels)

    # Only canonical fields, schema-driven
    result = {
        'category_group_id': cat.get('category_group_id'),
        'display_name': cat.get('display_name'),
        'identifiers': cat.get('identifiers', []),
        'include': cat.get('include'),
        'first_seen': cat.get('first_seen'),
        'last_seen': cat.get('last_seen'),
        'channels': channels,
        'stats': {
            'num_channels': num_channels,
            'num_streams': num_streams
        }
    }
    return jsonify(result)
