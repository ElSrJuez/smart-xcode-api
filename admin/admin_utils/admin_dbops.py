# Canonical accessor for a single category_group by id
def get_category_by_id(category_group_id):
	"""
	Returns a single category_group object by canonical id, or None if not found.
	"""
	return dbops.get_object('category_group', {'category_group_id': category_group_id})
#
# Schema-driven field accessor for admin UI
def get_category_fields(category_name):
	"""
	Returns the list of field definitions for a given category from the loaded schema.
	"""
	return dbops.get_schema_field(category_name, 'fields')
#
# Hierarchical data fetcher for admin UI

def build_category_hierarchy(categories, channels, streams):
	"""
	Given lists of categories, channels, and streams, build the nested hierarchy.
	Returns a list of category dicts, each with a 'channels' key (list), each channel with a 'streams' key (list).
	"""
	# Index channels and streams by parent id
	channels_by_cat = {}
	for ch in channels:
		cat_id = ch.get('category_group_id')
		if cat_id:
			channels_by_cat.setdefault(cat_id, []).append(ch)
	streams_by_chan = {}
	for st in streams:
		chan_id = st.get('channel_id')
		if chan_id:
			streams_by_chan.setdefault(chan_id, []).append(st)
	# Build hierarchy
	for cat in categories:
		cat_id = cat.get('category_group_id')
		cat['channels'] = []
		for ch in channels_by_cat.get(cat_id, []):
			ch_id = ch.get('channel_id')
			ch['streams'] = streams_by_chan.get(ch_id, [])
			cat['channels'].append(ch)
	return categories

def get_full_hierarchy():
	"""
	Returns the full nested hierarchy: categories > channels > streams, using canonical dbops accessors.
	"""
	dbops.init_module()
	categories = dbops._db.table('category_group').all() if hasattr(dbops._db, 'table') else []
	channels = dbops._db.table('channel').all() if hasattr(dbops._db, 'table') else []
	streams = dbops._db.table('stream').all() if hasattr(dbops._db, 'table') else []
	return build_category_hierarchy(categories, channels, streams)

def get_category_hierarchy_by_id(category_group_id):
	"""
	Returns a single category_group dict with its nested channels and streams, or None if not found.
	"""
	dbops.init_module()
	cat = dbops.get_object('category_group', {'category_group_id': category_group_id})
	if not cat:
		return None
	channels = dbops._db.table('channel').all() if hasattr(dbops._db, 'table') else []
	streams = dbops._db.table('stream').all() if hasattr(dbops._db, 'table') else []
	# Only build hierarchy for this category
	return build_category_hierarchy([cat], channels, streams)[0]
"""
admin_utils.admin_dbops

Re-exports canonical DB and schema accessors for the admin app.
All admin DB operations must go through this module, which delegates to utils.dbops.
"""

from utils import dbops

# Re-expose only the needed functions for admin use
init_module = dbops.init_module
get_schema_field = dbops.get_schema_field
get_category_for_action = dbops.get_category_for_action
get_canonical_id_field = dbops.get_canonical_id_field

def update_category_group(category_group_id, data):
	"""
	Canonical, schema-driven update for a category_group object.
	Uses dbops.touch_object to update only allowed fields.
	"""
	# The canonical identifier field for category_group is 'category_group_id'
	return dbops.touch_object('category_group', {'category_group_id': category_group_id}, data)
