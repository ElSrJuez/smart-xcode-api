#
# Hierarchical data fetcher for admin UI
def get_full_hierarchy():
	"""
	Returns the full nested hierarchy: categories > channels > streams, using canonical dbops accessors.
	Returns a list of category dicts, each with a 'channels' key (list), each channel with a 'streams' key (list).
	"""
	dbops.init_module()
	# Fetch all categories
	categories = dbops._db.table('category_group').all() if hasattr(dbops._db, 'table') else []
	channels = dbops._db.table('channel').all() if hasattr(dbops._db, 'table') else []
	streams = dbops._db.table('stream').all() if hasattr(dbops._db, 'table') else []
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
# Add more as needed for admin features
