# Xcode Reverse Proxy: IPTV API Discovery & Simplification

## Overview

Xcode Reverse Proxy is a FastAPI-based middleware designed to simplify IPTV client configuration and provide passive, real-time discovery of Xtream Codes (xcode) API, M3U, and EPG data. The proxy enables clients to connect using a short, credential-free URL, while transparently injecting backend credentials and monitoring all API transactions. It maintains a minimalist, hierarchical database of discovered xcode objects (streams, categories, EPG entries, etc.), tracking their lifecycle for efficient backend management and analysis.

## Features

- **Credential-Free Client Access:**
  - Clients connect using a simple, short URL without providing credentials.
  - The proxy injects backend credentials as required for all xcode API requests.

- **Passive API Discovery:**
  - Monitors and logs all xcode API, M3U, and EPG transactions.
  - Automatically discovers and catalogs standard xcode objects (categories, streams, series, VOD, EPG entries, etc.).

- **Minimalist Hierarchical Database:**
  - Stores discovered objects in a lightweight, hierarchical structure (e.g., categories → streams → EPG entries).
  - Preserves original field names and schema as much as possible.
  - For each object, records:
    - `added`: Timestamp when first discovered.
    - `last_seen`: Timestamp when last observed as active.
  - Avoids artificial fields, indexes, or schema inflation.

- **Efficient Transaction Processing:**
  - Designed for fast, low-overhead updates and lookups.
  - Only updates `last_seen` when objects are observed in new transactions.
  - Removes or marks objects as inactive if not seen for a configurable period.

- **Comprehensive Logging:**
  - Maintains additive, structured logs for API discovery and troubleshooting.
  - Supports multiple logging phases (raw, discovery, elegant).

- **Extensible Architecture:**
  - Easily adaptable to new xcode API endpoints or object types.
  - Modular design for future enhancements (e.g., analytics, visualization, alerting).

## Database Schema

- **Categories**
  - Fields: As discovered from API (e.g., `category_id`, `category_name`, `parent_id`, `added`, `last_seen`)
  - Children: Streams
- **Streams**
  - Fields: As discovered (e.g., `stream_id`, `name`, `category_id`, ...)
  - Children: EPG entries
- **EPG Entries**
  - Fields: As discovered (e.g., `id`, `title`, `start`, `end`, ...)
- **VOD/Series**
  - Fields: As discovered

## Usage

1. **Configure Backend Credentials:**
   - Set backend xcode API URL and credentials in `config.ini`.
2. **Run the Proxy:**
   - Start the FastAPI server. Clients connect using the proxy URL.
3. **Client Configuration:**
   - Use the proxy URL in IPTV clients (no credentials required).
4. **Monitor and Analyze:**
   - The proxy passively discovers and logs all xcode objects and transactions.
   - The database is updated in real time as new objects are seen or disappear.

## Example Workflow

- Client requests channel list via proxy.
- Proxy injects credentials, forwards request, and logs transaction.
- New categories/streams are discovered and added to the database with `added` and `last_seen` timestamps.
- On subsequent requests, `last_seen` is updated for active objects.
- If an object is not seen for a configurable period, it is marked as inactive or removed.

## Design Principles

- **Transparency:** Proxy is invisible to clients; all discovery is passive.
- **Minimalism:** Database and logs retain only essential, original schema.
- **Performance:** Hierarchical, in-memory or lightweight persistent storage for fast access.
- **Extensibility:** Modular codebase for future features.

## Coding Principles for Maintainability

- **DRY (Don't Repeat Yourself):** Avoid code duplication by abstracting repeated logic into reusable functions or modules.
- **Separation of Concerns:** Organize code so that each module, function, or class has a single, well-defined responsibility.
- **Short Utilities, Modules, and Functions:** Keep functions and modules concise and focused. This makes code easier to read, test, and maintain.
- **Readability:** Prioritize clear naming and straightforward logic over cleverness.
- **Testability:** Write code that is easy to test, with minimal side effects and clear input/output boundaries.
- **Documentation:** Document public interfaces and complex logic to aid future contributors.

## Directory Structure

- `apipxy.py` — Main FastAPI proxy and discovery logic
- `config.ini` — Backend and proxy configuration
- `log/` — Discovery and troubleshooting logs
- `db/` — Minimalist hierarchical database (e.g., TinyDB, JSON, or similar)
- `README.md` — Project documentation

## Requirements

- Python 3.8+
- FastAPI
- httpx
- TinyDB (or similar lightweight DB)

## License

MIT License

## Credits

Created by github.com/ElSrJuez

