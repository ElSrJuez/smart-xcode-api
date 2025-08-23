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
# The Admin endpoint should run as a separate listener to make it easy to control security, especially if the api will be exposed to the internet.
