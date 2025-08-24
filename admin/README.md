# Guidance for Future Admin App Maintainers (2025-08-24)

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
# The Admin endpoint should run as a separate listener to make it easy to control security, especially if the api will be exposed to the internet.
