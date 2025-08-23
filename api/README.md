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
The api service actively but silently discovers new standard iptv objects like streams, categories, epg source associations, etc. up to *but not including* individual programmes.
The incoming data is assumed to be imperfect/dirty, with undesirable prefixes, duplicity, orphaned, inconsistent syntax among other common flaws
The incoming data should also be assumed to be potentially, undesirable large / many records
The schema used for these objects is synthesis/minimal, as the main objective is for potential grouping and summarization avenues - recognizing that specifics is enemy #1 of grouping.
In the future the discovery feature will also support automatic smart discovery of recurring string/tags that can be used for inclusion/exclusion filters (i.e, substrings for grouping variants of the same channel (1, 2, 3 or "HD", "SD"))
When complete jsonl is enabled, this feature also logs a jsonl object with the payload of each transaction so that the detail can be used for troubleshooting and manual analysis.
Since the XC API is not well documented and the M3U text objects and the EPG XML objects may also be made available from the endpoint, this log stores records of the payloads (not entire API transactions).
Minimal tracking with timestamping is another feature, when an object was first discovered - so that automatic age based cleanup can be done of unused/unrequested stale objects.

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
