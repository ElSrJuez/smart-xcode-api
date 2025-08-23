# Implementation Table & Order

| Step | Function Name                        | Purpose                                                      | Module           |
|------|---------------------------------------|--------------------------------------------------------------|------------------|
| 1    | _self_init                           | Ensure DB/schema exist, create if missing                    | utils/dbops.py   |
| 2    | validate_against_schema              | Validate data against canonical schema                       | utils/dbops.py   |
| 3    | add_object                           | Add a new object to the DB                                   | utils/dbops.py   |
| 4    | get_object                           | Retrieve a single object by identifiers                      | utils/dbops.py   |
| 5    | update_object                        | Update an object by identifiers                              | utils/dbops.py   |
| 6    | find_objects                         | Find objects matching filters                                | utils/dbops.py   |
| 7    | delete_object                        | Delete an object by identifiers                              | utils/dbops.py   |
| 8    | touch_object                         | Add if new, or update last_seen if exists                    | utils/dbops.py   |
| 9    | deduplicate_objects                  | Merge/deduplicate objects in a category                      | utils/dbops.py   |
| 10   | prune_stale_objects                  | Remove/mark inactive objects not seen since cutoff           | utils/dbops.py   |
| 11   | update_stream_status                 | Update status/quality for a stream URL                       | utils/dbops.py   |
| 12   | log_discovery_event                  | Log a discovery event for audit/troubleshooting              | utils/dbops.py   |
| 13   | parse_m3u, parse_xc, parse_epg       | Parse incoming data sources into canonical objects            | api/discovery.py |
| 14   | normalize_identifiers                | Normalize identifiers for deduplication                      | api/discovery.py |
| 15   | ingest_object                        | Main entry: process, validate, dedupe, and store object      | api/discovery.py |

---

This table documents the canonical order of implementation and the responsibilities of each function/module for the passive discovery and deduplication pipeline.
# Database Schema Draft (Canonical Fields Only)

---


## Schema Design Agreements (Latest)

- The schema defines object categories (types) and their relationships, not the structure of the actual data records.
- No dedicated id fields; use lists of identifiers/aliases where needed (e.g., identifiers, aliases).
- `friendly_name` is an optional, admin-facing property for display in the Admin app; it is not present in incoming source data and is not required in the discovery schema. It may be generated or set during moderation/grouping.
- Remove example and notes fields from schema.
- Where multiple ids may be discovered, use a list (e.g., `identifiers`).
- Add an `include` (boolean) field to each object type for API moderation (toggle include/exclude in admin UI).
- Schema supports a hierarchical structure: categories/groups > channels > streams > programmes.
- Admin interface should present a hierarchical list with an intuitive toggle for include/exclude.

# The schema is a blueprint for discovery, grouping, and moderation—not a template for every record or a reflection of the raw data structure.


---

## Database Architecture & Management (Agreements)

- **Engine:** TinyDB (JSON, human-readable, schema-less, file-based)
- **Self-initializing:**
	- On startup, checks for existence of main DB and schema DB; creates if missing.
- **Schema as Data:**
	- Schema (field definitions, types, version, etc.) is stored in a dedicated TinyDB table or file.
	- On init, code checks for schema changes and applies migrations if needed.
- **Configuration-driven:**
	- All file paths, options, and behaviors are set via config.ini.
- **Canonical API:**
	- Exposes both internal (for code) and external (for modules/CLI) functions for CRUD, deduplication, tagging, etc.
- **Schema Evolution:**
	- On startup, compares current schema to stored schema; if different, applies changes (e.g., add new fields, migrate data).
- **No VOD:**
	- VOD objects are not tracked or modeled in this system.

This architecture supports flexible, evolvable, and transparent object discovery and management, as described in the README and concept map.

# Concept Table: General Object Types (XC/EPG/M3U Agnostic)
#

## Conceptual Groupings and Source Field Mapping

- **Category/Group (deduplicated)**
	- XC: `category_name`, `parent_id`
	- M3U: `group-title`
	- EPG: (not present)

- **Channel (deduplicated)**
	- XC: `name`, `stream_id`, `epg_channel_id`
	- M3U: `tvg-name`, `tvg-id`
	- EPG: `<channel id>`, `<display-name>`

- **Stream (deduplicated)**
	- XC: `stream_id`, `stream_icon`, `url`
	- M3U: `#EXTINF`/URL, `tvg-id`, `tvg-name`
	- EPG: (not present)


- **Programme**
	- EPG: `<programme channel>`, `<title>`, `<desc>`, `start`, `stop`
	- XC: `epg_listings`
	- M3U: (not present)

- **Include/Exclude Tag**
	- Internal: matched against all names/fields above; user-defined or auto-discovered

# Channel & Streams Model:
# - Channel: Logical TV/radio service (e.g., "Sky Sports F1"). This is the main moderation/inclusion/exclusion unit.
# - Each channel has a collection of associated stream URLs (endpoints).
# - Each stream URL has a status/quality object (e.g., last viewed timestamp, last status flag, error counter).
# - Admin moderation is performed at the channel level; all streams for a channel are included/excluded together.
# - This model supports simple admin control and detailed diagnostics/tracking per stream.
#
# Category vs. Group:
# - Category: Backend/API-defined organizational label (e.g., "Sports"). May be hierarchical.
# - Group: Presentation/UI-oriented grouping (e.g., M3U group-title). May overlap with categories but is more flexible.

# Smart Substring Label (Internal Concept):
#
# Smart Grouping Substring (Internal Concept):
# - Represents the common core substring across related names (e.g., "TNT SPORTS 1" in "TNT SPORTS 1", "TNT SPORTS 1 HD", "TNT SPORTS 1 FHD")
# - Used for fuzzy grouping and summarization of channels/streams that are variants of the same logical entity
# - General fields: grouping_key (string), example_variants (list), usage_contexts (list: channel, stream, group, etc.), first_seen (timestamp), last_seen (timestamp), notes (string, optional)
#
# Smart Filter Substring (Internal Concept):
# - Represents substrings/tags used for inclusion or exclusion filtering (e.g., "xxx" to filter out adult content, "VIP" to include/exclude premium channels)
# - Used for automatic filtering-in or filtering-out of channels/streams/groups
# - General fields: filter_key (string), filter_type (inclusion|exclusion), example_matches (list), usage_contexts (list), first_seen (timestamp), last_seen (timestamp), notes (string, optional)


# EPG (XMLTV) Discovery Notes:
# - <channel> elements: id (attribute), <display-name> (can be multiple), <icon src="...">
#   - id may be empty, duplicated, or reused; display-name is the main label, icon is logo URL
# - <programme> elements: start, stop (attributes), channel (attribute), <title>, <desc>
#   - start/stop are datetimes, channel links to <channel> id, title/desc are text
# - Field names and presence can vary; some channels have multiple display-names, some icons missing
# - Programme entries are linked to channels by channel id, and may overlap in time
# - All objects should be tracked with first_seen/last_seen timestamps for passive discovery


## Concept Table: General Object Types (XC/EPG/M3U Agnostic)

| Object Type   | General Fields                                                                 |
|-------------- |-------------------------------------------------------------------------------|
| Channel       | id, name(s), logo, group/category, tvg_id, attributes, first_seen, last_seen  |
| Streams (per channel) | url, status/quality (last viewed, last status, error count, etc.) |
| Category      | id, name, parent_id, attributes, first_seen, last_seen                        |
| Programme     | id, channel_id, title, desc, start, stop, lang, attributes, first_seen, last_seen |
| Account/Info  | user_info, server_info, attributes, first_seen, last_seen                     |

# Notes:
# - Fields are generalized for grouping, summarization, and tracking, not strict validation.
# - "attributes" is a flexible dict for any extra/unknown fields.
# - "first_seen"/"last_seen" support passive discovery and cleanup.
# - "id" may be a string, integer, or hash, depending on source.


## categories
- category_id (string)
- category_name (string)
- parent_id (integer or string)

## streams
- num (integer)
- name (string)
- stream_type (string)
- stream_id (integer)
- stream_icon (string)
- epg_channel_id (string or null)
- added (string, timestamp)
- category_id (string)
- custom_sid (string)
- tv_archive (integer)
- direct_source (string)
- tv_archive_duration (integer)

## epg_listings
- id (integer)
- epg_id (integer)
- title (string, base64-encoded)
- lang (string)
- start (string, datetime)
- end (string, datetime)
- description (string, base64-encoded)
- channel_id (string)
- start_timestamp (integer)
- stop_timestamp (integer)

## account_info (raw, as returned)

Note: This schema is strictly based on the canonical fields present in the source data/logs. Further reduction is possible by removing fields that are canonical but not useful for any purpose. Review and trim as needed for your use case.
## discovered_m3u_streams

# Flexible, minimal schema for passively discovered IPTV/M3U streams (from JSONL logs)
# - Each channel object contains a list of stream URLs.
# - Each stream URL has an associated status/quality object:
#     - url (string): Stream endpoint
#     - status (string): Last known status (e.g., working, error, geo-blocked)
#     - last_viewed (timestamp, optional)
#     - error_count (integer, optional)
#     - attributes (dict, optional): Any extra/unknown fields
# - Group/category, tvg_id, logo, etc. are still tracked at the channel level.
# - This model supports grouping, summarization, and minimal tracking, while keeping admin moderation simple.

Addendum: The `discovered_m3u_streams` schema is designed to support robust, minimal, and flexible object discovery from variable M3U/playlist sources, as described in the project README. It is intended for grouping, summarization, and passive cataloging of IPTV streams, not for strict validation or full-fidelity archival.