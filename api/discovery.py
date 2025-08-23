"""
Passive Discovery Module (`api/discovery.py`)

This module implements the passive discovery feature for the smart-xcode-api project. It is responsible for parsing, normalizing, deduplicating, and tracking IPTV objects from incoming M3U, XC, and EPG data sources, updating the discovery database, and logging events. It does not handle admin moderation or UI actions.

Design & Tooling Agreements:
- Use TinyDB (via dbops) for all object storage and lookup.
- Use hashlib for identifier normalization and deduplication.
- Use the m3u8 library for M3U playlist parsing.
- Use the built-in xml.etree.ElementTree for EPG (XMLTV) parsing (no extra dependencies).
- All parsing and ingestion code should be minimal, robust, and use standard Python idioms.

Responsibilities:
- Parse incoming M3U, XC, and EPG data to extract categories/groups, channels, streams, etc.
- Normalize extracted objects to the canonical schema fields and structure.
- Deduplicate objects using identifiers to avoid redundant entries.
- Update the discovery database:
  - Add new objects with `first_seen` and `last_seen` timestamps.
  - Update `last_seen` for existing objects.
  - For streams, update or create the status/quality object.
- Log new discoveries and significant changes for audit/troubleshooting.
- Optionally prune or mark as inactive any objects not seen for a configurable period.

Not Responsible For:
- Admin moderation (inclusion/exclusion, naming, grouping, manual pruning, etc.)
- UI or admin interface actions

Usage:
This module is called by the API proxy or ingestion logic whenever new source data is received. It maintains a clean, deduped, and up-to-date catalog of all IPTV objects for admin review and client consumption.

---

See the main `api/README.md` for integration details and the schema for object definitions.
"""
