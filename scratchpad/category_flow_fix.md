# Issues in category_group Ingestion Flow

## 1. parse_xc: raw_obj Construction (FIXED)
Now passing the full raw object to `create_category_group_object` from `parse_xc`, making the dispatcher thin and schema-agnostic. All field selection and validation is handled in the canonical function.

## 2. create_identifiers_object: Schema Field Usage (FIXED)
Now always called with the full raw object, dynamically uses the schema, and logs a warning if no identifier fields are found. The function is robust to schema changes and misconfigurations.

## 3. normalize_identifiers: Redundant/Conflicting Identifiers (FIXED)
normalize_identifiers has been removed. All identifier logic is now schema-driven and handled in the canonical construction function. Any legacy code relying on normalize_identifiers will surface immediately and can be updated as needed.

## 4. ingest_object: id_key Selection (ALLEGEDLY FIXED)
Upsert logic now uses the schema-driven canonical id field for each category, ensuring correct and idempotent upsert/insert operations. This should prevent duplicate or missed records for all categories. Further validation may be needed in production.

## 5. Error Handling
All exceptions in `ingest_object` are caught and only logged, but not re-raised or handled further. This could hide errors from upstream callers.

## 6. deduplicate_object Function
This is a direct pass-through and may shadow the imported function name, but since you now use `dbops.deduplicate_object` everywhere, this is not a runtime issue—just a potential confusion.

## 7. parse_xc: Only category_group Supported
The dispatcher only supports 'category_group'. If other categories are passed, it raises an error. This is intentional but means the flow is incomplete for other object types.
