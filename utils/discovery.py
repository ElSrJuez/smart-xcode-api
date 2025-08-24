
from utils import logging as logmod
import m3u8
from utils.dbops import touch_object, validate_against_schema

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
        obj = {
          "name": cat.get('category_name'),
          "parent_id": cat.get('parent_id'),
          "attributes": {},
          "first_seen": None,
          "last_seen": None
        }
        logmod.log_message('debug', f"Discovered XC category: name={obj['name']}")
        yield obj
    elif category == 'channel':
      if not isinstance(xc_json, dict):
        raise TypeError(f"Expected dict for channel, got {type(xc_json).__name__}")
      chans = xc_json.get('channels', [])
      for ch in chans:
        obj = {
          "id": ch.get('stream_id'),
          "name": ch.get('name'),
          "logo": ch.get('stream_icon'),
          "group": ch.get('category_id'),
          "tvg_id": ch.get('epg_channel_id'),
          "attributes": {},
          "first_seen": None,
          "last_seen": None
        }
        logmod.log_message('debug', f"Discovered XC channel: {obj['name']} (id={obj['id']})")
        yield obj
    elif category == 'stream':
      if not isinstance(xc_json, dict):
        raise TypeError(f"Expected dict for stream, got {type(xc_json).__name__}")
      streams = xc_json.get('streams', [])
      for st in streams:
        obj = {
          "id": st.get('stream_id'),
          "name": st.get('name'),
          "url": st.get('url'),
          "group": st.get('category_id'),
          "logo": st.get('stream_icon'),
          "tvg_id": st.get('epg_channel_id'),
          "attributes": {},
          "first_seen": None,
          "last_seen": None
        }
        logmod.log_message('debug', f"Discovered XC stream: {obj['name']} (id={obj['id']}) -> {obj['url']}")
        yield obj
    else:
      raise ValueError(f"Unknown or unsupported category for parse_xc: {category}")
    logmod.log_message('info', f"parse_xc completed for category={category}")
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
  logmod.log_message('info', "normalize_identifiers called (stub)")
  # TODO: Implement normalization
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
    ident = obj.get('id') if 'id' in obj else obj.get('name')
    logmod.log_message('debug', f"ingest_object called for category={category}, ident={ident}")
    norm_obj = normalize_identifiers(obj)
    validate_against_schema(category, norm_obj)
    # Use 'id' if present, otherwise 'name' as identifier for touch_object
    id_key = 'id' if 'id' in norm_obj else 'name'
    result = touch_object(category, {id_key: norm_obj[id_key]}, norm_obj)
    logmod.log_message('info', f"Ingested object in {category}: {norm_obj.get(id_key, None)} result={result}")
    return result
  except Exception as e:
    logmod.log_message('error', f"ingest_object failed for {category} obj={obj}: {e}")
def deduplicate_object(category, data):
  raise

