"""
discovery.py — Canonical Discovery and Parsing Logic

This module provides canonical parsing, normalization, and ingestion for category_group and related objects.
All imports are at the top, following project conventions.
"""

from utils import logging as logmod
import m3u8
import re
import utils.dbops as dbops

# Canonical construction of a category_group object from raw input
def create_category_group_object(raw_obj):
  """
  Synthesize a canonical, schema-compliant category_group object from raw input.
  Args:
    raw_obj (dict): The raw category/group object from XC API or M3U source.
  Returns:
    dict: A fully-formed, schema-compliant category_group object.
  Raises:
    ValueError: If required incoming fields are missing.
  """
  if 'category_name' not in raw_obj:
    raise ValueError("Missing required field 'category_name' in raw_obj")

  display_name = raw_obj['category_name']
  category_group_id = canonical_category_group_id(display_name)
  # Canonically build identifiers using schema
  identifiers = create_identifiers_object(raw_obj, 'category_group')

  canonical = {
    "category_group_id": category_group_id,
    "display_name": display_name,
    "identifiers": identifiers,
    # Pass through parent_id if present (for diagnostics, not canonical)
    **({"parent_id": raw_obj["parent_id"]} if "parent_id" in raw_obj else {})
  }
  return canonical

#
# Canonical construction of an identifiers list from raw input
def create_identifiers_object(raw_obj, object_categories_object_name):
  """
  Canonically construct the identifiers list for an object, using the canbeidentifier fields from the schema.
  Args:
    raw_obj (dict): The raw input object from source data.
    object_categories_object_name (str): The object category name (e.g., 'category_group').
  Returns:
    list: List of identifier dicts, each with 'field' and 'value'.
  """

  canbeidentifier_fields = dbops.get_schema_field(object_categories_object_name, 'canbeidentifier')
  if not canbeidentifier_fields:
    logmod.log_message('warning', f"No identifier fields found in schema for object category '{object_categories_object_name}'")
  identifiers = []
  for field in canbeidentifier_fields:
    if field in raw_obj and raw_obj[field] is not None:
      identifiers.append({"field": field, "value": str(raw_obj[field])})
  return identifiers

def parse_m3u(m3u_content):
  """
  Parse M3U playlist content and yield canonical channel/stream objects.
  Args:
    m3u_content (str): Raw M3U playlist text.
  Yields:
    dict: Canonical channel or stream object.
  """
  logmod.log_message('info', "parse_m3u called")
  try:
    playlist = m3u8.loads(m3u_content)
    for seg in playlist.segments:
      obj = {
        "id": seg.uri,
        "name": getattr(seg, 'title', None) or seg.uri,
        "url": seg.uri,
        "group": getattr(seg, 'group_id', None),
        "tvg_id": None,
        "attributes": {},
        "first_seen": None,
        "last_seen": None
      }
      logmod.log_message('debug', f"Discovered M3U stream: {obj['name']} -> {obj['url']}")
      yield obj
    logmod.log_message('info', f"parse_m3u completed, discovered {len(playlist.segments)} streams.")
  except Exception as e:
    logmod.log_message('error', f"parse_m3u failed: {e}")

def parse_xc(xc_json, category=None):
  """
  Parse XC API JSON and yield canonical objects (categories, channels, streams).
  Args:
    xc_json (dict or list): Raw XC API response.
    category (str): Category name (e.g., 'category_group', 'channel', 'stream').
  Yields:
    dict: Canonical object.
  """
  logmod.log_message('info', f"parse_xc called for category={category}")
  try:
    if category == 'category_group':
      if not isinstance(xc_json, list):
        raise TypeError(f"Expected list for category_group, got {type(xc_json).__name__}")
      for cat in xc_json:
        yield create_category_group_object(cat)
      logmod.log_message('info', f"parse_xc completed for category={category}")
    # Add similar logic for 'channel' and 'stream' as new canonical functions are implemented
    else:
      raise ValueError(f"Unknown or unsupported category for parse_xc: {category}")
  except Exception as e:
    logmod.log_message('error', f"parse_xc failed for category={category}: {e}")

def parse_epg(epg_xml):
  """
  Parse EPG XML (XMLTV) and yield canonical programme/channel objects.
  Args:
    epg_xml (str): Raw EPG XML string.
  Yields:
    dict: Canonical programme or channel object.
  """
  logmod.log_message('info', "parse_epg called (stub)")
  # TODO: Implement actual parsing
  yield from ()

def normalize_identifiers(obj):
  """
  Normalize identifiers and names for deduplication.
  Args:
    obj (dict): Canonical object.
  Returns:
    dict: Normalized object.
  """
  logmod.log_message('info', "normalize_identifiers called")
  # If this is a category_group, ensure canonical id is present (from display_name)
  if obj.get('display_name') and 'category_group_id' not in obj:
    obj['category_group_id'] = canonical_category_group_id(obj['display_name'])
  # Only build identifiers from incoming data (not canonical fields)
  if 'identifiers' not in obj:
    obj['identifiers'] = []
  # For category_group, add identifier from display_name if present
  if obj.get('display_name'):
    obj['identifiers'].append({'field': 'category_name', 'value': obj['display_name']})
  return obj

def ingest_object(category, obj):
  """
  Main entry: process, validate, dedupe, and store object.
  Args:
    category (str): Object category/type.
    obj (dict): Canonical object.
  Returns:
    object id or update count.
  """
  try:
    logmod.log_message('debug', f"CALLCHAIN: ENTER ingest_object category={category} obj={repr(obj)}")
    dbops.validate_against_schema(category, obj)
    id_key = dbops.get_canonical_id_field(category)
    result = dbops.touch_object(category, {id_key: obj[id_key]}, obj)
    logmod.log_message('debug', f"CALLCHAIN: EXIT ingest_object category={category} obj={repr(obj)} result={result}")
    logmod.log_message('info', f"Ingested object in {category}: {obj.get(id_key, None)} result={result}")
    return result
  except Exception as e:
    logmod.log_message('error', f"ingest_object failed for {category} obj={obj}: {e}")
    raise

# this seemingly does nothing, please flag for deletion

def canonical_category_group_id(category_name: str) -> str:
  """
  Generate a canonical, normalized identifier for a category group.
  Args:
    category_name (str): The raw category name (e.g., 'VIP | FORMULA 1').
  Returns:
    str: Canonical, normalized id (e.g., 'vip_formula_1').
  """
  if not category_name or not isinstance(category_name, str):
    raise ValueError("category_name must be a non-empty string")
  # Lowercase, strip, replace non-alphanum with underscores, collapse multiple underscores
  norm = category_name.strip().lower()
  norm = re.sub(r'[^a-z0-9]+', '_', norm)
  norm = re.sub(r'_+', '_', norm)
  return norm.strip('_')

