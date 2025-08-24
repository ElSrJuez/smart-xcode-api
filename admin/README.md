## Data Model & Schema-Driven UI

All admin objects are stored in TinyDB, with a schema defined in `db/schema/discovery_schema.json` and referenced in `config.ini`. The admin UI is strictly schema-driven—any changes to the schema are reflected in the UI.

**Canonical TinyDB Document Structure:**

- **Category**
	- `id` (str): Unique identifier
	- `name` (str)
	- `enabled` (bool)
	- `channels` (list of Channel objects)
- **Channel**
	- `id` (str)
	- `name` (str)
	- `enabled` (bool)
	- `streams` (list of Stream objects)
- **Stream**
	- `id` (str)
	- `name` (str)
	- `enabled` (bool)
	- `tags` (list of Tag IDs)
- **Tag**
	- `id` (str)
	- `name` (str)
	- `type` (str): 'include' or 'exclude'
	- `context` (str): e.g., 'channel', 'stream', 'category'

All objects must conform to this schema. The admin UI must never assume or hardcode field names/types—always use the schema.

---

## Hierarchical View Implementation

The admin UI renders a nested, collapsible hierarchy:

- Categories > Channels > Streams
- Each object displays its `enabled` status as a toggle (Flask-Admin action or inline button).
- The hierarchy is rendered using Flask-Admin custom views or Jinja2 templates, driven by the schema.
- Any changes to the schema or data structure are automatically reflected in the UI.

---

## Maintenance Toggle (Semaphore)

- The maintenance toggle is a prominent UI element (button/switch) at the top of the admin interface.
- Toggling ON creates the lock file defined in `config.ini` (`maintenance_flag_filename`); toggling OFF deletes it.
- The current status is polled and displayed in real time.
- All errors (e.g., file permission issues) are shown to the user and logged.
- No in-code fallback: if the lock file cannot be created/deleted, the UI must fail fast and show a clear error.

---

## Statistics Calculation & Display

- Statistics (counts per category, channel, stream, etc.) are computed by querying TinyDB at runtime.
- Stats are displayed at the top of the admin UI, using a Flask-Admin dashboard widget or custom view.
- All stats logic is schema-driven—no hardcoded field names or assumptions.

---

## Smart Tag CRUD

- Tags are stored as a separate collection/table in TinyDB.
- The admin UI provides a Flask-Admin model view for full CRUD (create, read, update, delete) of tags.
- Tags are associated with their context (category, channel, stream) and type (include/exclude).
- All tag operations are schema-driven and validated.

---

## Error Handling & User Feedback

- All errors (missing config, DB issues, etc.) are logged and shown to the user in the UI.
- The app must fail fast on any critical error—never fallback or continue with partial config/data.
- User-facing error messages are clear, actionable, and never expose sensitive details.

---

## Testing & Extensibility

- All admin logic should be covered by unit and integration tests (see `tests/` folder for future expansion).
- New features must follow the same schema-driven, config-only, fail-fast principles.
- To add a new view or model, define its schema, update the config, and implement a Flask-Admin view or custom template.

---
## Coding Principles: No In-Code Defaults or Fallbacks

**This project is strictly allergic to in-code defaults, fail- and fall-backs.**

- All configuration must be loaded from config.ini or other explicit config files.
- If a required config value is missing or invalid, the app must fail fast and exit with a clear error.
- No hardcoded values, silent fallbacks, or implicit defaults are permitted anywhere in the codebase.
- This principle ensures deterministic, predictable, and maintainable behavior across all environments.

> This is a core project value—see utils/config.py and admin_utils/admin_config.py for canonical enforcement patterns.
# Guidance for Future Admin App Maintainers (2025-08-24)

## Admin Web Interface Vision (2025-08-24)

- **UI/UX Goals:**
	- The admin web interface should be simple, modern, and visually appealing, prioritizing clarity and ease of use.
	- Use a clean, responsive layout with intuitive controls and clear visual hierarchy.

- **Core Features:**
	1. **Maintenance/Semaphore Control:**
		 - Provide a clear toggle/button to enable or disable maintenance mode (semaphore), which will pause all proxy transactions when active.
		 - Display current maintenance status prominently at the top of the interface.
	2. **Hierarchical Object View:**
		 - Render all discovered objects (categories, channels, streams) in a hierarchical, collapsible tree or list.
		 - Each object should have an intuitive enable/disable (include/exclude) button or switch, reflecting and controlling its moderation status.
		 - The UI should be schema-driven and adapt to changes in the discovery schema.
	3. **Basic Statistics:**
		 - Display summary statistics such as:
			 - Number of channels and streams per category
			 - Number of streams per channel
			 - Total counts and breakdowns for quick diagnostics
	4. **Smart Tag Management:**
		 - Provide a simple interface to view, add, edit, or remove smart tags for inclusion/exclusion filtering.
		 - Tags should be clearly associated with their usage contexts (e.g., channel, stream, group).

- **Secondary Features:**
	- Manual pruning/removal of objects
	- Diagnostics for orphaned/discarded objects
	- Display of recent admin actions (if audit is ever implemented)

- **Design Principles:**
	- Prioritize safety: all destructive or bulk actions should require confirmation.
	- Make moderation status and object relationships visually clear.
	- Keep the interface schema-driven and adaptive to future changes.

---

### 1. **Agreed-Upon Tech Stack (Python-Only, Simple, Beautiful)**

- **Backend & UI:** Flask (already used) with [Flask-Admin](https://flask-admin.readthedocs.io/) for instant, modern, interactive admin UI.
- **UI Components:** Use Flask-Admin’s built-in Bootstrap themes for a clean, responsive look.
- **Interactivity:** Use Flask-Admin AJAX features and minimal vanilla JS only if needed.
- **Hierarchy:** Hierarchical/tree views via Flask-Admin plugins or custom templates (all Python-side).
- **Statistics & Smart Tags:** Rendered directly in Flask templates or Flask-Admin views.
- **Semaphore:** Exposed as a simple toggle in the admin UI, which creates/deletes the lock file.
- **No npm, no React, no build tools, no state management libraries.**
- **All logic, UI, and state are handled in Python/Flask.**

### 2. **Wireframe (Textual, Flask-Admin/Bootstrap Style)**

```
+---------------------------------------------------------------+
| [ Maintenance: ON/OFF Toggle ]   [ Stats: X categories, ... ] |
+---------------------------------------------------------------+
| Hierarchy:                                                    |
|   [Category 1] (enabled)                                      |
|     └─ [Channel A] (enabled)                                  |
|         └─ [Stream 1] (disabled)                              |
|         └─ [Stream 2] (enabled)                               |
|     └─ [Channel B] (disabled)                                 |
|   [Category 2] (enabled)                                      |
|     └─ ...                                                    |
+---------------------------------------------------------------+
| [Smart Tags]  [Add Tag] [Edit] [Delete]                      |
|   - Tag: 'VIP' (include)   - Tag: 'XXX' (exclude)            |
+---------------------------------------------------------------+
```
- **Enable/Disable**: Each object (category, channel, stream) has a toggle switch (Flask-Admin action or inline button).
- **Stats**: Displayed at the top (counts per category/channel/stream).
- **Maintenance Toggle**: Prominently at the top, toggles the lock file.
- **Smart Tag Management**: At the bottom or in a Flask-Admin view.

### 3. **Implementation Plan (Python-Only, No Extra APIs)**

**Phase 1: Maintenance/Semaphore**
- [ ] Add Flask route or Flask-Admin action to get/set maintenance mode (toggle lock file directly from UI).
- [ ] Add toggle button in Flask-Admin UI for maintenance mode.

**Phase 2: Hierarchical Object View**
- [ ] Use Flask-Admin model or custom view to render all objects in a hierarchical, collapsible tree (categories > channels > streams).
- [ ] Add enable/disable (include/exclude) toggle for each object, using Flask-Admin actions or inline buttons.

**Phase 3: Statistics**
- [ ] Compute stats in Python and render in a summary bar at the top of the Flask-Admin UI.

**Phase 4: Smart Tag Management**
- [ ] Use Flask-Admin model view for smart tags, with add/edit/delete actions.

**Phase 5: Polish**
- [ ] Responsive design (Bootstrap), error handling, confirmation dialogs for destructive actions.
- [ ] Schema-driven rendering: adapt UI fields to schema changes in Python.

---

## Key Advice & Best Practices

- **Separation of Concerns:** Keep admin logic (moderation, UI, manual edits) strictly separate from passive discovery and ingestion. Never let admin actions mutate canonical ingestion logic or schema.
- **Schema-Driven UI:** Always drive the admin UI from the current schema. Never hardcode field names, object types, or relationships. Use the schema to generate forms, lists, and moderation controls.
- **Idempotent, Safe Edits:** All admin actions (include/exclude, friendly_name edits, merges) must be idempotent and log every change for auditability. Never allow silent or destructive edits.
- **Logging:** All admin actions should be logged with user, timestamp, and before/after state. Use the canonical logging utilities and keep logs separate from API logs.
- **Security:** The admin endpoint must always run on a separate listener/port, with strong authentication and never exposed to the public internet. Use IP allowlists, strong passwords, and consider 2FA.
- **Bulk Actions:** Provide safe, clear bulk actions (e.g., include/exclude all in group) with confirmation dialogs and undo where possible.
- **Diagnostics:** Expose clear diagnostics for orphaned/discarded objects, moderation status, and recent admin actions.
- **No In-Code Defaults:** Never introduce in-code defaults or fallbacks for required fields. All admin edits must be explicit and schema-compliant.
- **UI/UX:** Prioritize clarity and safety in the UI. Make moderation status, object relationships, and edit history visible and understandable.

## Important Hints

- **Canonical IDs:** Always use the canonical schema-driven ID (e.g., `category_group_id`, `channel_id`) for lookups, edits, and relationships. Never use TinyDB doc_id or sequential keys.
- **Include/Exclude:** The `include` flag is the primary moderation toggle. Make it easy to see and edit, and always log changes.
- **Friendly Name vs. Display Name:** See the top of this file. Never confuse or conflate these fields in the UI or logic.
- **Schema Evolution:** If the schema changes, ensure the admin UI adapts automatically. Add migration/versioning logic as needed.
- **Testing:** Add tests for all admin actions, especially bulk and destructive operations.
- **Documentation:** Keep this README and the main dbschema.md up to date with all admin-related changes.

## Prioritized TODO (as of 2025-08-24)

1. **Security Hardening:**
	- [ ] *No in-app security will be implemented; all security (authentication, IP allowlists, etc.) is handled externally via the frontend web proxy or infrastructure. The admin app itself will not implement any authentication or access control.*
	- [ ] *Admin endpoints are isolated from the public internet by external means only.*
2. **Bulk Moderation Tools:**
	- [ ] *Bulk actions are not currently planned or needed. All moderation will be performed on a per-object basis. This is noted for future extensibility only.*
3. **Audit & Diagnostics:**
	- [ ] *No audit logging of admin actions will be implemented. Diagnostics for orphaned/discarded objects and moderation status are not a current priority.*
4. **Schema-Driven UI:**
	- [ ] *There is currently no UI to refactor. If/when a UI is built, it should be schema-driven and adaptive, but this is not in scope for the basic feature set.*
5. **Testing:**
	- [ ] *No automated testing will be implemented at this stage. The focus is on delivering the basic features and completing the solution. Testing may be revisited if the project scope expands.*
6. **Documentation:**
	- [ ] *Documentation will be updated as needed, but is not a strict requirement. We are documenting as we go, prioritizing delivery of core features.*

---
# Terminology Clarification: Friendly Name vs. Display Name

- **friendly_name** (schema): The static, admin-facing label for each object type (e.g., 'Channel', 'Category Group', 'Stream'). This is defined in the schema for UI grouping and clarity.
- **display_name** (object instance): The editable, user-friendly label for a specific object (e.g., a channel's display name as seen by the admin or end user). This is set or edited via the admin interface and is not part of the schema's object type definition.

Use 'friendly_name' for schema object type labels, and 'display_name' for per-object admin/user labels to avoid confusion.
# Admin Actions in Passive Discovery

The following actions are handled by the Admin app/UI, not the API core:

- Review and moderate discovered objects (categories, channels, streams, tags, etc.).
- Set or edit the `include` flag for any object to control API exposure.
- Assign or edit `friendly_name` for admin display.
- Group, merge, or deduplicate objects as needed for clarity.
- Manage smart grouping/filter substrings for advanced moderation.
- Prune or remove objects manually (in addition to automatic pruning).
- View discovery logs and audit trails for troubleshooting.
- Apply bulk actions (e.g., include/exclude all in a group).

These actions are performed via the admin interface and are not part of the API's passive discovery or ingestion logic.
#
# Admin/Proxy Interface Isolation
#

**How are the admin and proxy interfaces isolated?**

- The admin interface (admin app) and the proxy/API interface are isolated by running on separate listeners/ports, as configured in the application and infrastructure.
- No security or authentication is implemented in the admin app itself; all access control is enforced externally (e.g., via a frontend web proxy, firewall, or reverse proxy configuration).
- The admin endpoint is never exposed directly to the public internet. Only trusted users or systems can access it through the external security layer.
- This approach ensures a clear separation of concerns: the admin app remains simple and focused, while all security and access control are managed by infrastructure.

*This design is intentional and aligns with the project's priorities: rapid delivery of basic features, minimal in-app complexity, and reliance on external security best practices.*

## Admin App Directory Structure

```
admin/
├── admin_app.py         # Main Flask/Flask-Admin app entrypoint
├── README.md            # Admin app documentation
├── requirements.txt     # Admin-specific Python dependencies
├── .gitkeep             # Ensures folder is tracked in git
├── admin_utils/         # Utilities for admin app (DB ops, logging, etc.)
│   ├── admin_dbops.py
│   └── admin_logging.py
├── routes/              # (Future) Flask blueprints/routes for modularity
│   └── .gitkeep
├── static/              # Static assets (CSS, JS, images) for custom UI
├── templates/           # Jinja2/Flask-Admin templates (custom UI, overrides)
│   └── .gitkeep
```

- `admin_utils/` is for admin-specific helpers (DB ops, logging, etc.).
- `routes/` is for modular Flask blueprints (can be expanded as the app grows).
- `templates/` is for custom Jinja2 or Flask-Admin templates.
- `static/` is for static assets (CSS, JS, images) for UI customization.
- `.gitkeep` files ensure empty folders are tracked in git.

**This structure is clean and ready for Flask-Admin and future expansion.**
