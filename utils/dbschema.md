# parse_xc: Canonical Parsing and Dispatch Responsibilities

## Responsibilities of parse_xc

- Parse the incoming XC API JSON.
- For each object, determine its category (e.g., category_group, channel, stream) based on the action or context.
- Collect only the relevant, interesting raw fields for that object type (e.g., for category_group, just category_name, parent_id, etc.).
- Validate that each raw object contains the required incoming fields for that object type (e.g., category_name for category_group).
- Pass the raw object to the canonical pipeline function (e.g., create_category_group_object(raw_obj)).

## What parse_xc should NOT do

- It should NOT synthesize or normalize fields.
- It should NOT consult or enforce the schema.
- It should NOT add defaults or computed fields.

## Schema validation and synthesis

- These are handled later, inside the canonical pipeline function (e.g., create_category_group_object), which is the only place that knows about the schema and how to synthesize a fully compliant object.

## Summary of best practice

- Use the action/category hint to select the parsing logic.
- For each raw object, validate that it contains the required incoming fields for that object type before passing it to the canonical pipeline function.
- Do not rely solely on the action hint—always check the actual data for the expected fields.
- This ensures robust, source-agnostic parsing and prevents misclassification or silent data loss.
# Canonical Construction of category_group Objects

## Canonical Construction Function: create_category_group_object

- All category_group objects must be synthesized via the function `create_category_group_object(raw_obj)`.
- This function is the only entry point for constructing a canonical, schema-compliant category_group from raw input (XC, M3U, etc).
- The first step in this function is to validate that the raw input contains the fundamental incoming fields required for a category_group (e.g., `category_name` for XC sources, or equivalent for M3U).
- If any required incoming field is missing, the function must raise an error or return a clear failure, and must not attempt to synthesize or guess missing source data.
- Only after validation, the function will synthesize all canonical fields (e.g., `category_group_id`, `display_name`, `identifiers`, etc.) as defined in the schema, using the raw input and deterministic logic.
- No other part of the codebase is permitted to independently invent, synthesize, or normalize category_group fields.

**Benefits:**
- Ensures DRYness, atomicity, and schema compliance.
- Guarantees all category_group objects are constructed in a uniform, auditable way.
- Centralizes logic for easier maintenance, debugging, and schema evolution.
# Implementation Table & Order

# Parent/Child Relationships & Flattening


# Orphan Handling

- **Programmes**: Programme entries that cannot be associated with any stream, channel, or category_group should be discarded to save memory and storage. (Future TODO: Track statistics and summaries about discarded orphans for diagnostics.)
- **Streams and Channels**: Streams or channels that cannot be associated with a parent (i.e., category_group_id or channel_id is null) should be minimally recorded (just the corresponding id, name, and url fields if available). Objective: for reporting/tracking purposes.
- **Priority**: The top priority for orphan handling is to avoid disruption from cleaner, well-associated incoming data. Orphaned data should never pollute or interfere with the canonical, well-structured records.

This approach ensures the database remains clean, efficient, and focused on actionable, well-associated objects, while still allowing for future diagnostics and review of orphaned data if needed.

- **Channels And Groups have parents**: Each channel is uniquely associated with a parent category_group, identified by `category_group_id`. This relationship is canonical and used for hierarchy, moderation, and deduplication.
- **Streams have parents**: Each stream is uniquely associated with a parent channel, identified by `channel_id`. This supports grouping, diagnostics, and moderation at the channel level.
- **Category groups do not have parents**: category_groups are flattened and deduplicated from the incoming source data. There is no parent/child hierarchy wihtin category groups in the canonical model, even if the source data contains a `parent_id` field. This ensures a flat, deduplicated set of category groups for robust grouping and moderation.

These relationships are reflected in the schema and should be respected in all ingestion, deduplication, and moderation logic.

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

## Canonical Identifiers and the `identifiers` List

- Each object category (e.g., `category_group`, `channel`, `stream`) must have a canonical, normalized identifier field (e.g., `category_group_id`, `channel_id`, `stream_id`).
- This canonical ID is always included as a key/value pair in the object's `identifiers` list, with `field` set to the canonical field name (e.g., `category_group_id`) and `value` set to the canonical value (e.g., `vip_formula_1`).
- The `identifiers` list also includes all other known aliases or source names for the object (e.g., the original `name`, `category_name`, or `group-title` fields from the source data).
- This design allows for robust deduplication, lookup, and referencing by any known alias, but always provides a single, authoritative, schema-driven ID for storage, referencing, and hierarchy.
- Example for a category group:

```json
{
  "category_group_id": "vip_formula_1",
  "display_name": "VIP | FORMULA 1",
  "identifiers": [
    {"field": "category_group_id", "value": "vip_formula_1"},
    {"field": "name", "value": "VIP | FORMULA 1"},
    {"field": "category_name", "value": "VIP | FORMULA 1"}
  ],
  ...
}
```

- The canonical ID is used for all parent/child relationships and for deduplication. The `identifiers` list is used for matching, merging, and alias resolution.

---