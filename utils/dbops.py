

import os
import json
import hashlib
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from utils import config, logging



# ============================
# Module-level Config & State
# ============================
_DISCOVERY_DB_PATH = None
_SCHEMA_PATH = None

_db = None
_schema = None
_INIT_OK = False

_DEBUG_MODE = False
try:
	log_level = config.get('app', 'logging_common_level', str)
	if log_level and log_level.upper() == 'DEBUG':
		_DEBUG_MODE = True
except Exception:
	pass

# ============================
# Private Helpers and Initialization
# ============================
def _self_init():
	global _db, _DISCOVERY_DB_PATH, _SCHEMA_PATH
	if _DISCOVERY_DB_PATH is None or _SCHEMA_PATH is None:
		_DISCOVERY_DB_PATH = config.get('db', 'discovery_db_path')
		_SCHEMA_PATH = config.get('db', 'schema_path')
	if not os.path.exists(_DISCOVERY_DB_PATH):
		with open(_DISCOVERY_DB_PATH, 'w', encoding='utf-8') as f:
			json.dump({}, f)
		logging.log_message('info', f"Created new discovery DB at {_DISCOVERY_DB_PATH}")
	if not os.path.exists(_SCHEMA_PATH):
		raise FileNotFoundError(f"Schema file not found: {_SCHEMA_PATH}")
	_db = TinyDB(_DISCOVERY_DB_PATH, storage=CachingMiddleware(JSONStorage))

def _load_schema():
	global _schema
	if _SCHEMA_PATH is None:
		raise RuntimeError("SCHEMA_PATH is not set.")
	with open(_SCHEMA_PATH, 'r', encoding='utf-8') as f:
		_schema = json.load(f)


# Initialize DB and schema at import time
try:
	_self_init()
	_load_schema()
	assert _db is not None, "DB initialization failed"
	assert _schema is not None, "Schema initialization failed"
	_INIT_OK = True
	logging.log_message('info', 'dbops.py: Initialization complete, DB and schema loaded.')
except Exception as e:
	_INIT_OK = False
	logging.log_message('error', f'dbops.py: Initialization failed: {e}')

def get_category_for_action(action):
	"""
	Map an API action to a category using the loaded schema.
	Returns the category name if found, else None.
	"""
	if not _INIT_OK:
		logging.log_message('error', 'dbops.py: get_category_for_action called before initialization completed.')
		return None
	global _schema
	if not isinstance(_schema, dict):
		raise RuntimeError("Schema is not loaded or is invalid.")
	for obj in _schema.get('object_categories', []):
		if 'actions' in obj and action in obj['actions']:
			return obj['name']
	return None

"""
dbops.py — Canonical Database Operations for smart-xcode-api

All database operations for passive discovery and admin moderation features.
Design: Self-initializing, config-driven, schema-validated, canonical logging, modular, minimal side effects.
"""

def deduplicate_object(category, data):
	"""
	Deduplicate an object in the given category using normalized identifiers.
	If a duplicate exists, merge fields and return the merged object.
	If not, return the original data.
	"""
	db = _get_db()
	table = db.table(category)
	# Collect all possible deduplication values (canonical id and identifier values)
	id_values = set()
	identifier_tuples = set()
	identifier_values = set()
	if 'id' in data and data['id']:
		val = str(data['id']).strip().lower()
		if _DEBUG_MODE:
			logging.log_message('debug', f"deduplicate_object: adding id value to id_values: {repr(val)} type={type(val)}")
		id_values.add(val)
	for key in data:
		if key.endswith('_id') and isinstance(data[key], str):
			val = data[key].strip().lower()
			if _DEBUG_MODE:
				logging.log_message('debug', f"deduplicate_object: adding _id value to id_values: {repr(val)} type={type(val)} key={key}")
			id_values.add(val)
	if 'identifiers' in data and isinstance(data['identifiers'], list):
		for ident in data['identifiers']:
			if _DEBUG_MODE:
				logging.log_message('debug', f"deduplicate_object: identifiers entry: {repr(ident)} type={type(ident)}")
			if isinstance(ident, dict) and 'field' in ident and 'value' in ident and ident['field'] and ident['value']:
				field = str(ident['field']).strip().lower()
				value = str(ident['value']).strip().lower()
				dedup_key = (field, value)
				if _DEBUG_MODE:
					logging.log_message('debug', f"deduplicate_object: adding identifier tuple to identifier_tuples: {repr(dedup_key)} type={type(dedup_key)} from ident={repr(ident)}")
				identifier_tuples.add(dedup_key)
				identifier_values.add(value)
	if not (id_values or identifier_tuples):
		return data  # No deduplication possible
	q = Query()
	cond = None
	# Match on id fields
	for v in id_values:
		for id_field in [k for k in data if k.endswith('_id')]:
			cond = (q[id_field] == v) if cond is None else (cond | (q[id_field] == v))
		cond = (q.id == v) if cond is None else (cond | (q.id == v))
	# Match on identifier values only (not tuples)
	for v in identifier_values:
		cond = cond | (q.identifiers.any(Query().value == v)) if cond is not None else (q.identifiers.any(Query().value == v))
	matches = table.search(cond) if cond is not None else []
	if matches:
		existing = matches[0]
		merged = dict(existing)
		merged.update({k: v for k, v in data.items() if v is not None})
		return merged
	return data


# Deduplication logic is now in api/discovery.py for modularity.
"""
git ---
"""



def _get_db():
	global _db
	if _db is None:
		_self_init()
	return _db


def add_object(category, data):
	"""Add a new object to the database in the given category."""
	dedup_values = set()
	if 'id' in data and data['id']:
		val = str(data['id']).strip().lower()
		if _DEBUG_MODE:
			logging.log_message('debug', f"deduplicate_object: adding id value to dedup_values: {repr(val)} type={type(val)}")
		dedup_values.add(val)
	# Also check for canonical id fields (e.g., category_group_id, channel_id, stream_id)
	for key in data:
		if key.endswith('_id') and isinstance(data[key], str):
			val = data[key].strip().lower()
			if _DEBUG_MODE:
				logging.log_message('debug', f"deduplicate_object: adding _id value to dedup_values: {repr(val)} type={type(val)} key={key}")
			dedup_values.add(val)
	# Add all identifier values
	if 'identifiers' in data and isinstance(data['identifiers'], list):
		for ident in data['identifiers']:
			if _DEBUG_MODE:
				logging.log_message('debug', f"deduplicate_object: identifiers entry: {repr(ident)} type={type(ident)}")
			if isinstance(ident, dict) and 'value' in ident and ident['value']:
				val = str(ident['value']).strip().lower()
				if _DEBUG_MODE:
					logging.log_message('debug', f"deduplicate_object: adding identifier value to dedup_values: {repr(val)} type={type(val)} from ident={repr(ident)}")
				dedup_values.add(val)
	logging.log_message('debug', f"CALLCHAIN: ENTER validate_against_schema category={category} data={repr(data)}")
	try:
		validate_against_schema(category, data)
		logging.log_message('debug', f"CALLCHAIN: EXIT validate_against_schema category={category} data={repr(data)}")
		db = _get_db()
		if db is None:
			raise RuntimeError("Database is not initialized.")
		table = db.table(category)
		obj_id = table.insert(data)
		logging.log_message('info', f"Added object to {category}: {obj_id}")
		return obj_id
	except Exception as e:
		logging.log_message('error', f"add_object failed for {category} with data={data}: {e}")
		raise
def get_object(category, identifiers):
	"""Retrieve a single object by identifiers. Returns None if not found."""
	if not _INIT_OK:
		logging.log_message('error', 'dbops.py: get_object called before initialization completed.')
		return None
	try:
		db = _get_db()
		if db is None:
			raise RuntimeError("Database is not initialized.")
		table = db.table(category)
		q = Query()
		cond = None
		for k, v in identifiers.items():
			cond = (q[k] == v) if cond is None else (cond & (q[k] == v))
		result = table.get(cond)
		if result is None:
			logging.log_message('warning', f"No object found in {category} with {identifiers}")
		else:
			logging.log_message('info', f"Fetched object from {category} with {identifiers}: {result}")
		return result
	except Exception as e:
		logging.log_message('error', f"get_object failed for {category} with identifiers={identifiers}: {e}")
		raise


def find_objects(category, filters=None):
	"""Find objects in a category matching filters. If filters is None or empty, returns all objects."""
	if not _INIT_OK:
		logging.log_message('error', 'dbops.py: find_objects called before initialization completed.')
		return None
	try:
		db = _get_db()
		if db is None:
			raise RuntimeError("Database is not initialized.")
		table = db.table(category)
		if not filters:
			results = table.all()
			logging.log_message('info', f"Found all objects in {category}: {len(results)} found")
			return results
		q = Query()
		cond = None
		for k, v in filters.items():
			cond = (q[k] == v) if cond is None else (cond & (q[k] == v))
		results = table.search(cond) if cond is not None else table.all()
		logging.log_message('info', f"Found objects in {category} with {filters}: {len(results)} found")
		return results
	except Exception as e:
		logging.log_message('error', f"find_objects failed for {category} with filters={filters}: {e}")
		raise


def delete_object(category, identifiers):
	"""Delete an object from the database by identifiers. Returns number of objects deleted."""
	if not _INIT_OK:
		logging.log_message('error', 'dbops.py: delete_object called before initialization completed.')
		return 0
	try:
		db = _get_db()
		if db is None:
			raise RuntimeError("Database is not initialized.")
		table = db.table(category)
		q = Query()
		cond = None
		for k, v in identifiers.items():
			cond = (q[k] == v) if cond is None else (cond & (q[k] == v))
		deleted = table.remove(cond)
		if deleted:
			logging.log_message('info', f"Deleted object(s) from {category} with {identifiers}: {deleted}")
		else:
			logging.log_message('warning', f"No object deleted from {category} with {identifiers}")
		return len(deleted) if deleted else 0
	except Exception as e:
		logging.log_message('error', f"delete_object failed for {category} with identifiers={identifiers}: {e}")
		raise

def touch_object(category, identifiers, data):
	"""Add if new, or update last_seen if exists. Deduplicates before upsert. Returns object id or update count."""
	logging.log_message('debug', f"CALLCHAIN: ENTER touch_object category={category} identifiers={repr(identifiers)} data={repr(data)}")
	if not _INIT_OK:
		logging.log_message('error', 'dbops.py: touch_object called before initialization completed.')
		return 0
	db = _get_db()
	if db is None:
		raise RuntimeError("Database is not initialized.")
	table = db.table(category)
	merged_data = deduplicate_object(category, data)
	q = Query()
	cond = None
	for k, v in identifiers.items():
		cond = (q[k] == v) if cond is None else (cond & (q[k] == v))
	existing = table.get(cond)
	if existing:
		if isinstance(merged_data, dict):
			update_fields = {k: v for k, v in merged_data.items() if k != 'id'}
			result = table.update(update_fields, cond)
			logging.log_message('debug', f"CALLCHAIN: EXIT touch_object (update) category={category} identifiers={repr(identifiers)} result={result}")
			logging.log_message('info', f"Touched (deduped+updated) object in {category} with {identifiers}: {result}")
			return result
		else:
			logging.log_message('error', f"Merged data is not a dict: {merged_data}")
			return 0
	else:
		if isinstance(merged_data, dict):
			validate_against_schema(category, merged_data)
			obj_id = table.insert(merged_data)
			logging.log_message('debug', f"CALLCHAIN: EXIT touch_object (insert) category={category} identifiers={repr(identifiers)} obj_id={obj_id}")
			logging.log_message('info', f"Touched (deduped+added) new object in {category}: {obj_id}")
			return obj_id
		else:
			logging.log_message('error', f"Merged data is not a dict: {merged_data}")
			return 0

def prune_stale_objects(category, cutoff_timestamp):
	"""Remove or mark as inactive any objects not seen since cutoff_timestamp."""
	pass

def log_discovery_event(event_type, details):
	"""Log a discovery event for audit/troubleshooting."""
	pass

def update_stream_status(channel_id, url, status_obj):
	"""Update the status/quality object for a stream URL associated with a channel."""
	pass

def validate_against_schema(category, data):
	"""Validate incoming data against the canonical schema before insert/update."""
	logging.log_message('debug', f"CALLCHAIN: ENTER validate_against_schema category={category} data={repr(data)}")
	if _schema is None:
		logging.log_message('debug', f"CALLCHAIN: _schema is None")
		raise RuntimeError("Schema not loaded.")
	schema_obj = None
	if not isinstance(_schema, dict):
		logging.log_message('debug', f"CALLCHAIN: _schema is not dict")
		raise RuntimeError("Schema is not loaded or is invalid.")
	for obj in _schema.get('object_categories', []):
		if obj['name'] == category:
			schema_obj = obj
			break
	if not schema_obj:
		logging.log_message('debug', f"CALLCHAIN: No schema definition for category/type: {category}")
		raise ValueError(f"No schema definition for category/type: {category}")
	logging.log_message('debug', f"CALLCHAIN: schema_obj['fields'] (raw)={schema_obj['fields']}")
	logging.log_message('debug', f"CALLCHAIN: data.keys() (raw)={list(data.keys())}")
	required_field_names = set(f['name'] for f in schema_obj['fields'])
	logging.log_message('debug', f"CALLCHAIN: required_field_names={required_field_names}")
	data_fields = set(data.keys())
	logging.log_message('debug', f"CALLCHAIN: data_fields={data_fields}")
	missing = required_field_names - data_fields
	extra = data_fields - required_field_names
	logging.log_message('debug', f"CALLCHAIN: missing={missing} extra={extra}")
	if missing:
		logging.log_message('debug', f"CALLCHAIN: Missing required fields for {category}: {missing}")
		raise ValueError(f"Missing required fields for {category}: {missing}")
	if extra:
		logging.log_message('debug', f"CALLCHAIN: Extra fields not allowed for {category}: {extra}")
		raise ValueError(f"Extra fields not allowed for {category}: {extra}")
	logging.log_message('debug', f"CALLCHAIN: EXIT validate_against_schema category={category} data={repr(data)}")
	return True

def deduplicate_objects(category):
	"""Merge or deduplicate objects in a category based on identifiers."""
	pass


