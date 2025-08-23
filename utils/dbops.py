"""
---
"""
"""
dbops.py — Canonical Database Operations for smart-xcode-api

This module provides all database operations for the passive discovery and admin moderation features of smart-xcode-api.

Design Agreements & Tooling:
- Self-initializing: On import or first use, checks for existence of the discovery DB and schema; creates if missing.
- All file paths and options are config-driven (see config.ini [db] section).
- Schema as data: Loads and validates against the canonical schema (JSON).
- Exposes only public functions for CRUD, deduplication, tagging, pruning, etc.
- Uses canonical logging for all operations and errors.
- No in-code defaults; all behavior is config-driven.
- Modular, testable, and minimal side effects.
- Uses TinyDB for in-memory+file document storage (no custom cache needed for most use cases).
- Uses hashlib for identifier normalization/deduplication.
- All parsing and ingestion modules should use standard Python libraries or well-known packages (see discovery.py for details).

---
"""


import os
import json
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from utils import config, logging


_db_path = config.get('db', 'discovery_db_path')
_schema_path = config.get('db', 'schema_path')


# TinyDB instance (singleton)
_db = None

def _get_db():
	_self_init()
	return _db



def _self_init():
	global _db
	if not os.path.exists(_db_path):
		# Create empty DB file
		with open(_db_path, 'w', encoding='utf-8') as f:
			json.dump({}, f)
		logging.log_message('info', f"Created new discovery DB at {_db_path}")
	if not os.path.exists(_schema_path):
		raise FileNotFoundError(f"Schema file not found: {_schema_path}")
	# Always re-initialize TinyDB instance to ensure _db is valid
	_db = TinyDB(_db_path, storage=CachingMiddleware(JSONStorage))


# Load schema on module import
_schema = None
def _load_schema():
	global _schema
	with open(_schema_path, 'r', encoding='utf-8') as f:
		_schema = json.load(f)
_self_init()
_load_schema()


def add_object(category, data):
	"""Add a new object to the database in the given category."""
	validate_against_schema(category, data)
	db = _get_db()
	table = db.table(category)
	obj_id = table.insert(data)
	logging.log_message('info', f"Added object to {category}: {obj_id}")
	return obj_id


def update_object(category, identifiers, data):
	"""Update an existing object in the database by identifiers."""
	validate_against_schema(category, data)
	db = _get_db()
	table = db.table(category)
	q = Query()
	cond = None
	for k, v in identifiers.items():
		cond = (q[k] == v) if cond is None else (cond & (q[k] == v))
	updated = table.update(data, cond)
	logging.log_message('info', f"Updated object(s) in {category} with {identifiers}: {updated}")
	return updated


def get_object(category, identifiers):
	"""Retrieve a single object by identifiers. Returns None if not found."""
	db = _get_db()
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


def find_objects(category, filters=None):
	"""Find objects in a category matching filters. If filters is None or empty, returns all objects."""
	db = _get_db()
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


def delete_object(category, identifiers):
	"""Delete an object from the database by identifiers. Returns number of objects deleted."""
	db = _get_db()
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

def touch_object(category, identifiers, data):
	"""Add if new, or update last_seen if exists. Returns object id or update count."""
	db = _get_db()
	table = db.table(category)
	q = Query()
	cond = None
	for k, v in identifiers.items():
		cond = (q[k] == v) if cond is None else (cond & (q[k] == v))
	existing = table.get(cond)
	if existing:
		# Update last_seen (and any other updatable fields in data)
		update_fields = {k: v for k, v in data.items() if k != 'id'}
		result = table.update(update_fields, cond)
		logging.log_message('info', f"Touched (updated) object in {category} with {identifiers}: {result}")
		return result
	else:
		# Validate and add new
		validate_against_schema(category, data)
		obj_id = table.insert(data)
		logging.log_message('info', f"Touched (added) new object in {category}: {obj_id}")
		return obj_id

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
	if _schema is None:
		raise RuntimeError("Schema not loaded.")
	# Find the schema object for this category/type
	schema_obj = None
	for obj in _schema.get('objects', []):
		if obj['type'] == category:
			schema_obj = obj
			break
	if not schema_obj:
		raise ValueError(f"No schema definition for category/type: {category}")
	required_fields = set(schema_obj['fields'])
	data_fields = set(data.keys())
	missing = required_fields - data_fields
	extra = data_fields - required_fields
	if missing:
		raise ValueError(f"Missing required fields for {category}: {missing}")
	if extra:
		raise ValueError(f"Extra fields not allowed for {category}: {extra}")
	return True

def deduplicate_objects(category):
	"""Merge or deduplicate objects in a category based on identifiers."""
	pass

