"""
discovery.py — Canonical Discovery and Parsing Logic

This module provides canonical parsing, normalization, and ingestion for category_group and related objects.
All imports are at the top, following project conventions.
"""

from utils import logging as logmod
import m3u8
import re
import utils.dbops as dbops
import time


# Module-level private parent id field names (DRY)
_STREAM_PARENT_ID_FIELD = 'meta_channel_id'
_META_CHANNEL_PARENT_ID_FIELD = 'category_group_id'
_CATEGORY_GROUP_ID_FIELD = 'category_group_id'


# Canonical construction of a meta_channel object from raw input and parent category_group_id
def create_meta_channel_object(raw_obj, category_group_id):
  """
  Synthesize a canonical, schema-compliant meta_channel object from raw input and parent category_group_id.
  Args:
    raw_obj (dict): The raw channel object from XC API or M3U source.
    category_group_id (str): Canonical parent category_group_id (from context or request).
  Returns:
    dict: A fully-formed, schema-compliant meta_channel object.
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
  """
  canbeid_fields = dbops.get_schema_field('meta_channel', 'canbeid')
  display_name = None
  for field in canbeid_fields:
    if field in raw_obj and raw_obj[field]:
      display_name = raw_obj[field]
      break
  if not display_name:
    logmod.log_message('error', f"No canbeid field found in raw_obj for meta_channel: {raw_obj}")
    return None
  meta_channel_id = canonical_meta_channel_id(display_name)
  identifiers = create_identifiers_object(raw_obj, 'meta_channel')
  now = int(time.time())
  canonical = {
    _META_CHANNEL_PARENT_ID_FIELD: meta_channel_id,
    "display_name": display_name,
    _CATEGORY_GROUP_ID_FIELD: category_group_id,
    "identifiers": identifiers,
    "first_seen": now,
    "last_seen": now,
    "include": True
  }
  required_fields = dbops.get_schema_field('meta_channel', 'fields')
  for field in required_fields:
    fname = field['name']
    if fname not in canonical:
      logmod.log_message('warning', f"Required field '{fname}' is missing from canonical meta_channel object and has not been auto-filled.")
  logmod.log_message('info', f"Successfully constructed canonical meta_channel object: {canonical}")
  return canonical

def create_category_group_object(raw_obj):
  """
  Synthesize a canonical, schema-compliant category_group object from raw input.
  Args:
    raw_obj (dict): The raw category/group object from XC API or M3U source.
  Returns:
    dict: A fully-formed, schema-compliant category_group object.
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
  """

  # Detect incoming raw object type
  incoming_type = detect_category_group_incoming_object_type(raw_obj)

  if incoming_type == 'xc_category_group':
    display_name = raw_obj['category_name']
    category_group_id = canonical_category_group_id(display_name)
    identifiers = create_identifiers_object(raw_obj, 'category_group')
    now = int(time.time())
    canonical = {
      _CATEGORY_GROUP_ID_FIELD: category_group_id,
      "display_name": display_name,
      "identifiers": identifiers,
      "first_seen": now,
      "last_seen": now,
      "include": True
    }
    # Check for any other required fields in the schema and log if missing
    required_fields = dbops.get_schema_field('category_group', 'fields')
    for field in required_fields:
      fname = field['name']
      if fname not in canonical:
        logmod.log_message('warning', f"Required field '{fname}' is missing from canonical category_group object and has not been auto-filled.")
    logmod.log_message('info', f"Successfully constructed canonical category_group object: {canonical}")
    return canonical
  elif incoming_type == 'm3u_category_group':
    logmod.log_message('error', "Canonical construction for m3u_category_group is not yet implemented. Incoming object: {}".format(raw_obj))
    return None
  else:
    logmod.log_message('error', f"Unknown incoming_type: {incoming_type}. Incoming object: {raw_obj}")
    return None

#
def create_identifiers_object(raw_obj, object_categories_object_name):
  """
  Canonically construct the identifiers list for an object, using the canbeidentifier fields from the schema.
  Args:
    raw_obj (dict): The raw input object from source data.
    object_categories_object_name (str): The object category name (e.g., 'category_group').
  Returns:
    list: List of identifier dicts, each with 'field' and 'value'.
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
  """

  canbeidentifier_fields = dbops.get_schema_field(object_categories_object_name, 'canbeidentifier')
  if not canbeidentifier_fields:
    logmod.log_message('warning', f"No identifier fields found in schema for object category '{object_categories_object_name}'")
  identifiers = []
  for field in canbeidentifier_fields:
    if field in raw_obj and raw_obj[field] is not None:
      identifiers.append({"field": field, "value": str(raw_obj[field])})
  return identifiers

# Canonical parent ID selection for meta_channel: prefer request context, else raw object, else log error
def get_canonical_category_group_id_for_meta_channel(raw_obj, request_context=None):
  """
  Determine the canonical parent category_group_id for a meta_channel object.
  Args:
    raw_obj (dict): The raw channel object from XC API or M3U source.
    request_context (dict, optional): Context dict, e.g., query params or API args.
  Returns:
    str: Canonical, normalized category_group_id, or None if not found.
  """
  # 1. Prefer explicit parent ID from request context (e.g., category_id in query params)
  category_id = None
  if request_context and 'category_id' in request_context and request_context['category_id']:
    category_id = request_context['category_id']
  # 2. Otherwise, extract from raw object
  elif 'category_id' in raw_obj and raw_obj['category_id']:
    category_id = raw_obj['category_id']
  # 3. If still not found, log error
  if not category_id:
    logmod.log_message('error', f"No category_group_id found for meta_channel: {raw_obj} | context={request_context}")
    return None
  # Canonicalize
  return canonical_category_group_id(str(category_id))

def parse_m3u(m3u_content):
  """
  Parse M3U playlist content and yield canonical channel/stream objects.
  Args:
    m3u_content (str): Raw M3U playlist text.
  Yields:
    dict: Canonical channel or stream object.
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
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



def create_stream_object(raw_obj, meta_channel_id):
  """
  Synthesize a canonical, schema-compliant stream object from raw input.
  Args:
    raw_obj (dict): The raw stream object from XC API or M3U source.
    meta_channel_id (str): Canonical meta_channel_id to use as parent. Must be provided.
  Returns:
    dict: A fully-formed, schema-compliant stream object.
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
  """
  url = raw_obj.get('url')
  if not url:
    logmod.log_message('error', f"No 'url' field found in raw_obj for stream: {raw_obj}")
    return None
  if not meta_channel_id:
    logmod.log_message('error', f"No meta_channel_id provided for stream: {raw_obj}")
    return None
  canonical = {
    _STREAM_PARENT_ID_FIELD: meta_channel_id,
    "url": url,
    "status": raw_obj.get('status', {}),
    "first_seen": int(time.time()),
    "last_seen": int(time.time()),
    "include": True
  }
  required_fields = dbops.get_schema_field('stream', 'fields')
  for field in required_fields:
    fname = field['name']
    if fname not in canonical:
      logmod.log_message('warning', f"Required field '{fname}' is missing from canonical stream object and has not been auto-filled.")
  logmod.log_message('info', f"Successfully constructed canonical stream object: {canonical}")
  return canonical


def parse_xc(xc_json, category=None, parent_id=None):
  """
  Parse XC API JSON and yield canonical objects (category_group, meta_channel, stream).
  Args:
    xc_json (dict or list): Raw XC API response.
    category (str): Category name (e.g., 'category_group', 'meta_channel', 'stream').
    parent_id (str): Canonical parent ID (category_group_id for meta_channel, meta_channel_id for stream).
  Yields:
    dict: Canonical object.
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
  """
  logmod.log_message('info', f"parse_xc called for category={category}")
  try:
    if category == 'category_group':
      if not isinstance(xc_json, list):
        logmod.log_message('error', f"Expected list for category_group, got {type(xc_json).__name__}. Incoming object: {xc_json}")
        return
      for cat in xc_json:
        yield create_category_group_object(cat)
      logmod.log_message('info', f"parse_xc completed for category={category}")
    elif category == 'meta_channel':
      if not isinstance(xc_json, list):
        logmod.log_message('error', f"Expected list for meta_channel, got {type(xc_json).__name__}. Incoming object: {xc_json}")
        return
      for ch in xc_json:
        parent_id = get_canonical_category_group_id_for_meta_channel(ch)
        logmod.log_message('debug', f"parse_xc: meta_channel parent_id resolved as {parent_id} for raw object: {ch}")
        if not parent_id:
          logmod.log_message('error', f"Skipping meta_channel due to missing parent category_group_id: {ch}")
          continue
        yield create_meta_channel_object(ch, parent_id)
      logmod.log_message('info', f"parse_xc completed for category={category}")
    elif category == 'stream':
      if not isinstance(xc_json, list):
        logmod.log_message('error', f"Expected list for stream, got {type(xc_json).__name__}. Incoming object: {xc_json}")
        return
      if not parent_id:
        logmod.log_message('error', f"No parent meta_channel_id provided for stream parsing.")
        return
      for s in xc_json:
        yield create_stream_object(s, parent_id)
      logmod.log_message('info', f"parse_xc completed for category={category}")
    else:
      logmod.log_message('error', f"Unknown or unsupported category for parse_xc: {category}. Incoming object: {xc_json}")
      return
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
  if obj.get('display_name') and _CATEGORY_GROUP_ID_FIELD not in obj:
    obj[_CATEGORY_GROUP_ID_FIELD] = canonical_category_group_id(obj['display_name'])
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
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
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
    logmod.log_message('error', f"category_name must be a non-empty string. Got: {category_name}")
    return ""
  # Lowercase, strip, replace non-alphanum with underscores, collapse multiple underscores
  norm = category_name.strip().lower()
  norm = re.sub(r'[^a-z0-9]+', '_', norm)
  norm = re.sub(r'_+', '_', norm)
  return norm.strip('_')

# Canonical, normalized identifier for meta channels
def canonical_meta_channel_id(display_name: str) -> str:
  """
  Generate a canonical, normalized identifier for a meta channel.
  Args:
    display_name (str): The raw display name for the channel (e.g., 'Sky Sports F1 HD').
  Returns:
    str: Canonical, normalized id (e.g., 'sky_sports_f1_hd').
  """
  if not display_name or not isinstance(display_name, str):
    logmod.log_message('error', f"display_name must be a non-empty string. Got: {display_name}")
    return ""
  norm = display_name.strip().lower()
  norm = re.sub(r'[^a-z0-9]+', '_', norm)
  norm = re.sub(r'_+', '_', norm)
  return norm.strip('_')


# --- Object type detection helpers ---
def detect_category_group_incoming_object_type(raw_obj):
  """
  Detect the incoming raw object type for category_group objects.
  Args:
    raw_obj (dict): The raw input object.
  Returns:
    str: The detected type, e.g. 'xc_category_group' or 'm3u_category_group'.
  Logs:
    Canonically logs an informative INFO message on success, on failure the incoming object, if DEBUG the resulting object.
  """
  if 'category_name' in raw_obj:
    return 'xc_category_group'
  elif 'group_title' in raw_obj:
    return 'm3u_category_group'
  else:
    logmod.log_message('error', f"Unknown or unsupported category_group raw object type: missing 'category_name' or 'group_title'. Incoming object: {raw_obj}")
    return None

