# Logging Strategy

| Purpose                                 | Source/Trigger                              | Log Location/Path (config)                  | Content/Detail Level                                 | Notes                                                      |
|------------------------------------------|---------------------------------------------|---------------------------------------------|-----------------------------------------------------|------------------------------------------------------------|
| API Proxy Summary/Error Logging          | `log_transaction` in `apipxy.py`            | `logging_api_log_file` (`log/api_log.txt`)  | Method, URL, status, headers (no bodies/payloads)   | For high-level events, warnings, errors only               |
| Passive JSONL Transaction Logging        | `log_jsonl_payload` in `apipxy.py`          | `logging_api_discover_jsonl_path` + `discovery.jsonl` | Full backend payload (JSON or raw text), timestamp   | For troubleshooting/manual analysis, not summary log       |
| Raw API Traffic Logging (if used)        | (Not currently called in code)              | `logging_api_raw_path`                      | (Intended for raw HTTP traffic, not currently active)| Placeholder for future raw traffic logging                 |
| Admin App Logging                        | Admin modules (not shown in apipxy.py)      | `logging_admin_log_path` (`log/admin`)      | Admin events, errors, warnings                      | Controlled by admin config section                         |
| Common App Logging                       | Shared/common modules                       | `logging_common_log_file` (`log/common_log.txt`) | General app-level events, warnings, errors           | Used if not admin/api context                              |
| Database Operation Logging               | DB ops (not shown in apipxy.py)             | `logging_db_log` (`log/db/db_log.txt`)      | DB operation events, errors                         | Controlled by dbops config section                         |

**Key Points:**
- Each log file has a distinct purpose and level of detail.
- API summary/error log (`api_log.txt`) should never contain full payloads—only summary info.
- JSONL log (`discovery.jsonl`) is for full payloads, for troubleshooting/manual analysis, not for summary or error events.
- All log file paths and enable flags are set in `config.ini` and preloaded into private variables at module init.
- Uvicorn/server access logs are separate and not controlled by your app’s logging config.

# API Proxy Feature (apipxy)

This document describes the API proxy feature of the smart-xcode-api project, as implemented in the `api/apipxy.py` module. This module is responsible for robustly and transparently proxying requests between clients and backend services, with strict configuration and logging.

## Overview
- The API proxy (apipxy) acts as a controlled gateway between external clients and internal APIs/services.
- All proxy behavior is deterministic and driven by external configuration (`config.ini`).
- No in-code defaults or fallbacks are permitted; all operational parameters must be explicitly set in the config file.
- Logging is routed through the canonical logging module, with per-module log file separation.

## Key Features
- **Config-Driven Routing:** All target URLs, allowed methods, and security settings are defined in `config.ini` under the `[api.apipxy]` section.
- **Security:** Only explicitly allowed endpoints and HTTP methods are permitted. All other requests are rejected.
- **Request/Response Logging:** All proxy activity is logged using the canonical `log_message` function, with logs routed to the API log file as configured.
- **No In-Code Defaults:** Any missing or invalid configuration results in immediate, explicit failure.
- **Separation of Concerns:** The proxy logic is isolated in `api/apipxy.py`, with no cross-module configuration or logging code.

### Object Discovery Feature
#### Passive Automatic Object Discovery
The api service actively but silently discovers new standard iptv objects like streams, meta_channels (canonical channels), categories, epg source associations, etc. up to *but not including* individual programmes.
The incoming data is assumed to be imperfect/dirty, with undesirable prefixes, duplicity, orphaned, inconsistent syntax among other common flaws
The incoming data should also be assumed to be potentially, undesirable large / many records
The schema used for these objects is synthesis/minimal, as the main objective is for potential grouping and summarization avenues - recognizing that specifics is enemy #1 of grouping.
In the future the discovery feature will also support automatic smart discovery of recurring string/tags that can be used for inclusion/exclusion filters (i.e, substrings for grouping variants of the same channel (1, 2, 3 or "HD", "SD"))
Minimal tracking with timestamping is another feature, when an object was first discovered - so that automatic age based cleanup can be done of unused/unrequested stale objects.


#### Canonical Object Construction (2025-08-25)

- **meta_channel objects:** Canonical meta_channel objects are now constructed using the new `create_meta_channel_object(raw_obj)` function. This function uses the first available field from the schema's `canbeid` array to set both the `display_name` and the canonical `meta_channel_id` (via `canonical_meta_channel_id`).
- **category_group objects:** The canonical ID and display_name are now always derived from the first present field in the schema's `canbeid` array, not a hardcoded field.
- **stream objects:** The canonical ID for a stream is always the URL field, as this is unique and stable.
- **Schema-driven canbeid logic:** All canonical object construction now uses the schema's `canbeid` array for robust, source-agnostic deduplication and grouping.

#### Schema-Driven Field Updates

- The discovery ingestion and update logic now respects the `updatefields` array in the schema for each object category.
- For example, in `category_group` and `meta_channel`, only fields listed in `updatefields` (such as `identifiers` and `last_seen`) are updated on subsequent ingestions; all other fields (like `first_seen`) remain unchanged after initial creation.
- This ensures accurate tracking of when an object was first seen versus last seen, and prevents accidental overwrites of fields not meant to be updated.

#### Implementation Details

- The update logic in `utils/dbops.py` uses the `get_schema_field` helper to fetch the `updatefields` list from the loaded schema at runtime.
- Canonical object construction for meta_channel and category_group now uses the first present field from the schema's `canbeid` array for both display_name and canonical ID.
---

## For New Maintainers (2025-08-25)

- The canonical construction of meta_channel and category_group objects is now schema-driven, using the first available field from the `canbeid` array for both display_name and canonical ID.
- The function `create_meta_channel_object(raw_obj)` is the only entry point for canonical meta_channel construction, mirroring the approach for category_group.
- For streams, the canonical ID is always the URL.
- All update logic is strictly controlled by the schema's `updatefields` array.
- Passive JSONL logging and robust troubleshooting are fully enforced.
- See `utils/dbschema.md` for the latest schema and canonical construction details.
- Only fields present in `updatefields` are included in update operations; all others are left untouched unless a full insert occurs.
- This approach is DRY, efficient, and canonical, leveraging the schema loaded at module initialization.

#### Passive JSONL Transaction logging
When complete jsonl is enabled, this feature also logs a jsonl object with the payload of each transaction so that the detail can be used for troubleshooting and manual analysis.
Since the XC API is not well documented and the M3U text objects and the EPG XML objects may also be made available from the endpoint, this log stores records of the payloads (not entire API transactions).

## Configuration
All proxy settings must be defined in the `[api.apipxy]` section of `config.ini`. Example:

```
[api.apipxy]
target_url = https://backend.example.com/api
allowed_methods = GET,POST
api_port = 8080
logging_api_log_file = log/discovery/discovery.log
```

- `target_url`: The backend endpoint to which requests are proxied.
- `allowed_methods`: Comma-separated list of HTTP methods permitted for proxying.
- `api_port`: The port on which the proxy listens.
- `logging_api_log_file`: Path to the log file for API proxy activity.

## Coding Principles
- All configuration is loaded on demand or preloaded into private variables at import time.
- No global ALL_CAPS config variables; use `_PRIVATE_VARIABLES` per module.
- All logging is performed via the canonical `log_message` function.
- Fail fast: any missing or invalid config results in immediate error and shutdown.

## Planned Updates
- Refactor `apipxy.py` to use the new config and logging patterns (no legacy imports, no in-code defaults).
- Enforce strict config validation at startup.
- Add more granular logging for request/response cycles and error conditions.

## See Also
- `../utils/config.py` for config access patterns
- `../utils/logging.py` for canonical logging
- `../config.ini` for configuration structure
